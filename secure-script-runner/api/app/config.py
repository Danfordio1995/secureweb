from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    SECRET_KEY: str
    AUTH_MODE: str = "demo_header"  # demo_header | oidc

    OIDC_ISSUER: str | None = None
    OIDC_AUDIENCE: str | None = None
    OIDC_JWKS_URL: str | None = None

    DATABASE_URL: str
    REDIS_URL: str

    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_REGION: str = "us-east-1"
    S3_BUCKET: str = "artifacts"
    S3_SECURE: bool = False

    SIEM_WEBHOOK_URL: str | None = None

    SCRIPT_BASE: str = "/opt/scripts"
    ALLOW_INTERPRETERS: str = "python3,bash,pwsh,node"
    RUNNER_IMAGE: str = "secure-script-runner/runner:latest"

    DEFAULT_TIMEOUT_SEC: int = 600
    DEFAULT_CPU_LIMIT: float = 1.0
    DEFAULT_MEM_LIMIT_MB: int = 512
    MAX_OUTPUT_MB: int = 16

    class Config:
        env_file = ".env"

settings = Settings()
