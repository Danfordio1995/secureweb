from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import asc
from datetime import datetime
from app.database import get_db
from app.models import Execution, Module, User, ExecutionLog, ExecutionArtifact
from app.schemas import ExecutionRequest, ExecutionOut, LogChunkOut, ArtifactOut
from app.worker.celery_app import celery
from app.audit import audit

router = APIRouter(prefix="/api/modules", tags=["executions"])

@router.post('/{id}/execute', response_model=ExecutionOut)
def execute_module(id: int, payload: ExecutionRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=request.headers.get('X-Demo-User')).first()
    if not user:
        raise HTTPException(status_code=403, detail="Unknown user")
    m = db.query(Module).get(id)
    if not m:
        raise HTTPException(status_code=404, detail="Module not found")

    ex = Execution(module_id=m.id, trigger_user_id=user.id, status='queued')
    db.add(ex)
    db.commit()

    audit(db, user.id, 'execution.enqueue', 'execution', str(ex.id), None, {"module_id": m.id}, request)

    celery.send_task('app.tasks.run_execution', args=[ex.id, payload.parameters])

    return ex

@router.get('/exec/{exec_id}', response_model=ExecutionOut)
def get_execution(exec_id: int, db: Session = Depends(get_db)):
    ex = db.query(Execution).get(exec_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Not found")
    return ex

@router.get('/exec/{exec_id}/logs')
def get_logs(exec_id: int, sinceSeq: int = 0, db: Session = Depends(get_db)):
    rows = db.query(ExecutionLog).filter(ExecutionLog.execution_id==exec_id, ExecutionLog.sequence_no>=sinceSeq).order_by(asc(ExecutionLog.sequence_no)).all()
    return [LogChunkOut(sequence_no=r.sequence_no, stream=r.stream, text=r.chunk_text_redacted) for r in rows]

@router.get('/exec/{exec_id}/artifacts')
def get_artifacts(exec_id: int, db: Session = Depends(get_db)):
    rows = db.query(ExecutionArtifact).filter_by(execution_id=exec_id).all()
    return [ArtifactOut(filename=r.filename, size_bytes=r.size_bytes, url=r.storage_url_signed) for r in rows]
