from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pathlib import Path
from app.config import settings
from app.database import get_db
from app.schemas import ScriptRegisterIn, ScriptOut
from app.models import Script, User
from app.security import get_principal, Principal
from app.services.checksum import sha256_file
from app.audit import audit

router = APIRouter(prefix="/api/scripts", tags=["scripts"])

@router.post('/register', response_model=ScriptOut)
def register_script(payload: ScriptRegisterIn, request: Request, db: Session = Depends(get_db), p: Principal = Depends(get_principal)):
    # Resolve user
    user = db.query(User).filter_by(email=p.email).first()
    if not user:
        raise HTTPException(status_code=403, detail="Unknown user")
    if user.role not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="Admin required")

    # Validate path under base
    pth = Path(payload.path)
    base = Path(settings.SCRIPT_BASE)
    try:
        pth = pth.resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not str(pth).startswith(str(base) + "/"):
        raise HTTPException(status_code=400, detail="Path must be under allowlisted base")
    if not pth.exists() or not pth.is_file():
        raise HTTPException(status_code=400, detail="File not found")

    checksum = sha256_file(str(pth))

    scr = Script(name=pth.name, path=str(pth), interpreter=payload.interpreter, checksum=checksum, registered_by=user.id)
    db.add(scr)
    db.commit()

    audit(db, user.id, 'script.register', 'script', str(scr.id), None, {"path": scr.path, "checksum": scr.checksum}, request)

    return scr

@router.get('', response_model=list[ScriptOut])
def list_scripts(db: Session = Depends(get_db), p: Principal = Depends(get_principal)):
    rows = db.query(Script).all()
    return rows
