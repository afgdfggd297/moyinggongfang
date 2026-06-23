"""Dashboard API endpoints for user plan management."""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.security import TokenPayload, get_current_user
from app.db.database import get_db
from app.db.models import Plan, PlanStatus
from app.schemas.template import (
    DashboardStats,
    DuplicatePlanRequest,
    PlanBrief,
    PlanListResponse,
    RenamePlanRequest,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user dashboard statistics."""
    user_id = uuid.UUID(current_user.sub)

    # Total plans
    total_result = await db.execute(
        select(func.count(Plan.id)).where(Plan.user_id == user_id)
    )
    total_plans = total_result.scalar() or 0

    # Exported count
    exported_result = await db.execute(
        select(func.count(Plan.id)).where(
            Plan.user_id == user_id,
            Plan.status == PlanStatus.EXPORTED,
        )
    )
    exported_count = exported_result.scalar() or 0

    # Draft count
    draft_result = await db.execute(
        select(func.count(Plan.id)).where(
            Plan.user_id == user_id,
            Plan.status == PlanStatus.DRAFT,
        )
    )
    draft_count = draft_result.scalar() or 0

    # Generated count
    generated_result = await db.execute(
        select(func.count(Plan.id)).where(
            Plan.user_id == user_id,
            Plan.status == PlanStatus.GENERATED,
        )
    )
    generated_count = generated_result.scalar() or 0

    # Recent activity (last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_result = await db.execute(
        select(func.count(Plan.id)).where(
            Plan.user_id == user_id,
            Plan.created_at >= seven_days_ago,
        )
    )
    recent_activity_count = recent_result.scalar() or 0

    logger.info(
        "[dashboard] stats for user=%s: total=%d, exported=%d",
        current_user.username, total_plans, exported_count,
    )

    return DashboardStats(
        total_plans=total_plans,
        exported_count=exported_count,
        draft_count=draft_count,
        generated_count=generated_count,
        recent_activity_count=recent_activity_count,
    )


@router.get("/recent", response_model=list[PlanBrief])
async def get_recent_plans(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's most recent 10 plans."""
    user_id = uuid.UUID(current_user.sub)

    result = await db.execute(
        select(Plan)
        .where(Plan.user_id == user_id)
        .order_by(Plan.updated_at.desc())
        .limit(10)
    )
    plans = result.scalars().all()

    logger.info("[dashboard] recent plans for user=%s, count=%d", current_user.username, len(plans))

    return [PlanBrief.model_validate(p) for p in plans]


@router.get("/plans", response_model=PlanListResponse)
async def list_plans(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's plans with pagination."""
    user_id = uuid.UUID(current_user.sub)

    # Total count
    total_result = await db.execute(
        select(func.count(Plan.id)).where(Plan.user_id == user_id)
    )
    total = total_result.scalar() or 0

    # Paginated results
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Plan)
        .where(Plan.user_id == user_id)
        .order_by(Plan.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    plans = result.scalars().all()

    logger.info(
        "[dashboard] plans list: user=%s, page=%d, total=%d, returned=%d",
        current_user.username, page, total, len(plans),
    )

    return PlanListResponse(
        plans=[PlanBrief.model_validate(p) for p in plans],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a plan owned by the current user."""
    try:
        pid = uuid.UUID(plan_id)
    except ValueError:
        raise BadRequestError("无效的方案 ID 格式")

    user_id = uuid.UUID(current_user.sub)
    result = await db.execute(
        select(Plan).where(Plan.id == pid, Plan.user_id == user_id)
    )
    plan = result.scalar_one_or_none()

    if plan is None:
        raise NotFoundError("方案不存在")

    await db.delete(plan)
    await db.flush()

    logger.info("[dashboard] deleted plan: id=%s, user=%s", plan_id, current_user.username)
    return None


@router.put("/plans/{plan_id}/title", response_model=PlanBrief)
async def rename_plan(
    plan_id: str,
    body: RenamePlanRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rename a plan owned by the current user."""
    try:
        pid = uuid.UUID(plan_id)
    except ValueError:
        raise BadRequestError("无效的方案 ID 格式")

    user_id = uuid.UUID(current_user.sub)
    result = await db.execute(
        select(Plan).where(Plan.id == pid, Plan.user_id == user_id)
    )
    plan = result.scalar_one_or_none()

    if plan is None:
        raise NotFoundError("方案不存在")

    plan.title = body.title
    await db.flush()
    await db.refresh(plan)

    logger.info("[dashboard] renamed plan: id=%s, new_title=%s", plan_id, body.title)
    return PlanBrief.model_validate(plan)


@router.post("/plans/{plan_id}/duplicate", response_model=PlanBrief, status_code=status.HTTP_201_CREATED)
async def duplicate_plan(
    plan_id: str,
    body: DuplicatePlanRequest = DuplicatePlanRequest(),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Duplicate a plan owned by the current user."""
    try:
        pid = uuid.UUID(plan_id)
    except ValueError:
        raise BadRequestError("无效的方案 ID 格式")

    user_id = uuid.UUID(current_user.sub)
    result = await db.execute(
        select(Plan).where(Plan.id == pid, Plan.user_id == user_id)
    )
    original = result.scalar_one_or_none()

    if original is None:
        raise NotFoundError("方案不存在")

    # Create a copy
    new_title = body.new_title or f"{original.title or 'Untitled'} (Copy)"
    new_plan = Plan(
        user_id=user_id,
        title=new_title,
        outline=original.outline,
        suggested_pages=original.suggested_pages,
        suggested_style=original.suggested_style,
        plan_summary=original.plan_summary,
        html_content=original.html_content,
        extra_info=original.extra_info,
        user_text=original.user_text,
        data_sources=original.data_sources,
        confirmed_pages=original.confirmed_pages,
        confirmed_style=original.confirmed_style,
        confirmed_color=original.confirmed_color,
        custom_colors=original.custom_colors,
        custom_style=original.custom_style,
        font_scheme=original.font_scheme,
        layout_density=original.layout_density,
        bg_style=original.bg_style,
        page_number=original.page_number,
        border_radius=original.border_radius,
        shadow_level=original.shadow_level,
        content_align=original.content_align,
        status=PlanStatus.DRAFT,
    )
    db.add(new_plan)
    await db.flush()
    await db.refresh(new_plan)

    logger.info(
        "[dashboard] duplicated plan: original=%s, new=%s, user=%s",
        plan_id, new_plan.id, current_user.username,
    )

    return PlanBrief.model_validate(new_plan)
