from app.worker.celery_app import celery
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Execution, Module, ExecutionLog, ExecStatus, ExecutionArtifact
from app.services.command_builder import build_argv, extract_env_map
from app.services.redaction import mask_secrets
from app.config import settings
from datetime import datetime
import docker
import io, tarfile, os, time

@celery.task(name='app.tasks.run_execution')
def run_execution(execution_id: int, params: dict):
    db: Session = SessionLocal()
    try:
        ex = db.query(Execution).get(execution_id)
        m = db.query(Module).get(ex.module_id)
        ex.status = ExecStatus.running.value
        ex.started_at = datetime.utcnow()
        db.commit()

        client = docker.from_env()
        argv = build_argv(m.command_template_json, params)
        env_map = extract_env_map(m.command_template_json, params)
        # Identify secrets for redaction from param schema
        param_types = {k: v.get('type') for k, v in (m.parameters_schema_json or {}).items()}
        secret_values = [v for k, v in params.items() if param_types.get(k) == 'secret']

        mem_bytes = m.mem_limit_mb * 1024 * 1024
        workdir = f"/work/{execution_id}"

        container = client.containers.run(
            settings.RUNNER_IMAGE,
            argv,
            user="1000:1000",
            network_mode='none',
            working_dir=workdir,
            detach=True,
            environment=env_map,
            volumes={
                os.getcwd() + '/scripts': {'bind': settings.SCRIPT_BASE, 'mode': 'ro'},
            },
            mem_limit=mem_bytes,
            nano_cpus=int(m.cpu_limit * 1e9),
            stdin_open=False,
            tty=False,
        )
        ex.sandbox_id = container.id[:12]
        db.commit()

        seq = 0
        start_time = time.time()
        for line in container.logs(stream=True, stdout=True, stderr=True, follow=True):
            if time.time() - start_time > m.timeout_sec:
                container.kill()
                ex.status = ExecStatus.timeout.value
                db.commit()
                break
            text = line.decode('utf-8', errors='ignore')
            red = mask_secrets(text, secret_values)
            db.add(ExecutionLog(execution_id=execution_id, stream='stdout', chunk_text_redacted=red, sequence_no=seq))
            seq += 1
            db.commit()

        ret = container.wait(timeout=3)
        exit_code = ret.get('StatusCode', 1) if isinstance(ret, dict) else 1
        ex.exit_code = exit_code
        ex.finished_at = datetime.utcnow()
        if ex.status != ExecStatus.timeout.value:
            ex.status = ExecStatus.succeeded.value if exit_code == 0 else ExecStatus.failed.value
        db.commit()

        # Collect artifacts: copy /work/<id>/artifacts/*
        artifacts_dir = f"{workdir}/artifacts"
        try:
            bits, stat = container.get_archive(artifacts_dir)
            file_like = io.BytesIO(b''.join(list(bits)))
            with tarfile.open(fileobj=file_like) as tar:
                for mtr in tar.getmembers():
                    if not mtr.isfile():
                        continue
                    f = tar.extractfile(mtr)
                    if not f:
                        continue
                    data = f.read()
                    # Upload to S3/MinIO
                    key = f"exec/{execution_id}/{os.path.basename(mtr.name)}"
                    import boto3
                    s3 = boto3.client('s3', endpoint_url=settings.S3_ENDPOINT_URL, aws_access_key_id=settings.S3_ACCESS_KEY, aws_secret_access_key=settings.S3_SECRET_KEY)
                    s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data)
                    # Presign URL
                    url = s3.generate_presigned_url('get_object', Params={'Bucket': settings.S3_BUCKET, 'Key': key}, ExpiresIn=3600)
                    db.add(ExecutionArtifact(execution_id=execution_id, filename=os.path.basename(mtr.name), size_bytes=len(data), content_type='text/plain', storage_url_signed=url))
                    db.commit()
        except Exception:
            pass
    except Exception as e:
        ex = db.query(Execution).get(execution_id)
        if ex:
            ex.status = ExecStatus.failed.value
            ex.error_summary = str(e)
            ex.finished_at = datetime.utcnow()
            db.commit()
    finally:
        try:
            container.remove(force=True)
        except Exception:
            pass
        db.close()
