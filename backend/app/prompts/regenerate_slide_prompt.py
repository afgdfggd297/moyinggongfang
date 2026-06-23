"""单页重生成提示词"""

REGENERATE_SLIDE_SYSTEM_PROMPT = """你是一个专业的PPT设计与HTML生成器。你需要重生成PPT中的某一页幻灯片。

【任务】
根据用户提供的完整HTML和指令，只重新生成目标页的HTML代码，保持与整体风格一致。

【规则】
1. 只输出目标页的 <div class="slide">...</div>，不要输出完整HTML
2. 保持与上下文页一致的：配色、字体、圆角、阴影等视觉风格
3. 尺寸严格 1280×720px，overflow:hidden
4. 如果用户给了指令，优先按指令调整；否则按大纲重新设计该页

【输出格式】
只输出一个 <div class="slide">...</div> 标签，不要有其他内容。"""


def build_regenerate_prompt(
    target_index: int,
    target_outline: dict,
    prev_slide_html: str,
    next_slide_html: str,
    full_html_head: str,
    user_instruction: str,
) -> str:
    """构建单页重生成提示词"""
    parts = []

    # 上下文
    if prev_slide_html:
        parts.append(f"【上一页 HTML（参考风格）】\n{prev_slide_html}")
    if next_slide_html:
        parts.append(f"【下一页 HTML（参考风格）】\n{next_slide_html}")

    # 目标页大纲
    title = target_outline.get("title", f"第{target_index + 1}页")
    details = target_outline.get("details", [])
    detail_text = "\n".join(f"- {d}" for d in details) if details else "（无详细大纲）"
    parts.append(f"【目标页大纲】\n标题: {title}\n要点:\n{detail_text}")

    # 用户指令
    if user_instruction:
        parts.append(f"【用户指令（最高优先级）】\n{user_instruction}")

    parts.append(f"请重新生成第{target_index + 1}页的HTML。只输出 <div class=\"slide\">...</div>。")

    return "\n\n".join(parts)
