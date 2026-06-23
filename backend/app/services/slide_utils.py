"""HTML 幻灯片拆分/替换工具"""
import re
from typing import Optional


def split_slides(html_content: str) -> list[str]:
    """将完整 HTML 拆分为单个 slide 列表"""
    pattern = r'(<div\s+class="slide"[^>]*>.*?</div>)\s*(?=<div\s+class="slide"|$)'
    matches = re.findall(pattern, html_content, re.DOTALL)
    if not matches:
        # fallback: 按 page-break 或 slide 分割
        matches = re.findall(r'(<div[^>]*class="slide"[^>]*>[\s\S]*?</div>)\s*(?=<div[^>]*class="slide"|$)', html_content)
    return matches


def get_html_head(html_content: str) -> str:
    """提取 <head> 部分（样式、字体等）"""
    match = re.search(r'(<head[\s\S]*?</head>)', html_content, re.IGNORECASE)
    return match.group(1) if match else ""


def get_html_body_attrs(html_content: str) -> str:
    """提取 <body> 标签的属性"""
    match = re.search(r'<body([^>]*)>', html_content, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def replace_slide(html_content: str, index: int, new_slide_html: str) -> str:
    """替换指定索引的 slide"""
    slides = split_slides(html_content)
    if index < 0 or index >= len(slides):
        raise ValueError(f"slide index {index} out of range (0-{len(slides)-1})")

    slides[index] = new_slide_html

    # 重建完整 HTML
    head = get_html_head(html_content)
    body_attrs = get_html_body_attrs(html_content)

    # 提取 <style> 和 <link> 标签
    styles = re.findall(r'(<style[\s\S]*?</style>)', head, re.IGNORECASE)
    links = re.findall(r'(<link[^>]*>)', head, re.IGNORECASE)
    meta = re.findall(r'(<meta[^>]*>)', head, re.IGNORECASE)

    head_content = "\n".join(meta + links + styles)
    slides_content = "\n\n".join(slides)

    return f"""<!DOCTYPE html>
<html>
<head>
{head_content}
</head>
<body{f' {body_attrs}' if body_attrs else ''}>
{slides_content}
</body>
</html>"""
