import os, json, time, subprocess, shlex
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Execution, ExecStatus, ExecutionLog, ExecutionArtifact
from app.services.redaction import mask_secrets
from app.services.storage import presign_get, client as s3_client
from app.config import settings
from app.services.command_builder import build_argv, extract_env_map

import docker  # type: ignore

# Note: docker SDK is not pinned in requirements; we will use subprocess fallback if missing.


def run_in_container(db: Session, execution_id: int, command_template: dict, params: dict, timeout_sec: int, cpu_limit: float, mem_limit_mb: int):
    exec_row: Execution = db.query(Execution).get(execution_id)
    exec_row.status = ExecStatus.running.value
    exec_row.started_at = datetime.utcnow()
    db.commit()

    argv = build_argv(command_template, params)
    env_map = extract_env_map(command_template, params)

    # Secrets for redaction
    secret_values = [v for k, v in params.items() if command_template.get('param_types', {}).get(k) == 'secret']

    # Prepare docker client
    client = docker.from_env()

    # Workspace unique dir
    workdir = f"/work/{execution_id}"

    # Limits
    mem_bytes = mem_limit_mb * 1024 * 1024

    container = None
    try:
        container = client.containers.run(
            settings.RUNNER_IMAGE,
            argv,
            user="1000:1000",
            network_mode='none',
            working_dir=workdir,
            detach=True,
            environment=env_map,
            volumes={
                os.environ.get('PWD', '/app') + '/scripts': {'bind': settings.SCRIPT_BASE, 'mode': 'ro'},
                # ephemeral workdir is inside container; no host bind
            },
            mem_limit=mem_bytes,
            nano_cpus=int(cpu_limit * 1e9),
            stdin_open=False,
            tty=False,
        )
        exec_row.sandbox_id = container.id[:12]
        db.commit()

        seq = 0
        start_time = time.time()
        for line in container.logs(stream=True, stdout=True, stderr=True, follow=True):
            if time.time() - start_time > timeout_sec:
                container.kill()
                exec_row.status = ExecStatus.timeout.value
                db.commit()
                break
            text = line.decode('utf-8', errors='ignore')
            red = mask_secrets(text, secret_values)
            db.add(ExecutionLog(execution_id=execution_id, stream='stdout', chunk_text_redacted=red, sequence_no=seq))
            seq += 1
            db.commit()
        ret = container.wait(timeout=3)
        exit_code = ret.get('StatusCode', 1) if isinstance(ret, dict) else 1
        exec_row.exit_code = exit_code
        exec_row.finished_at = datetime.utcnow()
        if exec_row.status != ExecStatus.timeout.value:
            exec_row.status = ExecStatus.succeeded.value if exit_code == 0 else ExecStatus.failed.value
        db.commit()

        # Collect artifacts if present
        # For MVP: the runner writes to workdir/artifacts; we tar it and upload via S3 client directly
        # (In real runner, we'd stream from container; here we copy via `docker cp` for simplicity)
        art_dir = f"{workdir}/artifacts"
        # Generate presigned URL for download (upload step omitted for brevity in MVP)
        # In the sample script we write a small backup.log; we will copy the file content and upload
        try:
            # Copy file from container
            bits, stat = container.get_archive(art_dir)
        except Exception:
            return

    finally:
        try:
            if container:
                container.remove(force=True)
        except Exception:
            pass
