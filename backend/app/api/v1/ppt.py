"""PPT 生成 API 路由 - 支持流式输出"""
import asyncio
import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.schemas.ppt import (
    PlanRequest,
    PlanResponse,
    UpdatePlanRequest,
    ConfirmPlanRequest,
    GenerateResponse,
    EditRequest,
    ExportRequest,
    PPTResponse,
)
from app.core.langgraph.graph import compile_graph
from app.core.config import get_settings
from app.services.llm_service import llm_service

settings = get_settings()
from app.services.ppt_export import ppt_export_service
from app.services.redis_store import plan_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ppt", tags=["ppt"])

# 编译工作流图
graph = compile_graph()


@router.post("/plan", response_model=PlanResponse)
async def create_plan(req: PlanRequest):
    """步骤1: 提交需求，AI规划方案"""
    try:
        logger.info("[plan] 收到方案请求, text_length=%d", len(req.text))
        state = {
            "user_text": req.text,
            "extra_info": req.extra_info or "",
            "enable_search": req.enable_search,
            "messages": [],
            "plan_id": "",
            "title": "",
            "outline": [],
            "suggested_pages": 8,
            "suggested_style": "business",
            "plan_summary": "",
            "confirmed_pages": 8,
            "confirmed_style": "business",
            "confirmed_color": "blue",
            "plan_confirmed": False,
            "html_content": "",
            "html_confirmed": False,
            "pptx_path": "",
            "export_ready": False,
            "current_step": "start",
            "error": None,
        }

        result = await graph.ainvoke(state)

        if result.get("error"):
            logger.error("[plan] 方案规划失败: %s", result["error"])
            raise HTTPException(status_code=500, detail=result["error"])

        plan_id = result["plan_id"]

        # 存储方案状态到 Redis
        plan_store.save(plan_id, {
            "user_text": req.text,
            "extra_info": req.extra_info or "",
            "title": result["title"],
            "outline": result["outline"],
            "suggested_pages": result["suggested_pages"],
            "suggested_style": result["suggested_style"],
            "plan_summary": result["plan_summary"],
            "data_sources": result.get("data_sources", []),
        })

        logger.info("[plan] 方案规划成功, plan_id=%s, title=%s", plan_id, result["title"])
        return PlanResponse(
            plan_id=plan_id,
            title=result["title"],
            outline=result["outline"],
            suggested_pages=result["suggested_pages"],
            suggested_style=result["suggested_style"],
            summary=result["plan_summary"],
            data_sources=result.get("data_sources", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[plan] 创建方案异常: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-plan", response_model=PlanResponse)
async def update_plan(req: UpdatePlanRequest):
    """编辑方案 - 用户可修改标题和大纲"""
    stored = plan_store.get(req.plan_id)
    if not stored:
        raise HTTPException(status_code=404, detail="方案不存在")

    if req.title is not None:
        stored["title"] = req.title
    if req.outline is not None:
        stored["outline"] = req.outline
        stored["suggested_pages"] = len(req.outline)

    plan_store.save(req.plan_id, stored)
    logger.info("[update-plan] 方案已更新: %s", req.plan_id)

    return PlanResponse(
        plan_id=req.plan_id,
        title=stored["title"],
        outline=stored["outline"],
        suggested_pages=stored["suggested_pages"],
        suggested_style=stored["suggested_style"],
        summary=stored["plan_summary"],
    )


@router.post("/confirm-plan", response_model=GenerateResponse)
async def confirm_plan(req: ConfirmPlanRequest):
    """步骤2: 确认方案并生成HTML PPT（非流式）"""
    try:
        stored = plan_store.get(req.plan_id)
        if not stored:
            raise HTTPException(status_code=404, detail="方案不存在，请重新创建")

        state = _build_state(stored, req)

        from app.core.langgraph.nodes import html_generate_node
        logger.info("[confirm-plan] 开始生成HTML, plan_id=%s, pages=%s, style=%s", req.plan_id, req.pages, req.style)
        result = await html_generate_node(state)

        if result.get("error"):
            logger.error("[confirm-plan] HTML生成失败: %s", result["error"])
            raise HTTPException(status_code=500, detail=result["error"])

        html_content = result.get("html_content", "")
        logger.info("[confirm-plan] HTML生成成功, length=%d", len(html_content))
        if not html_content:
            raise HTTPException(status_code=500, detail="HTML内容为空，LLM可能未返回有效内容")

        _update_store(req.plan_id, req, html_content)

        return GenerateResponse(plan_id=req.plan_id, html_content=html_content, title=stored["title"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[confirm-plan] 异常: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm-plan/stream")
async def confirm_plan_stream(req: ConfirmPlanRequest):
    """步骤2: 确认方案并生成HTML PPT（SSE流式输出）"""
    stored = plan_store.get(req.plan_id)
    if not stored:
        raise HTTPException(status_code=404, detail="方案不存在")

    async def event_generator():
        try:
            from app.prompts.html_prompt import HTML_SYSTEM_PROMPT, build_html_prompt

            user_prompt = build_html_prompt(
                title=stored["title"],
                outline=stored["outline"],
                pages=req.pages,
                style=req.style,
                color_scheme=req.color_scheme,
                user_text=stored["user_text"],
                custom_colors=req.custom_colors,
                custom_style=req.custom_style,
                font_scheme=req.font_scheme,
                layout_density=req.layout_density,
                bg_style=req.bg_style,
                page_number=req.page_number,
                border_radius=req.border_radius,
                shadow_level=req.shadow_level,
                content_align=req.content_align,
                extra_options=req.extra_options,
            )

            messages = [
                {"role": "system", "content": HTML_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': '开始生成HTML PPT...'})}\n\n"

            # 流式调用LLM
            full_content = ""
            async for chunk in llm_service.call_stream(messages, temperature=settings.LLM_STREAM_TEMPERATURE, max_tokens=16384):
                full_content += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # 清理HTML
            html_content = full_content.strip()
            if html_content.startswith("```html"):
                html_content = html_content[7:]
            if html_content.startswith("```"):
                html_content = html_content[3:]
            if html_content.endswith("```"):
                html_content = html_content[:-3]
            html_content = html_content.strip()

            # 存储
            _update_store(req.plan_id, req, html_content)

            # 发送完成事件
            yield f"data: {json.dumps({'type': 'done', 'html_content': html_content, 'title': stored['title']})}\n\n"
            logger.info("[stream] 流式生成完成, length=%d", len(html_content))

        except Exception as e:
            logger.error("[stream] 流式生成异常: %s", str(e), exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/edit", response_model=GenerateResponse)
async def edit_html(req: EditRequest):
    """步骤3: 用户编辑后提交HTML"""
    stored = plan_store.get(req.plan_id)
    if not stored:
        raise HTTPException(status_code=404, detail="方案不存在")

    stored["html_content"] = req.html_content
    stored["html_confirmed"] = True
    plan_store.save(req.plan_id, stored)
    logger.info("[edit] 保存编辑, plan_id=%s, length=%d", req.plan_id, len(req.html_content))

    return GenerateResponse(plan_id=req.plan_id, html_content=req.html_content, title=stored["title"])


@router.post("/export")
async def export_pptx(req: ExportRequest):
    """步骤4: 导出PPTX文件"""
    try:
        stored = plan_store.get(req.plan_id)
        if not stored:
            raise HTTPException(status_code=404, detail="方案不存在")

        html_content = req.html_content or stored.get("html_content", "")
        if not html_content:
            raise HTTPException(status_code=400, detail="HTML内容为空")

        logger.info("[export] 开始导出PPTX, plan_id=%s, html_length=%d", req.plan_id, len(html_content))
        loop = asyncio.get_event_loop()
        pptx_path = await loop.run_in_executor(
            None, ppt_export_service.html_to_pptx_sync, html_content, req.plan_id
        )

        stored["pptx_path"] = pptx_path
        stored["export_ready"] = True
        plan_store.save(req.plan_id, stored)

        logger.info("[export] PPTX导出成功: %s", pptx_path)
        return PPTResponse(
            success=True,
            message="PPT导出成功",
            data={"plan_id": req.plan_id, "download_url": f"/api/v1/ppt/download/{req.plan_id}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[export] 导出异常: %s", str(e), exc_info=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e) or "导出失败")


@router.get("/download/{plan_id}")
async def download_pptx(plan_id: str):
    """下载PPTX文件"""
    stored = plan_store.get(plan_id)
    if not stored:
        raise HTTPException(status_code=404, detail="方案不存在")

    pptx_path = stored.get("pptx_path", "") or ppt_export_service.get_download_path(plan_id)
    if not pptx_path:
        raise HTTPException(status_code=404, detail="PPT文件未生成，请先导出")

    logger.info("[download] 下载PPTX: %s", pptx_path)
    return FileResponse(
        path=pptx_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"{stored.get('title', 'presentation')}.pptx",
    )


@router.get("/html/{plan_id}")
async def get_html(plan_id: str):
    """获取HTML内容"""
    stored = plan_store.get(plan_id)
    if not stored:
        raise HTTPException(status_code=404, detail="方案不存在")

    html_content = stored.get("html_content", "")
    if not html_content:
        raise HTTPException(status_code=404, detail="HTML未生成")

    return {"plan_id": plan_id, "html_content": html_content}


@router.get("/plan/{plan_id}")
async def get_plan(plan_id: str):
    """获取方案完整数据"""
    stored = plan_store.get(plan_id)
    if not stored:
        raise HTTPException(status_code=404, detail="方案不存在")

    return {
        "plan_id": plan_id,
        "title": stored.get("title", ""),
        "outline": stored.get("outline", []),
        "suggested_pages": stored.get("suggested_pages", 8),
        "suggested_style": stored.get("suggested_style", "business"),
        "summary": stored.get("plan_summary", ""),
        "html_content": stored.get("html_content", ""),
        "data_sources": stored.get("data_sources", []),
    }


def _build_state(stored: dict, req: ConfirmPlanRequest) -> dict:
    """构建工作流状态"""
    return {
        "user_text": stored["user_text"],
        "extra_info": stored["extra_info"],
        "messages": [],
        "plan_id": req.plan_id,
        "title": stored["title"],
        "outline": stored["outline"],
        "suggested_pages": stored["suggested_pages"],
        "suggested_style": stored["suggested_style"],
        "plan_summary": stored["plan_summary"],
        "confirmed_pages": req.pages,
        "confirmed_style": req.style,
        "confirmed_color": req.color_scheme,
        "plan_confirmed": True,
        "html_content": "",
        "html_confirmed": False,
        "pptx_path": "",
        "export_ready": False,
        "current_step": "plan_done",
        "error": None,
    }


def _update_store(plan_id: str, req, html_content: str):
    """更新存储"""
    stored = plan_store.get(plan_id)
    if stored:
        stored["html_content"] = html_content
        stored["confirmed_pages"] = req.pages
        stored["confirmed_style"] = req.style
        stored["confirmed_color"] = req.color_scheme
        plan_store.save(plan_id, stored)
