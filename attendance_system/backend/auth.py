"""
Authentication: JWT-based login for Admin Panel.
Admin credentials from environment (ADMIN_USERNAME, ADMIN_PASSWORD) or defaults.
Tokens are invalidated on server restart so user must login again.
"""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Secret for signing JWT (use env in production)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "smart-attendance-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# New value on every server start → old tokens become invalid after restart
SERVER_RESTART_NONCE = secrets.token_hex(16)

# Admin credentials: set ADMIN_USERNAME and ADMIN_PASSWORD in env, or use defaults
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")  # If set, we use this; else hash plain ADMIN_PASSWORD
ADMIN_PASSWORD_PLAIN = os.getenv("ADMIN_PASSWORD", "admin123")  # Default for dev

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def _get_admin_password_hash() -> str:
    """Get stored hash for admin password. If not set, hash the plain default."""
    if ADMIN_PASSWORD_HASH:
        return ADMIN_PASSWORD_HASH
    return pwd_context.hash(ADMIN_PASSWORD_PLAIN)


def verify_password(plain: str) -> bool:
    """Verify admin password. Supports both env hash and plain env password."""
    if ADMIN_PASSWORD_HASH:
        return pwd_context.verify(plain, ADMIN_PASSWORD_HASH)
    return plain == ADMIN_PASSWORD_PLAIN


def create_access_token(username: str) -> str:
    """Create JWT access token. Invalidated when server restarts."""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "exp": expire, "restart": SERVER_RESTART_NONCE}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    """Decode JWT and return username (sub). Returns None if invalid or server was restarted."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("restart") != SERVER_RESTART_NONCE:
            return None  # Server restarted, token no longer valid
        return payload.get("sub")
    except Exception:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """
    Dependency: get current user from Bearer token.
    Accepts 'Authorization: Bearer <token>' or 'Authorization: <token>' for flexibility.
    """
    token = None
    if credentials:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    elif authorization:
        token = authorization.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = decode_token(token)
    if not username or username != ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username
