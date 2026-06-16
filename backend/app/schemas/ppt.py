"""PPT 相关数据模型"""
from pydantic import BaseModel, Field
from typing import Optional


class PlanRequest(BaseModel):
    """用户提交需求"""
    text: str = Field(..., description="用户输入的文字内容")
    extra_info: Optional[str] = Field(None, description="额外说明或计划")
    enable_search: bool = Field(default=True, description="是否启用网络搜索")


class SlideStyle(BaseModel):
    """幻灯片风格配置"""
    pages: int = Field(default=8, ge=3, le=30, description="页数")
    style: str = Field(default="business", description="风格: business/academic/creative/minimal")
    color_scheme: str = Field(default="blue", description="配色方案: blue/green/red/purple/dark")
    language: str = Field(default="zh-CN", description="语言")


class DataSource(BaseModel):
    """数据来源"""
    title: str
    url: str
    summary: str
    is_trusted: bool = False


class PlanResponse(BaseModel):
    """方案响应"""
    plan_id: str
    title: str
    outline: list[dict]
    suggested_pages: int
    suggested_style: str
    summary: str
    data_sources: list[DataSource] = []


class UpdatePlanRequest(BaseModel):
    """编辑方案"""
    plan_id: str
    title: Optional[str] = None
    outline: Optional[list[dict]] = None


class ConfirmPlanRequest(BaseModel):
    """确认方案"""
    plan_id: str
    pages: int
    style: str
    color_scheme: str = "blue"
    custom_colors: list[str] = Field(default_factory=list, description="自定义 HEX 色值列表")
    custom_style: str = Field(default="", description="自定义风格描述")
    # 用户自定义 PPT 元素
    font_scheme: str = Field(default="", description="字体方案: A-G 或自定义")
    layout_density: str = Field(default="", description="布局密度: sparse/normal/dense")
    bg_style: str = Field(default="", description="背景样式")
    page_number: str = Field(default="", description="页码样式")
    border_radius: str = Field(default="", description="圆角大小")
    shadow_level: str = Field(default="", description="阴影强度")
    content_align: str = Field(default="", description="内容对齐")
    extra_options: dict = Field(default_factory=dict, description="其他自定义选项")


class GenerateResponse(BaseModel):
    """生成结果"""
    plan_id: str
    html_content: str
    title: str


class EditRequest(BaseModel):
    """用户编辑后提交"""
    plan_id: str
    html_content: str


class ExportRequest(BaseModel):
    """导出PPT"""
    plan_id: str
    html_content: str


class PPTResponse(BaseModel):
    """通用响应"""
    success: bool
    message: str
    data: Optional[dict] = None
