"""Authentication API endpoints – wired to PostgreSQL via SQLAlchemy async."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.exceptions import AuthError, ConflictError, NotFoundError, ForbiddenError
from app.core.security import (
    TokenPayload,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db import crud
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import (
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


# ── Helpers ──────────────────────────────────────────────────────────────────

def _user_response(user: User) -> UserResponse:
    """Convert an ORM User instance to a UserResponse schema."""
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        is_active=user.is_active,
    )


def _build_token(user: User) -> Token:
    """Create a JWT token response for the given user."""
    access_token = create_access_token(
        user_id=str(user.id), username=user.username
    )
    return Token(access_token=access_token, token_type="bearer", user=_user_response(user))


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user and return an access token."""
    # Check username uniqueness
    existing = await crud.get_user_by_username(db, body.username)
    if existing is not None:
        raise ConflictError("用户名已被占用")

    # Check email uniqueness
    existing = await crud.get_user_by_email(db, body.email)
    if existing is not None:
        raise ConflictError("邮箱已被注册")

    # Create user in the database
    hashed = hash_password(body.password)
    user = await crud.create_user(
        db,
        username=body.username,
        email=body.email,
        hashed_password=hashed,
    )
    logger.info("Registered new user: %s", user.username)
    return _build_token(user)


@router.post("/login", response_model=Token)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate a user and return an access token."""
    user = await crud.get_user_by_username(db, body.username)
    if user is None:
        raise AuthError("用户名或密码错误")

    if not verify_password(body.password, user.hashed_password):
        raise AuthError("用户名或密码错误")

    if not user.is_active:
        raise ForbiddenError("账号已被禁用")

    return _build_token(user)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's profile."""
    from uuid import UUID

    user = await crud.get_user_by_id(db, UUID(current_user.sub))
    if user is None:
        raise NotFoundError("用户不存在")
    return _user_response(user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile."""
    from uuid import UUID

    user = await crud.get_user_by_id(db, UUID(current_user.sub))
    if user is None:
        raise NotFoundError("用户不存在")

    # Username change – check uniqueness
    if body.username is not None and body.username != user.username:
        existing = await crud.get_user_by_username(db, body.username)
        if existing is not None:
            raise ConflictError("用户名已被占用")
        user.username = body.username

    # Email change – check uniqueness
    if body.email is not None and body.email != user.email:
        existing = await crud.get_user_by_email(db, body.email)
        if existing is not None:
            raise ConflictError("邮箱已被注册")
        user.email = body.email

    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url

    # Flush changes through the session (committed by get_db dependency)
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return _user_response(user)
