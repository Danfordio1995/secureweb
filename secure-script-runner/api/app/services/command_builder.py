from typing import Dict, Any, List
from fastapi import HTTPException
from app.config import settings
import shlex

ALLOWED_INTERPRETERS = set(i.strip() for i in settings.ALLOW_INTERPRETERS.split(','))


def build_argv(command_template: Dict[str, Any], params: Dict[str, Any]) -> List[str]:
    """Create argv array from template and param map. No shell join."""
    interp = command_template.get('interpreter')
    script = command_template.get('script_path')
    if interp not in ALLOWED_INTERPRETERS:
        raise HTTPException(status_code=400, detail=f"Interpreter not allowlisted: {interp}")
    if not script or not script.startswith(settings.SCRIPT_BASE + "/"):
        raise HTTPException(status_code=400, detail="Script path must be under allowlisted base")

    argv: List[str] = [interp, script]
    # positional args
    pos: list[str] = command_template.get('positional_args', [])
    for p in pos:
        v = params.get(p)
        if v is None:
            continue
        argv.append(str(v))
    # named flags
    flags: Dict[str, str] = command_template.get('named_args', {})
    for flag, pname in flags.items():
        if pname in params and params[pname] is not None:
            argv.extend([flag, str(params[pname])])
    return argv


def extract_env_map(command_template: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, str]:
    env_map: Dict[str, str] = {}
    for key, pname in (command_template.get('env', {}) or {}).items():
        v = params.get(pname)
        if v is None:
            continue
        env_map[str(key)] = str(v)
    return env_map
