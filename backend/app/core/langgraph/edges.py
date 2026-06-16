"""LangGraph 边定义 - 路由逻辑"""
from app.core.langgraph.state import PPTState


def route_after_plan(state: PPTState) -> str:
    """方案规划后的路由"""
    if state.get("error"):
        return "error"
    return "wait_confirm"


def route_after_html(state: PPTState) -> str:
    """HTML生成后的路由"""
    if state.get("error"):
        return "error"
    return "done"
