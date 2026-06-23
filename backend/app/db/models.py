"""SQLAlchemy ORM 模型定义"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class PlanStatus(str, enum.Enum):
    """PPT 方案状态"""
    DRAFT = "draft"
    GENERATED = "generated"
    EXPORTED = "exported"


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    # 关系
    plans: Mapped[list["Plan"]] = relationship(
        "Plan", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Plan(Base):
    """PPT 方案模型"""
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # 方案基本信息
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    outline: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    suggested_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    suggested_style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    plan_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # HTML 内容
    html_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 用户输入
    extra_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_sources: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 用户确认的设置
    confirmed_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confirmed_style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confirmed_color: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 自定义样式
    custom_colors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    custom_style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    font_scheme: Mapped[str | None] = mapped_column(String(100), nullable=True)
    layout_density: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bg_style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    page_number: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    border_radius: Mapped[str | None] = mapped_column(String(50), nullable=True)
    shadow_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    content_align: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 导出
    pptx_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 状态
    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus), default=PlanStatus.DRAFT, nullable=False
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="plans")

    def __repr__(self) -> str:
        return f"<Plan {self.id} - {self.title}>"


class Template(Base):
    """PPT 模板模型"""
    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    color_scheme: Mapped[str | None] = mapped_column(String(100), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    html_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    outline_template: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Template {self.name}>"
