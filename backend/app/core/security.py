"""JWT authentication and password hashing utilities."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.exceptions import AuthError

# ── Configuration ───────────────────────────────────────────────────────────
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# ── Password hashing ────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT tokens ──────────────────────────────────────────────────────────────
class TokenPayload(BaseModel):
    sub: str  # user id
    username: str
    exp: Optional[float] = None


def create_access_token(user_id: str, username: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": user_id,
        "username": username,
        "exp": expire,
    }
    return jwt.encode(payload, get_settings().SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate a JWT access token.

    Raises JWTError if the token is invalid or expired.
    """
    payload = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[ALGORITHM])
    return TokenPayload(**payload)


# ── FastAPI dependency ──────────────────────────────────────────────────────
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> TokenPayload:
    """Extract the current user from the Authorization header.

    Returns a TokenPayload with ``sub`` (user id) and ``username``.
    Raises 401 if the token is missing, malformed, or expired.
    """
    if credentials is None:
        raise AuthError("未提供认证凭据")

    try:
        token_data = decode_access_token(credentials.credentials)
    except JWTError:
        raise AuthError("无效或过期的令牌")

    return token_data


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[TokenPayload]:
    """Extract the current user from the Authorization header, if present.

    Returns a TokenPayload if a valid token is provided, or None if no token
    is present. Raises 401 only if a token is provided but is invalid/expired.
    """
    if credentials is None:
        return None

    try:
        return decode_access_token(credentials.credentials)
    except JWTError:
        return None
