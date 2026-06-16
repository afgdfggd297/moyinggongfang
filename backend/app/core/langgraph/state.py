"""LangGraph PPT 生成工作流状态定义"""
from typing import TypedDict, Optional, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import AnyMessage


class PPTState(TypedDict):
    """PPT 生成工作流全局状态"""

    # 消息历史
    messages: Annotated[list[AnyMessage], add_messages]

    # 输入
    user_text: str                # 用户输入的文字
    extra_info: str               # 额外说明
    enable_search: bool           # 是否启用网络搜索

    # 方案规划
    plan_id: str                  # 方案ID
    title: str                    # PPT标题
    outline: list[dict]           # 大纲列表 [{title, details}]
    suggested_pages: int          # 建议页数
    suggested_style: str          # 建议风格
    plan_summary: str             # 方案摘要

    # 用户确认的配置
    confirmed_pages: int          # 用户确认的页数
    confirmed_style: str          # 用户确认的风格
    confirmed_color: str          # 用户确认的配色
    custom_colors: list[str]      # 自定义色值
    custom_style: str             # 自定义风格描述
    plan_confirmed: bool          # 方案是否已确认

    # HTML 生成
    html_content: str             # 生成的HTML内容
    html_confirmed: bool          # HTML是否已确认（用户编辑后）

    # 导出
    pptx_path: str                # PPTX文件路径
    export_ready: bool            # 是否可导出

    # 状态控制
    current_step: str             # 当前步骤
    error: Optional[str]          # 错误信息
