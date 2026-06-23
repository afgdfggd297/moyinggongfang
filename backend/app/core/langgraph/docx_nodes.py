"""LangGraph 节点 - DOCX 生成工作流"""
import json
import uuid
import logging
from langchain_core.messages import AIMessage

from app.core.langgraph.docx_state import DocxState
from app.core.config import get_settings
from app.services.llm_service import llm_service
from app.services.search_service import search_service
from app.services.web_fetch import web_fetch_tool
from app.prompts.docx_plan_prompt import DOCX_PLAN_SYSTEM_PROMPT, DOCX_PLAN_USER_TEMPLATE
from app.prompts.docx_content_prompt import DOCX_CONTENT_SYSTEM_PROMPT, build_docx_content_prompt

settings = get_settings()
logger = logging.getLogger(__name__)


async def docx_plan_node(state: DocxState) -> dict:
    """方案规划节点：分析用户输入，生成文档方案"""
    try:
        user_text = state.get("user_text", "")
        extra_info = state.get("extra_info", "")
        enable_search = state.get("enable_search", True)

        if not user_text:
            return {"error": "未收到用户输入", "current_step": "error"}

        extra_section = f"【额外说明】\n{extra_info}" if extra_info else ""

        # 搜索 + WebFetch
        search_context = ""
        data_sources = []
        if enable_search:
            logger.info("[docx_plan] 搜索相关资料...")
            try:
                titles, urls = search_service.search_for_plan(user_text)
                if urls:
                    summaries = []
                    for i, url in enumerate(urls[:3]):
                        logger.info("[docx_plan] WebFetch 抓取: %s", url[:60])
                        result = await web_fetch_tool.fetch_and_summarize(url, user_text)
                        title = titles[i] if i < len(titles) else url[:40]
                        summary_text = result.get("summary", "")
                        if summary_text:
                            summaries.append(f"【参考】{title}\n{summary_text}")
                            data_sources.append({
                                "title": title,
                                "url": url,
                                "summary": summary_text[:300],
                                "is_trusted": result.get("is_trusted", False),
                            })
                    if summaries:
                        search_context = "\n\n【参考资料】\n" + "\n\n".join(summaries)
                        logger.info("[docx_plan] 获取到参考资料，长度=%d", len(search_context))
            except Exception as e:
                logger.warning("[docx_plan] 搜索/抓取失败，跳过: %s", e)

        messages = [
            {"role": "system", "content": DOCX_PLAN_SYSTEM_PROMPT},
            {"role": "user", "content": DOCX_PLAN_USER_TEMPLATE.format(
                user_text=user_text,
                extra_section=extra_section,
                search_context=search_context,
            )},
        ]

        result = await llm_service.call_json(messages, temperature=settings.LLM_PLAN_TEMPERATURE)

        plan_id = str(uuid.uuid4())

        logger.info("文档方案规划完成: plan_id=%s, title=%s", plan_id, result.get("title"))

        return {
            "plan_id": plan_id,
            "title": result.get("title", "未命名文档"),
            "outline": result.get("outline", []),
            "suggested_style": result.get("suggested_style", "formal"),
            "plan_summary": result.get("summary", ""),
            "data_sources": data_sources,
            "current_step": "plan_done",
            "error": None,
            "messages": [AIMessage(content=json.dumps(result, ensure_ascii=False))],
        }

    except Exception as e:
        logger.error("文档方案规划失败: %s", str(e))
        return {"error": f"文档方案规划失败: {str(e)}", "current_step": "error"}


async def docx_content_node(state: DocxState) -> dict:
    """内容生成节点：根据确认的方案生成文档内容"""
    try:
        title = state.get("title", "文档")
        outline = state.get("outline", [])
        style = state.get("confirmed_style", state.get("suggested_style", "formal"))
        custom_style = state.get("custom_style", "")
        user_text = state.get("user_text", "")

        logger.info("[docx_content] 开始生成, title=%s, style=%s", title, style)

        user_prompt = build_docx_content_prompt(
            title=title,
            outline=outline,
            style=style,
            user_text=user_text,
            custom_style=custom_style,
        )

        messages = [
            {"role": "system", "content": DOCX_CONTENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        logger.info("[docx_content] 调用LLM, prompt长度=%d", len(user_prompt))
        markdown_content = await llm_service.call(messages, temperature=settings.LLM_HTML_TEMPERATURE, max_tokens=settings.LLM_HTML_MAX_TOKENS)
        logger.info("[docx_content] LLM返回原始长度=%d", len(markdown_content) if markdown_content else 0)

        if not markdown_content:
            return {"error": "LLM返回空内容", "current_step": "error", "markdown_content": ""}

        # 清理 Markdown 内容
        markdown_content = markdown_content.strip()
        if markdown_content.startswith("```markdown"):
            markdown_content = markdown_content[11:]
        if markdown_content.startswith("```"):
            markdown_content = markdown_content[3:]
        if markdown_content.endswith("```"):
            markdown_content = markdown_content[:-3]
        markdown_content = markdown_content.strip()

        logger.info("[docx_content] 清理后Markdown长度=%d", len(markdown_content))

        return {
            "markdown_content": markdown_content,
            "current_step": "content_done",
            "error": None,
            "messages": [AIMessage(content="文档内容生成完成")],
        }

    except Exception as e:
        logger.error("文档内容生成失败: %s", str(e))
        return {"error": f"文档内容生成失败: {str(e)}", "current_step": "error"}
