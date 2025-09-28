from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any

class ScriptRegisterIn(BaseModel):
    path: str
    interpreter: str

class ScriptOut(BaseModel):
    id: int
    name: str
    path: str
    interpreter: str
    checksum: str

    class Config:
        from_attributes = True

class ModuleParam(BaseModel):
    name: str
    type: str  # string|int|float|bool|enum|secret|file
    required: bool = True
    default: Any | None = None
    validation: Dict[str, Any] | None = None  # regex|min|max|enum
    ui: Dict[str, Any] | None = None

class ModuleCreateIn(BaseModel):
    name: str
    script_id: int
    description: Optional[str] = None
    parameters: List[ModuleParam]
    command: Dict[str, Any]
    timeout_sec: int
    cpu_limit: float
    mem_limit_mb: int
    approvals_required: int = 0

class ModuleOut(BaseModel):
    id: int
    name: str
    version: int
    description: Optional[str]

    class Config:
        from_attributes = True

class AssignmentIn(BaseModel):
    subject_type: str  # user|group
    subject_id: int
    permissions: List[str]  # run|view|manage

class ExecutionRequest(BaseModel):
    parameters: Dict[str, Any]

class ExecutionOut(BaseModel):
    id: int
    status: str

    class Config:
        from_attributes = True

class LogChunkOut(BaseModel):
    sequence_no: int
    stream: str
    text: str

class ArtifactOut(BaseModel):
    filename: str
    size_bytes: int
    url: str
