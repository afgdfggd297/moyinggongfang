"""DOCX 内容生成提示词"""

DOCX_CONTENT_SYSTEM_PROMPT = """你是一个专业的文档内容生成器。根据方案生成结构化的HTML文档内容，用于预览和导出。

【任务】
根据用户提供的方案大纲，生成完整的文档内容。输出为HTML格式，便于预览，后续会转换为DOCX。

【规则】
1. 严格按照大纲结构生成内容
2. 每个章节要有实质性的内容，不要空洞的占位符
3. 使用合适的HTML标签：h1-h6标题, p段落, ul/ol列表, table表格
4. 内容要专业、准确、有逻辑性
5. 保持语言风格一致

【输出格式】
输出完整的HTML文档内容，包含：
- 文档标题（h1）
- 各章节内容（h2-h6 + 内容）
- 不要包含<html><head><body>等外层标签，只输出文档内容部分

【质量要求】
- 每个段落至少3-5句话
- 列表项要有具体内容
- 表格要有清晰的结构
- 数据要合理（可以是示例数据）
- 语言流畅，逻辑清晰

【风格适配】
- formal: 用词正式，结构严谨
- academic: 引用规范，论证严密
- technical: 术语准确，步骤清晰
- creative: 语言生动，形式多样
- report: 数据驱动，结论明确"""


def build_docx_content_prompt(
    title: str,
    outline: list,
    style: str,
    user_text: str,
    custom_style: str = "",
) -> str:
    """构建DOCX内容生成提示词"""
    outline_lines = []
    for i, item in enumerate(outline):
        if isinstance(item, dict):
            t = item.get("title", f"章节{i+1}")
            content_type = item.get("content_type", "paragraph")
            level = item.get("level", 1)
            details = item.get("details", [])
            detail_text = "\n".join(f"  - {d}" for d in details) if details else ""
            outline_lines.append(f"{'  ' * (level-1)}{t} ({content_type})\n{detail_text}")
        else:
            outline_lines.append(f"章节{i+1}: {item}")
    outline_text = "\n".join(outline_lines)

    # 风格
    style_desc = f"预设风格: {style}"
    if custom_style:
        style_desc += f"\n用户自定义风格（最高优先级）: {custom_style}"

    return f"""请根据以下方案生成完整的文档内容：

【文档标题】{title}

【大纲结构】
{outline_text}

【配置】
- {style_desc}

【用户原始内容】
{user_text}

⚠️ 关键要求：
1. 严格按照大纲结构生成内容
2. 每个章节要有实质性内容，不要空洞描述
3. 使用合适的HTML标签（h2-h4标题, p段落, ul/ol列表, table表格）
4. 内容要专业、准确、有逻辑性
5. 保持语言风格一致

请直接输出文档内容的HTML代码。"""
