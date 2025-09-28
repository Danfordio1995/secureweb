from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import User, ModuleAssignment, Module

class Permission:
    RUN = 'run'
    VIEW = 'view'
    MANAGE = 'manage'


def ensure_role(user: User, allowed: list[str]):
    if user.role not in allowed:
        raise HTTPException(status_code=403, detail="Insufficient role")


def ensure_module_permission(db: Session, user: User, module_id: int, perm: str):
    # For MVP: user-based assignments only
    q = db.query(ModuleAssignment).filter_by(module_id=module_id, subject_type='user', subject_id=user.id)
    for a in q:
        if perm in (a.permissions or []):
            return
    # allow admins to view/manage
    if user.role in ['admin', 'super_admin']:
        return
    raise HTTPException(status_code=403, detail=f"Missing permission {perm} on module {module_id}")
