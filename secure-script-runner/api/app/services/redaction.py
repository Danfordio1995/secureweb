import re
from typing import Iterable

SECRET_MASK = "***"

# Simple patterns for PII-like data (demo)
PII_PATTERNS = [
    re.compile(r"[\w.-]+@[\w.-]+\.[A-Za-z]{2,}"),
]


def mask_secrets(text: str, secrets: Iterable[str]) -> str:
    t = text
    for s in secrets:
        if s:
            t = t.replace(s, SECRET_MASK)
    for pat in PII_PATTERNS:
        t = pat.sub(SECRET_MASK, t)
    return t
