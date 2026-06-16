"""LangGraph PPT 生成工作流"""
from langgraph.graph import StateGraph, END

from app.core.langgraph.state import PPTState
from app.core.langgraph.nodes import plan_node, html_generate_node
from app.core.langgraph.edges import route_after_plan, route_after_html


def create_ppt_graph() -> StateGraph:
    """创建PPT生成工作流状态图"""
    workflow = StateGraph(PPTState)

    # 添加节点
    workflow.add_node("plan", plan_node)
    workflow.add_node("html_generate", html_generate_node)

    # 定义入口
    workflow.set_entry_point("plan")

    # 方案规划后的条件路由
    workflow.add_conditional_edges(
        "plan",
        route_after_plan,
        {
            "wait_confirm": END,   # 等待用户确认（前端交互）
            "error": END,
        },
    )

    # HTML生成后的路由
    workflow.add_conditional_edges(
        "html_generate",
        route_after_html,
        {
            "done": END,
            "error": END,
        },
    )

    return workflow


def compile_graph():
    """编译图"""
    workflow = create_ppt_graph()
    return workflow.compile()
