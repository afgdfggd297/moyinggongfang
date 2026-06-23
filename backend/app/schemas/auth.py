"""Pydantic schemas for authentication endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Request schemas ─────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Payload for user registration."""
    username: str = Field(..., min_length=3, max_length=32, description="Unique username (3-32 characters)")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)")


class UserLogin(BaseModel):
    """Payload for user login."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class UserUpdate(BaseModel):
    """Payload for updating user profile."""
    username: Optional[str] = Field(None, min_length=3, max_length=32)
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None


# ── Response schemas ────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Public user information returned by the API."""
    id: str
    username: str
    email: str
    avatar_url: Optional[str] = None
    created_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
