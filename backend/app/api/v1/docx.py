"""DOCX 生成 API 路由"""
import asyncio
import json
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.docx import (
    DocxPlanRequest,
    DocxPlanResponse,
    DocxConfirmRequest,
    DocxGenerateResponse,
    DocxEditRequest,
    DocxExportRequest,
    DocxResponse,
)
from app.core.langgraph.docx_graph import compile_docx_graph
from app.core.config import get_settings
from app.services.llm_service import llm_service
from app.core.security import get_current_user_optional, TokenPayload

settings = get_settings()
from app.services.docx_export import docx_export_service
from app.services.redis_store import plan_store
from app.db.database import async_session_factory
from app.db import crud, models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/docx", tags=["docx"])

# 编译工作流图
docx_graph = compile_docx_graph()


async def _save_docx_plan_to_db(plan_data: dict, user_id: Optional[uuid.UUID] = None):
    """将方案持久化到 PostgreSQL"""
    try:
        async with async_session_factory() as db:
            if user_id is None:
                return
            plan_id_uuid = uuid.UUID(plan_data.get("plan_id", ""))
            await crud.create_plan(
                db,
                user_id=user_id,
                id=plan_id_uuid,
                title=plan_data.get("title", ""),
                outline=plan_data.get("outline"),
                suggested_style=plan_data.get("suggested_style"),
                plan_summary=plan_data.get("plan_summary"),
                user_text=plan_data.get("user_text"),
                extra_info=plan_data.get("extra_info"),
                data_sources=plan_data.get("data_sources"),
                status=models.PlanStatus.DRAFT,
            )
            logger.info("[docx] 方案已持久化到 PostgreSQL: %s", plan_id_uuid)
    except Exception as e:
        logger.warning("[docx] PostgreSQL 持久化失败（不影响主流程）: %s", e)


async def _update_docx_plan_in_db(plan_id: str, **kwargs):
    """更新 PostgreSQL 中的方案"""
    try:
        async with async_session_factory() as db:
            plan_id_uuid = uuid.UUID(plan_id)
            await crud.update_plan(db, plan_id_uuid, **kwargs)
            logger.info("[docx] PostgreSQL 更新成功: %s", plan_id)
    except Exception as e:
        logger.warning("[docx] PostgreSQL 更新失败: %s", e)


async def _get_stored_docx_plan(plan_id: str) -> Optional[dict]:
    """获取存储的方案（Redis 优先，PostgreSQL 兜底）"""
    stored = plan_store.get(plan_id)
    if stored:
        return stored
    try:
        async with async_session_factory() as db:
            plan_id_uuid = uuid.UUID(plan_id)
            plan = await crud.get_plan(db, plan_id_uuid)
            if plan:
                return {
                    "plan_id": str(plan.id),
                    "title": plan.title,
                    "outline": plan.outline,
                    "suggested_style": plan.suggested_style,
                    "plan_summary": plan.plan_summary,
                    "markdown_content": plan.markdown_content,
                    "user_text": plan.user_text,
                    "extra_info": plan.extra_info,
                    "data_sources": plan.data_sources,
                }
    except Exception as e:
        logger.warning("[docx] PostgreSQL 查询失败: %s", e)
    return None


