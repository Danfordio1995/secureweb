from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Script, Module, ModuleAssignment
from app.config import settings
from app.services.checksum import sha256_file
from pathlib import Path

# Seed users, script, module v1, assignment per acceptance criteria

def run():
    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(name='Admin', email='admin@example.com', role='admin')
            db.add(admin)
        analyst = db.query(User).filter_by(email='analyst@example.com').first()
        if not analyst:
            analyst = User(name='Analyst', email='analyst@example.com', role='user')
            db.add(analyst)
        db.commit()

        # Register sample script
        script_path = Path(settings.SCRIPT_BASE) / 'backup_db.py'
        checksum = sha256_file(str(script_path)) if script_path.exists() else 'na'
        scr = db.query(Script).filter_by(path=str(script_path)).first()
        if not scr and script_path.exists():
            scr = Script(name='backup_db.py', path=str(script_path), interpreter='python3', checksum=checksum, registered_by=admin.id)
            db.add(scr)
            db.commit()

        # Create module v1
        if scr:
            existing = db.query(Module).filter_by(name='Backup DB').first()
            if not existing:
                params = [
                    {"name":"db_name","type":"enum","required":True,"validation":{"enum":["prod","staging","dev"]}},
                    {"name":"retention_days","type":"int","required":True,"validation":{"min":1,"max":365}},
                    {"name":"notify_email","type":"string","required":True,"validation":{"regex":"^.+@.+$"}},
                    {"name":"backup_key","type":"secret","required":True}
                ]
                command = {
                    "interpreter":"python3",
                    "script_path": str(script_path),
                    "named_args": {
                        "--db": "db_name",
                        "--retention": "retention_days",
                        "--notify": "notify_email"
                    },
                    "env": {
                        "BACKUP_KEY": "backup_key"
                    },
                    "param_types": {p['name']: p['type'] for p in params}
                }
                m = Module(name='Backup DB', script_id=scr.id, description='Daily backup with retention', parameters_schema_json={p['name']: p for p in params}, command_template_json=command, timeout_sec=120, cpu_limit=1.0, mem_limit_mb=256, approvals_required=1, created_by=admin.id)
                db.add(m)
                db.commit()
                # Assign to analyst
                db.add(ModuleAssignment(module_id=m.id, subject_type='user', subject_id=analyst.id, permissions=['run','view'], assigned_by=admin.id))
                db.commit()
        print("Seed complete")
    finally:
        db.close()

if __name__ == '__main__':
    run()
