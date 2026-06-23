"""Template and Dashboard Pydantic schemas."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Template Schemas ────────────────────────────────────────────────────────

class TemplateCreate(BaseModel):
    """Payload for creating a new template."""
    name: str = Field(..., min_length=1, max_length=200, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, max_length=100, description="Template category (e.g. business, academic, creative)")
    style: Optional[str] = Field(None, max_length=100, description="Visual style")
    color_scheme: Optional[str] = Field(None, max_length=100, description="Color scheme")
    thumbnail_url: Optional[str] = Field(None, max_length=500, description="Thumbnail image URL")
    html_preview: Optional[str] = Field(None, description="HTML preview content")
    outline_template: Optional[dict] = Field(None, description="JSON outline template structure")
    is_system: bool = Field(default=False, description="Whether this is a system/built-in template")


class TemplateResponse(BaseModel):
    """Public template information returned by the API."""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    style: Optional[str] = None
    color_scheme: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_system: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class TemplateDetailResponse(TemplateResponse):
    """Extended template info including preview and outline."""
    html_preview: Optional[str] = None
    outline_template: Optional[dict] = None


class TemplateListResponse(BaseModel):
    """Paginated template list."""
    templates: List[TemplateResponse]
    total: int
    page: int
    page_size: int


# ── Dashboard Schemas ───────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    """User dashboard statistics."""
    total_plans: int = 0
    exported_count: int = 0
    draft_count: int = 0
    generated_count: int = 0
    recent_activity_count: int = 0  # plans created in last 7 days


class PlanBrief(BaseModel):
    """Brief plan info for dashboard listing."""
    id: str
    title: Optional[str] = None
    status: str = "draft"
    suggested_style: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlanListResponse(BaseModel):
    """Paginated plan list for dashboard."""
    plans: List[PlanBrief]
    total: int
    page: int
    page_size: int


class RenamePlanRequest(BaseModel):
    """Payload for renaming a plan."""
    title: str = Field(..., min_length=1, max_length=500, description="New plan title")


class DuplicatePlanRequest(BaseModel):
    """Optional payload for duplicating a plan."""
    new_title: Optional[str] = Field(None, max_length=500, description="Title for the duplicated plan")
