from sqlalchemy.orm import Session
from app.models import AuditLog
from datetime import datetime
from fastapi import Request
from typing import Any
from app.services.siem import post_siem

def audit(db: Session, actor_user_id: int | None, action: str, entity_type: str, entity_id: str, before: Any = None, after: Any = None, request: Request | None = None):
    ip = request.client.host if request and request.client else None
    ua = request.headers.get('User-Agent') if request else None
    row = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        before_json=before,
        after_json=after,
        ip=ip,
        user_agent=ua,
        timestamp=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    # Fire and forget SIEM webhook
    try:
        post_siem({
            "actor_user_id": actor_user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "before": before,
            "after": after,
            "ip": ip,
            "user_agent": ua,
            "timestamp": row.timestamp.isoformat()+"Z",
        })
    except Exception:
        pass
