"""DOCX 相关数据模型"""
from pydantic import BaseModel, Field
from typing import Optional


class DocxPlanRequest(BaseModel):
    """用户提交需求"""
    text: str = Field(..., description="用户输入的文字内容")
    extra_info: Optional[str] = Field(None, description="额外说明或计划")
    enable_search: bool = Field(default=True, description="是否启用网络搜索")


class DocxPlanResponse(BaseModel):
    """方案响应"""
    plan_id: str
    title: str
    outline: list[dict]
    suggested_style: str
    summary: str
    data_sources: list[dict] = []


class DocxConfirmRequest(BaseModel):
    """确认方案"""
    plan_id: str
    style: str = "formal"
    custom_style: str = Field(default="", description="自定义风格描述")


class DocxGenerateResponse(BaseModel):
    """生成结果"""
    plan_id: str
    html_content: str
    title: str


class DocxEditRequest(BaseModel):
    """用户编辑后提交"""
    plan_id: str
    html_content: str


class DocxExportRequest(BaseModel):
    """导出DOCX"""
    plan_id: str
    html_content: str


class DocxResponse(BaseModel):
    """通用响应"""
    success: bool
    message: str
    data: Optional[dict] = None
