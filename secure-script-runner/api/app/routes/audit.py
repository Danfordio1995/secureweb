from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuditLog

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get('')
def list_audit(db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200).all()
    return [
        {
            "id": r.id,
            "actor_user_id": r.actor_user_id,
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "timestamp": r.timestamp.isoformat()+"Z",
        } for r in rows
    ]
