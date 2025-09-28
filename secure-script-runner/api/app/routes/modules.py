from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Script, Module
from app.schemas import ModuleCreateIn, ModuleOut
from app.config import settings
from app.audit import audit

router = APIRouter(prefix="/api/modules", tags=["modules"])

@router.post('', response_model=ModuleOut)
def create_module(payload: ModuleCreateIn, request: Request, db: Session = Depends(get_db)):
    # For demo: assume admin
    user = db.query(User).filter(User.role.in_(['admin','super_admin'])).first()
    if not user:
        raise HTTPException(status_code=403, detail="Admin required")

    script = db.query(Script).get(payload.script_id)
    if not script:
        raise HTTPException(status_code=400, detail="Script not found")

    params_schema = {p.name: p.model_dump() for p in payload.parameters}
    cmd_tmpl = payload.command

    m = Module(
        name=payload.name,
        script_id=script.id,
        description=payload.description,
        parameters_schema_json=params_schema,
        command_template_json=cmd_tmpl,
        defaults_json={},
        timeout_sec=payload.timeout_sec or settings.DEFAULT_TIMEOUT_SEC,
        cpu_limit=payload.cpu_limit or settings.DEFAULT_CPU_LIMIT,
        mem_limit_mb=payload.mem_limit_mb or settings.DEFAULT_MEM_LIMIT_MB,
        approvals_required=payload.approvals_required or 0,
        created_by=user.id,
    )
    db.add(m)
    db.commit()
    audit(db, user.id, 'module.create', 'module', str(m.id), None, {"name": m.name, "version": m.version}, request)
    return m

@router.get('', response_model=list[ModuleOut])
def list_modules(assignedTo: str | None = None, db: Session = Depends(get_db)):
    rows = db.query(Module).filter_by(enabled=True).all()
    return rows
