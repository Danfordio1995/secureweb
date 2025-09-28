from app.config import settings
import httpx

def post_siem(event: dict):
    if not settings.SIEM_WEBHOOK_URL:
        return
    try:
        httpx.post(settings.SIEM_WEBHOOK_URL, json=event, timeout=3.0)
    except Exception:
        pass