@router.post("/plan", response_model=DocxPlanResponse)
async def create_docx_plan(
    req: DocxPlanRequest,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional),
):
    """步骤1: 提交需求，获取文档方案"""
    try:
        state = {
            "user_text": req.text,
            "extra_info": req.extra_info or "",
            "enable_search": req.enable_search,
            "messages": [],
            "plan_id": "",
            "title": "",
            "outline": [],
            "suggested_style": "formal",
            "plan_summary": "",
            "confirmed_style": "formal",
            "custom_style": "",
            "plan_confirmed": False,
            "sections": [],
            "markdown_content": "",
            "html_confirmed": False,
            "docx_path": "",
            "export_ready": False,
            "current_step": "start",
            "error": None,
        }

        result = await docx_graph.ainvoke(state)

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        plan_id = result["plan_id"]

        # 保存到 Redis
        plan_data = {
            "plan_id": plan_id,
            "title": result["title"],
            "outline": result["outline"],
            "suggested_style": result["suggested_style"],
            "plan_summary": result["plan_summary"],
            "user_text": req.text,
            "extra_info": req.extra_info or "",
            "data_sources": result.get("data_sources", []),
            "current_step": "plan_done",
        }
        plan_store.save(plan_id, plan_data)

        # 异步持久化到 PostgreSQL
        user_id = uuid.UUID(current_user.sub) if current_user else None
        asyncio.create_task(_save_docx_plan_to_db(plan_data, user_id))

        logger.info("[docx_plan] 方案创建成功: %s", plan_id)

        return DocxPlanResponse(
            plan_id=plan_id,
            title=result["title"],
            outline=result["outline"],
            suggested_style=result["suggested_style"],
            summary=result["plan_summary"],
            data_sources=result.get("data_sources", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[docx_plan] 失败: %s", str(e))
        raise HTTPException(status_code=500, detail=f"方案规划失败: {str(e)}")


@router.post("/confirm", response_model=DocxGenerateResponse)
async def confirm_docx_plan(
    req: DocxConfirmRequest,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional),
):
    """步骤2: 确认方案，生成文档内容（非流式）"""
    stored = await _get_stored_docx_plan(req.plan_id)
    if not stored:
        raise HTTPException(status_code=404, detail="方案不存在")

    from app.core.langgraph.docx_state import DocxState

    state: DocxState = {
        "user_text": stored["user_text"],
        "extra_info": stored.get("extra_info", ""),
        "messages": [],
        "plan_id": req.plan_id,
        "title": stored["title"],
        "outline": stored["outline"],
        "suggested_style": stored.get("suggested_style", "formal"),
        "plan_summary": stored.get("plan_summary", ""),
        "confirmed_style": req.style,
        "custom_style": req.custom_style,
        "plan_confirmed": True,
        "sections": [],
        "markdown_content": "",
        "html_confirmed": False,
        "docx_path": "",
        "export_ready": False,
        "current_step": "plan_done",
        "error": None,
        "enable_search": True,
    }

    try:
        result = await docx_graph.ainvoke(state)

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        markdown_content = result.get("markdown_content", "")

        # 更新存储
        stored["markdown_content"] = markdown_content
        stored["confirmed_style"] = req.style
        stored["current_step"] = "content_done"
        plan_store.save(req.plan_id, stored)

        # 异步更新 PostgreSQL
        asyncio.create_task(_update_docx_plan_in_db(
            req.plan_id,
            markdown_content=markdown_content,
            confirmed_style=req.style,
        ))

        logger.info("[docx_confirm] 内容生成成功: %s", req.plan_id)

        return DocxGenerateResponse(
            plan_id=req.plan_id,
            markdown_content=markdown_content,
            title=stored["title"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[docx_confirm] 失败: %s", str(e))
        raise HTTPException(status_code=500, detail=f"内容生成失败: {str(e)}")


@router.post("/confirm/stream")
async def confirm_docx_plan_stream(
    req: DocxConfirmRequest,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional),
):
    """步骤2: 确认方案，流式生成文档内容"""
    stored = await _get_stored_docx_plan(req.plan_id)
    if not stored:
        raise HTTPException(status_code=404, detail="方案不存在")

    from app.prompts.docx_content_prompt import DOCX_CONTENT_SYSTEM_PROMPT, build_docx_content_prompt

    user_prompt = build_docx_content_prompt(
        title=stored["title"],
        outline=stored["outline"],
        style=req.style,
        user_text=stored["user_text"],
        custom_style=req.custom_style,
    )

    messages = [
        {"role": "system", "content": DOCX_CONTENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    async def event_stream():
        full_content = ""
        try:
            yield json.dumps({"type": "start", "message": "开始生成文档内容..."}, ensure_ascii=False) + "\n"

            async for chunk in llm_service.call_stream(messages, temperature=settings.LLM_STREAM_TEMPERATURE):
                full_content += chunk
                yield json.dumps({"type": "chunk", "content": chunk}, ensure_ascii=False) + "\n"

            # 清理
            markdown_content = full_content.strip()
            if markdown_content.startswith("```html"):
                markdown_content = markdown_content[7:]
            if markdown_content.startswith("```"):
                markdown_content = markdown_content[3:]
            if markdown_content.endswith("```"):
                markdown_content = markdown_content[:-3]
            markdown_content = markdown_content.strip()

            # 保存
            stored["markdown_content"] = markdown_content
            stored["confirmed_style"] = req.style
            stored["current_step"] = "content_done"
            plan_store.save(req.plan_id, stored)

            asyncio.create_task(_update_docx_plan_in_db(
                req.plan_id,
                markdown_content=markdown_content,
                confirmed_style=req.style,
            ))

            yield json.dumps({
                "type": "done",
                "markdown_content": markdown_content,
                "title": stored["title"],
            }, ensure_ascii=False) + "\n"

        except Exception as e:
            logger.error("[docx_stream] 失败: %s", str(e))
            yield json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/edit", response_model=DocxGenerateResponse)
async def edit_docx_html(
    req: DocxEditRequest,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional),
):
    """步骤3: 用户编辑后提交HTML"""
    stored = await _get_stored_docx_plan(req.plan_id)
    if not stored:
        raise HTTPException(status_code=404, detail="方案不存在")

    stored["markdown_content"] = req.markdown_content
    stored["html_confirmed"] = True
    plan_store.save(req.plan_id, stored)

    asyncio.create_task(_update_docx_plan_in_db(req.plan_id, markdown_content=req.markdown_content))

    logger.info("[docx_edit] 保存编辑, plan_id=%s, length=%d", req.plan_id, len(req.markdown_content))

    return DocxGenerateResponse(plan_id=req.plan_id, markdown_content=req.markdown_content, title=stored["title"])


@router.post("/export")
async def export_docx(
    req: DocxExportRequest,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional),
):
    """步骤4: 导出DOCX文件"""
    try:
        stored = await _get_stored_docx_plan(req.plan_id)
        if not stored:
            raise HTTPException(status_code=404, detail="方案不存在")

        markdown_content = req.markdown_content or stored.get("markdown_content", "")
        if not markdown_content:
            raise HTTPException(status_code=400, detail="HTML内容为空")

        title = stored.get("title", "文档")

        logger.info("[docx_export] 开始导出DOCX, plan_id=%s, markdown_length=%d", req.plan_id, len(markdown_content))
        loop = asyncio.get_event_loop()
        docx_path = await loop.run_in_executor(
            None, docx_export_service.markdown_to_docx_sync, markdown_content, title, req.plan_id
        )

        stored["docx_path"] = docx_path
        stored["export_ready"] = True
        plan_store.save(req.plan_id, stored)

        asyncio.create_task(_update_docx_plan_in_db(
            req.plan_id,
            pptx_path=docx_path,
            status=models.PlanStatus.EXPORTED,
        ))

        logger.info("[docx_export] 导出成功: %s", docx_path)

        return DocxResponse(
            success=True,
            message="DOCX导出成功",
            data={"plan_id": req.plan_id, "path": docx_path}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[docx_export] 失败: %s", str(e))
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/download/{plan_id}")
async def download_docx(plan_id: str):
    """下载DOCX文件"""
    stored = await _get_stored_docx_plan(plan_id)
    if not stored:
        raise HTTPException(status_code=404, detail="方案不存在")

    docx_path = stored.get("docx_path", "")
    if not docx_path:
        raise HTTPException(status_code=400, detail="DOCX文件不存在")

    import os
    if not os.path.exists(docx_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    filename = f"{stored.get('title', '文档')}.docx"
    return FileResponse(
        docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )


@router.get("/html/{plan_id}")
async def get_docx_html(plan_id: str):
    """获取HTML内容"""
    stored = await _get_stored_docx_plan(plan_id)
    if not stored:
        raise HTTPException(status_code=404, detail="方案不存在")

    markdown_content = stored.get("markdown_content", "")
    if not markdown_content:
        raise HTTPException(status_code=400, detail="HTML内容为空")

    return {"plan_id": plan_id, "markdown_content": markdown_content}


@router.get("/plan/{plan_id}")
async def get_docx_plan(plan_id: str):
    """获取方案完整数据"""
    stored = await _get_stored_docx_plan(plan_id)
    if not stored:
        raise HTTPException(status_code=404, detail="方案不存在")

    return {
        "plan_id": plan_id,
        "title": stored.get("title", ""),
        "outline": stored.get("outline", []),
        "suggested_style": stored.get("suggested_style", "formal"),
        "summary": stored.get("plan_summary", ""),
        "markdown_content": stored.get("markdown_content", ""),
        "data_sources": stored.get("data_sources", []),
    }
