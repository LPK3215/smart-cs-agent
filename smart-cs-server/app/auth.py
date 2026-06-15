"""Authentication module — JWT tokens + password hashing + FastAPI dependencies."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Request, HTTPException, Depends
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_HOURS
from app.database import get_user_by_id_db

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, role: str) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT token. Returns payload dict or raises."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role", "user")
        if user_id is None:
            raise HTTPException(401, "无效的令牌")
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise HTTPException(401, "令牌已过期或无效")


def _extract_token(request: Request) -> Optional[str]:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


async def get_current_user(request: Request) -> dict:
    """FastAPI dependency: require authentication. Returns user dict."""
    token = _extract_token(request)
    if not token:
        raise HTTPException(401, "未提供认证令牌")

    token_data = decode_access_token(token)
    user = await get_user_by_id_db(token_data["user_id"])
    if not user:
        raise HTTPException(401, "用户不存在")

    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
    }


async def get_optional_user(request: Request) -> Optional[dict]:
    """FastAPI dependency: optional authentication. Returns user dict or None."""
    token = _extract_token(request)
    if not token:
        return None

    try:
        token_data = decode_access_token(token)
        user = await get_user_by_id_db(token_data["user_id"])
        if not user:
            return None
        return {
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "role": user["role"],
        }
    except HTTPException:
        return None


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """FastAPI dependency: require admin role."""
    if user.get("role") != "admin":
        raise HTTPException(403, "需要管理员权限")
    return user
