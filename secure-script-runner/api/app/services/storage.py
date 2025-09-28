from app.config import settings
import boto3
from botocore.client import Config
from datetime import timedelta, datetime

_session = None

def client():
    global _session
    if _session is None:
        _session = boto3.session.Session(
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )
    s3 = _session.client(
        's3',
        endpoint_url=settings.S3_ENDPOINT_URL,
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
        use_ssl=settings.S3_SECURE,
    )
    return s3


def presign_put(key: str, expires_sec: int = 3600):
    return client().generate_presigned_url('put_object', Params={'Bucket': settings.S3_BUCKET, 'Key': key}, ExpiresIn=expires_sec)


def presign_get(key: str, expires_sec: int = 3600):
    return client().generate_presigned_url('get_object', Params={'Bucket': settings.S3_BUCKET, 'Key': key}, ExpiresIn=expires_sec)
