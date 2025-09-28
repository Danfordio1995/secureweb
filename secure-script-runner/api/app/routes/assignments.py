from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ModuleAssignment, User
from app.schemas import AssignmentIn
from app.audit import audit

router = APIRouter(prefix="/api/modules", tags=["assignments"])

@router.post('/{id}/assign')
def assign_module(id: int, payload: AssignmentIn, request: Request, db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.role.in_(['admin','super_admin'])).first()
    if not admin:
        raise HTTPException(status_code=403, detail="Admin required")

    a = ModuleAssignment(module_id=id, subject_type=payload.subject_type, subject_id=payload.subject_id, permissions=payload.permissions, assigned_by=admin.id)
    db.add(a)
    db.commit()
    audit(db, admin.id, 'module.assign', 'module', str(id), None, a.permissions, request)
    return {"ok": True}
