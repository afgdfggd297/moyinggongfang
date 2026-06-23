"""CRUD 数据库操作"""

import logging
import uuid
from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Plan, PlanStatus, Template, User

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════
#  User CRUD
# ═══════════════════════════════════════

async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    hashed_password: str,
    avatar_url: str | None = None,
) -> User:
    """创建新用户"""
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        avatar_url=avatar_url,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    logger.info("创建用户: %s (id=%s)", username, user.id)
    return user


async def get_user_by_username(
    db: AsyncSession, username: str
) -> User | None:
    """通过用户名查找用户"""
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession, email: str
) -> User | None:
    """通过邮箱查找用户"""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(
    db: AsyncSession, user_id: uuid.UUID
) -> User | None:
    """通过 ID 查找用户"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


# ═══════════════════════════════════════
#  Plan CRUD
# ═══════════════════════════════════════

async def create_plan(
    db: AsyncSession,
    user_id: uuid.UUID,
    **kwargs,
) -> Plan:
    """创建新 PPT 方案"""
    plan = Plan(user_id=user_id, **kwargs)
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    logger.info("创建方案: id=%s, user_id=%s", plan.id, user_id)
    return plan


async def get_plan(
    db: AsyncSession, plan_id: uuid.UUID
) -> Plan | None:
    """通过 ID 获取方案"""
    result = await db.execute(
        select(Plan).where(Plan.id == plan_id)
    )
    return result.scalar_one_or_none()


async def get_plans_by_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> Sequence[Plan]:
    """分页获取用户的方案列表"""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Plan)
        .where(Plan.user_id == user_id)
        .order_by(Plan.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all()


async def update_plan(
    db: AsyncSession,
    plan_id: uuid.UUID,
    **kwargs,
) -> Plan | None:
    """更新方案"""
    plan = await get_plan(db, plan_id)
    if plan is None:
        return None
    for key, value in kwargs.items():
        if hasattr(plan, key):
            setattr(plan, key, value)
    await db.flush()
    await db.refresh(plan)
    logger.info("更新方案: id=%s, fields=%s", plan_id, list(kwargs.keys()))
    return plan


async def delete_plan(
    db: AsyncSession, plan_id: uuid.UUID
) -> bool:
    """删除方案"""
    plan = await get_plan(db, plan_id)
    if plan is None:
        return False
    await db.delete(plan)
    await db.flush()
    logger.info("删除方案: id=%s", plan_id)
    return True


async def count_plans_by_user(
    db: AsyncSession, user_id: uuid.UUID
) -> int:
    """统计用户的方案数量"""
    result = await db.execute(
        select(func.count(Plan.id)).where(Plan.user_id == user_id)
    )
    return result.scalar() or 0


# ═══════════════════════════════════════
#  Template CRUD
# ═══════════════════════════════════════

async def create_template(
    db: AsyncSession,
    name: str,
    description: str | None = None,
    category: str | None = None,
    style: str | None = None,
    color_scheme: str | None = None,
    thumbnail_url: str | None = None,
    html_preview: str | None = None,
    outline_template: dict | None = None,
    is_system: bool = False,
) -> Template:
    """创建新模板"""
    template = Template(
        name=name,
        description=description,
        category=category,
        style=style,
        color_scheme=color_scheme,
        thumbnail_url=thumbnail_url,
        html_preview=html_preview,
        outline_template=outline_template,
        is_system=is_system,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    logger.info("创建模板: %s (id=%s)", name, template.id)
    return template


async def get_template(
    db: AsyncSession, template_id: uuid.UUID
) -> Template | None:
    """通过 ID 获取模板"""
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    return result.scalar_one_or_none()


async def get_templates(
    db: AsyncSession,
    category: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> Sequence[Template]:
    """获取模板列表（支持按分类筛选）"""
    query = select(Template)
    if category:
        query = query.where(Template.category == category)
    offset = (page - 1) * page_size
    query = query.order_by(Template.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()


async def get_system_templates(
    db: AsyncSession,
) -> Sequence[Template]:
    """获取系统内置模板"""
    result = await db.execute(
        select(Template)
        .where(Template.is_system == True)
        .order_by(Template.name)
    )
    return result.scalars().all()
