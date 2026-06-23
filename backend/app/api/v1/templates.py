"""Template management API endpoints."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.security import TokenPayload, get_current_user
from app.db.database import get_db
from app.db.models import Template
from app.schemas.template import (
    TemplateCreate,
    TemplateDetailResponse,
    TemplateListResponse,
    TemplateResponse,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/categories", response_model=list[str])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all distinct template categories."""
    result = await db.execute(
        select(Template.category)
        .where(Template.category.isnot(None))
        .distinct()
        .order_by(Template.category)
    )
    categories = [row[0] for row in result.all() if row[0]]
    logger.info("[templates] categories listed, count=%d", len(categories))
    return categories


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """List templates with optional category filter and pagination."""
    # Build base query
    query = select(Template)
    count_query = select(func.count(Template.id))

    if category:
        query = query.where(Template.category == category)
        count_query = count_query.where(Template.category == category)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * page_size
    query = query.order_by(Template.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    templates = result.scalars().all()

    logger.info(
        "[templates] listed: category=%s, page=%d, total=%d, returned=%d",
        category, page, total, len(templates),
    )

    return TemplateListResponse(
        templates=[TemplateResponse.model_validate(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{template_id}", response_model=TemplateDetailResponse)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single template by ID."""
    try:
        tid = uuid.UUID(template_id)
    except ValueError:
        raise BadRequestError("无效的模板 ID 格式")

    result = await db.execute(select(Template).where(Template.id == tid))
    template = result.scalar_one_or_none()

    if template is None:
        raise NotFoundError("模板不存在")

    logger.info("[templates] get template: id=%s, name=%s", template_id, template.name)
    return TemplateDetailResponse.model_validate(template)


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    body: TemplateCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new template (requires authentication)."""
    template = Template(
        name=body.name,
        description=body.description,
        category=body.category,
        style=body.style,
        color_scheme=body.color_scheme,
        thumbnail_url=body.thumbnail_url,
        html_preview=body.html_preview,
        outline_template=body.outline_template,
        is_system=body.is_system,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)

    logger.info(
        "[templates] created: id=%s, name=%s, by user=%s",
        template.id, template.name, current_user.username,
    )

    return TemplateResponse.model_validate(template)
