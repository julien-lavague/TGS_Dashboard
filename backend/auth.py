import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from config import settings

_basic = HTTPBasic()


def require_login(credentials: HTTPBasicCredentials = Depends(_basic)) -> str:
    """HTTP Basic gate for the whole dashboard.

    Checks the request credentials against DASHBOARD_USER / DASHBOARD_PASSWORD
    (see config.Settings) using constant-time comparison so a wrong username or
    password can't be distinguished by timing. Applied to every data router in
    main.py; /health is left open for platform health checks.
    """
    ok_user = secrets.compare_digest(credentials.username, settings.dashboard_user)
    ok_password = secrets.compare_digest(credentials.password, settings.dashboard_password)
    if not (ok_user and ok_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
