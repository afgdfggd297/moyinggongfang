"""LangGraph 节点 - PPT 生成工作流"""
import json
import uuid
import logging
from langchain_core.messages import HumanMessage, AIMessage

from app.core.langgraph.state import PPTState
from app.core.config import get_settings
from app.services.llm_service import llm_service

settings = get_settings()
from app.services.search_service import search_service
from app.services.web_fetch import web_fetch_tool
from app.prompts.plan_prompt import PLAN_SYSTEM_PROMPT, PLAN_USER_TEMPLATE

logger = logging.getLogger(__name__)


async def plan_node(state: PPTState) -> dict:
    """方案规划节点：分析用户输入，生成PPT方案"""
    try:
        user_text = state.get("user_text", "")
        extra_info = state.get("extra_info", "")
        enable_search = state.get("enable_search", True)

        if not user_text:
            return {"error": "未收到用户输入", "current_step": "error"}

        extra_section = f"【额外说明】\n{extra_info}" if extra_info else ""

        # 搜索 + WebFetch 五阶段流水线
        search_context = ""
        data_sources = []  # 数据来源列表
        if enable_search:
            logger.info("[plan] 搜索相关资料...")
            try:
                titles, urls = search_service.search_for_plan(user_text)
                if urls:
                    summaries = []
                    for i, url in enumerate(urls[:3]):
                        logger.info("[plan] WebFetch 抓取: %s", url[:60])
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
                        logger.info("[plan] 获取到参考资料，长度=%d", len(search_context))
            except Exception as e:
                logger.warning("[plan] 搜索/抓取失败，跳过: %s", e)

        messages = [
            {"role": "system", "content": PLAN_SYSTEM_PROMPT},
            {"role": "user", "content": PLAN_USER_TEMPLATE.format(
                user_text=user_text,
                extra_section=extra_section,
                search_context=search_context,
            )},
        ]

        result = await llm_service.call_json(messages, temperature=settings.LLM_PLAN_TEMPERATURE)

        plan_id = str(uuid.uuid4())

        logger.info("方案规划完成: plan_id=%s, title=%s", plan_id, result.get("title"))

        return {
            "plan_id": plan_id,
            "title": result.get("title", "未命名PPT"),
            "outline": result.get("outline", []),
            "suggested_pages": result.get("suggested_pages", 8),
            "suggested_style": result.get("suggested_style", "business"),
            "plan_summary": result.get("summary", ""),
            "data_sources": data_sources,
            "current_step": "plan_done",
            "error": None,
            "messages": [AIMessage(content=json.dumps(result, ensure_ascii=False))],
        }

    except Exception as e:
        logger.error("方案规划失败: %s", str(e))
        return {"error": f"方案规划失败: {str(e)}", "current_step": "error"}


async def html_generate_node(state: PPTState) -> dict:
    """HTML生成节点：根据确认的方案生成打印友好的HTML PPT"""
    try:
        title = state.get("title", "PPT")
        outline = state.get("outline", [])
        pages = state.get("confirmed_pages", state.get("suggested_pages", 8))
        style = state.get("confirmed_style", state.get("suggested_style", "business"))
        color_scheme = state.get("confirmed_color", "blue")
        custom_colors = state.get("custom_colors", [])
        custom_style = state.get("custom_style", "")
        user_text = state.get("user_text", "")
        logger.info("[html_gen] 开始生成, title=%s, pages=%d, style=%s, color=%s", title, pages, style, color_scheme)

        from app.prompts.html_prompt import HTML_SYSTEM_PROMPT, build_html_prompt

        user_prompt = build_html_prompt(
            title=title,
            outline=outline,
            pages=pages,
            style=style,
            color_scheme=color_scheme,
            user_text=user_text,
            custom_colors=custom_colors,
            custom_style=custom_style,
        )

        messages = [
            {"role": "system", "content": HTML_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        logger.info("[html_gen] 调用LLM, prompt长度=%d", len(user_prompt))
        html_content = await llm_service.call(messages, temperature=settings.LLM_HTML_TEMPERATURE, max_tokens=settings.LLM_HTML_MAX_TOKENS)
        logger.info("[html_gen] LLM返回原始长度=%d", len(html_content) if html_content else 0)

        if not html_content:
            return {"error": "LLM返回空内容", "current_step": "error", "html_content": ""}

        # 清理HTML内容
        html_content = html_content.strip()
        if html_content.startswith("```html"):
            html_content = html_content[7:]
        if html_content.startswith("```"):
            html_content = html_content[3:]
        if html_content.endswith("```"):
            html_content = html_content[:-3]
        html_content = html_content.strip()

        logger.info("[html_gen] 清理后HTML长度=%d", len(html_content))

        return {
            "html_content": html_content,
            "current_step": "html_done",
            "error": None,
            "messages": [AIMessage(content="HTML PPT 生成完成，共{}页".format(pages))],
        }

    except Exception as e:
        logger.error("HTML生成失败: %s", str(e))
        return {"error": f"HTML生成失败: {str(e)}", "current_step": "error"}
