from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.database import Base
import enum

class Role(str, enum.Enum):
    super_admin = "super_admin"
    admin = "admin"
    user = "user"

class ExecStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"
    timeout = "timeout"

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(50), default=Role.user.value)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class Group(Base):
    __tablename__ = 'groups'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

class Script(Base):
    __tablename__ = 'scripts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    path: Mapped[str] = mapped_column(String(1024))
    interpreter: Mapped[str] = mapped_column(String(50))
    checksum: Mapped[str] = mapped_column(String(128))
    registered_by: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class Module(Base):
    __tablename__ = 'modules'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    version: Mapped[int] = mapped_column(Integer, default=1)
    script_id: Mapped[int] = mapped_column(Integer, ForeignKey('scripts.id'))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parameters_schema_json: Mapped[dict] = mapped_column(JSON)
    command_template_json: Mapped[dict] = mapped_column(JSON)
    defaults_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timeout_sec: Mapped[int] = mapped_column(Integer)
    cpu_limit: Mapped[float] = mapped_column(Integer)
    mem_limit_mb: Mapped[int] = mapped_column(Integer)
    approvals_required: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class ModuleAssignment(Base):
    __tablename__ = 'module_assignments'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_id: Mapped[int] = mapped_column(Integer, ForeignKey('modules.id'))
    subject_type: Mapped[str] = mapped_column(String(10))  # user | group
    subject_id: Mapped[int] = mapped_column(Integer)
    permissions: Mapped[list[str]] = mapped_column(JSON)
    assigned_by: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'))
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Execution(Base):
    __tablename__ = 'executions'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_id: Mapped[int] = mapped_column(Integer, ForeignKey('modules.id'))
    trigger_user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(20), default=ExecStatus.queued.value)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    runtime_sec: Mapped[float | None] = mapped_column(Integer, nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sandbox_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    redactions_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    approvals_info_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class ExecutionParam(Base):
    __tablename__ = 'execution_params'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[int] = mapped_column(Integer, ForeignKey('executions.id'))
    key: Mapped[str] = mapped_column(String(200))
    value_masked: Mapped[str] = mapped_column(String(200))
    stored_securely_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)

class ExecutionLog(Base):
    __tablename__ = 'execution_logs'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[int] = mapped_column(Integer, ForeignKey('executions.id'))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    stream: Mapped[str] = mapped_column(String(10))  # stdout | stderr | system
    chunk_text_redacted: Mapped[str] = mapped_column(Text)
    sequence_no: Mapped[int] = mapped_column(Integer)

class ExecutionArtifact(Base):
    __tablename__ = 'execution_artifacts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[int] = mapped_column(Integer, ForeignKey('executions.id'))
    filename: Mapped[str] = mapped_column(String(300))
    size_bytes: Mapped[int] = mapped_column(Integer)
    content_type: Mapped[str] = mapped_column(String(100))
    storage_url_signed: Mapped[str] = mapped_column(Text)
    retention_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(200))
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[str] = mapped_column(String(100))
    before_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(200), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
