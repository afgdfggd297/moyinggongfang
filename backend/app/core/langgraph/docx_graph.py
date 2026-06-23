"""LangGraph DOCX 生成工作流"""
from langgraph.graph import StateGraph, END

from app.core.langgraph.docx_state import DocxState
from app.core.langgraph.docx_nodes import docx_plan_node, docx_content_node


def create_docx_graph() -> StateGraph:
    """创建DOCX生成工作流状态图"""
    workflow = StateGraph(DocxState)

    # 添加节点
    workflow.add_node("plan", docx_plan_node)
    workflow.add_node("content_generate", docx_content_node)

    # 定义入口
    workflow.set_entry_point("plan")

    # 方案规划后的条件路由
    def route_after_plan(state: DocxState) -> str:
        if state.get("error"):
            return "error"
        return "wait_confirm"

    workflow.add_conditional_edges(
        "plan",
        route_after_plan,
        {
            "wait_confirm": END,   # 等待用户确认
            "error": END,
        },
    )

    # 内容生成后的路由
    def route_after_content(state: DocxState) -> str:
        if state.get("error"):
            return "error"
        return "done"

    workflow.add_conditional_edges(
        "content_generate",
        route_after_content,
        {
            "done": END,
            "error": END,
        },
    )

    return workflow


def compile_docx_graph():
    """编译DOCX图"""
    workflow = create_docx_graph()
    return workflow.compile()
