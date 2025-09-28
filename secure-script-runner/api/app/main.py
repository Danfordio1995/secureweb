from fastapi import FastAPI, Depends
from app.config import settings
from app.database import Base, engine
from app.routes import scripts, modules, assignments, executions, audit

app = FastAPI(title="Secure Script Runner", version="0.1.0")

# Create tables (MVP). For production use Alembic migrations.
Base.metadata.create_all(bind=engine)

app.include_router(scripts.router)
app.include_router(modules.router)
app.include_router(assignments.router)
app.include_router(executions.router)
app.include_router(audit.router)

@app.get('/')
def root():
    return {"service": "secure-script-runner", "env": settings.APP_ENV}
