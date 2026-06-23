"""HTML PPT 生成提示词 - 运行时字体拼接版"""

# ── 字体方案定义（运行时按选择拼接） ──────────────────────────────────
FONT_SCHEMES = {
    "A": {
        "name": "现代无衬线（business/minimal/default）",
        "import": "Noto+Sans+SC:wght@300;400;500;700;900,Inter:wght@300;400;500;600;700;800,JetBrains+Mono:wght@400;500;700",
        "title": "'Noto Sans SC','Inter',sans-serif",
        "title_weight": "700-900",
        "body": "'Noto Sans SC','Inter',sans-serif",
        "body_weight": "400-500",
        "accent": "'JetBrains Mono',monospace",
    },
    "B": {
        "name": "人文衬线（academic/literary）",
        "import": "Noto+Serif+SC:wght@400;600;700;900,Playfair+Display:wght@400;700;900,Source+Sans+3:wght@300;400;600",
        "title": "'Noto Serif SC','Playfair Display',serif",
        "title_weight": "700-900",
        "body": "'Source Sans 3','Noto Serif SC',serif",
        "body_weight": "400",
        "accent": "'Noto Serif SC',serif  font-style:italic",
    },
    "C": {
        "name": "圆润可爱（creative/children）",
        "import": "ZCOOL+KuaiLe,Noto+Sans+SC:wght@400;700,Pacifico",
        "title": "'ZCOOL KuaiLe','Noto Sans SC',cursive",
        "title_weight": "700",
        "body": "'Noto Sans SC',sans-serif",
        "body_weight": "400",
        "accent": "'Pacifico',cursive",
    },
    "D": {
        "name": "科技未来（tech/cyber/futuristic）",
        "import": "Orbitron:wght@400;700;900,Rajdhani:wght@300;400;500;600;700,Noto+Sans+SC:wght@300;400;700",
        "title": "'Orbitron','Noto Sans SC',sans-serif",
        "title_weight": "700-900",
        "body": "'Rajdhani','Noto Sans SC',sans-serif",
        "body_weight": "400-500",
        "accent": "'Orbitron',monospace",
    },
    "E": {
        "name": "手写文艺（artistic/poetry/emotional）",
        "import": "Ma+Shan+Zheng,Liu+Jian+Mao+Cao,Noto+Sans+SC:wght@300;400;700",
        "title": "'Ma Shan Zheng',cursive",
        "title_weight": "400",
        "body": "'Noto Sans SC',sans-serif",
        "body_weight": "300-400",
        "accent": "'Liu Jian Mao Cao',cursive",
    },
    "F": {
        "name": "高端商务（luxury/premium/formal）",
        "import": "Cormorant+Garamond:wght@400;600;700;900,Noto+Serif+SC:wght@400;700,Montserrat:wght@300;400;500;600;700",
        "title": "'Cormorant Garamond','Noto Serif SC',serif",
        "title_weight": "700-900",
        "body": "'Montserrat','Noto Sans SC',sans-serif",
        "body_weight": "300-400",
        "accent": "'Montserrat',sans-serif  text-transform:uppercase  letter-spacing:2px",
    },
    "G": {
        "name": "极简留白（zen/minimal/whitespace）",
        "import": "Noto+Sans+SC:wght@100;300;400;700,Inter:wght@200;300;400;600",
        "title": "'Noto Sans SC','Inter',sans-serif",
        "title_weight": "100-300",
        "body": "'Noto Sans SC','Inter',sans-serif",
        "body_weight": "300",
        "accent": "'Inter',sans-serif  font-weight:200",
    },
}

# 风格→默认字体映射
STYLE_FONT_MAP = {
    "business": "A",
    "minimal": "A",
    "academic": "B",
    "literary": "B",
    "creative": "C",
    "children": "C",
    "tech": "D",
    "cyber": "D",
    "artistic": "E",
    "luxury": "F",
    "premium": "F",
    "zen": "G",
}


def _build_font_section(font_scheme: str, style: str) -> str:
    """只拼接用户选中的字体方案"""
    key = font_scheme.upper() if font_scheme else STYLE_FONT_MAP.get(style, "A")
    if key not in FONT_SCHEMES:
        key = "A"
    f = FONT_SCHEMES[key]
    return f"""【字体方案 {key} - {f['name']}】
Google Fonts 引入: {f['import']}
标题: {f['title']}  weight:{f['title_weight']}
正文: {f['body']}  weight:{f['body_weight']}
装饰/标签: {f['accent']}"""


# ── 系统提示词（精简版） ──────────────────────────────────────────────
HTML_SYSTEM_PROMPT = """你是一个专业的PPT设计与HTML生成器。根据方案生成视觉精美、打印导出友好的HTML格式PPT。

⚠️ 最重要的要求：打印和导出必须正确！ ⚠️
生成的HTML将被程序自动截图为图片嵌入PPTX文件。因此：
- 每个幻灯片的内容必须完整显示在 1280×720 像素区域内
- 不能有任何内容溢出、被裁切、或显示不全
- 所有文字必须可见，不能被其他元素遮挡

【必须严格遵守的结构规则】
1. 整个HTML是一个页面，每个幻灯片是一个 <div class="slide">
2. 每个 .slide 必须：width:1280px; height:720px; position:relative; overflow:hidden;
3. 每个 .slide 必须有 page-break-after: always
4. body 必须有：@page { size: 1280px 720px; margin: 0; }
5. body 必须有 @media print { .slide { box-shadow:none; page-break-after:always; margin:0; } }
6. 所有内容必须在 .slide 容器内部
7. 在 <head> 中用 <link> 引入 Google Fonts

【排版规范】
- 大标题: 36-52px, font-weight: 700-900
- 副标题: 20-30px, font-weight: 400-500
- 正文: 16-20px, line-height: 1.6-1.8
- 小字/标签: 12-14px, font-weight: 500-600
- 中英文混排：英文字体放前面，中文字体做 fallback

【用户自定义元素 - 最高优先级】
当用户指定了以下元素时，必须严格按照用户要求执行，不要用默认值覆盖：
- 字体、布局密度、背景、页码、圆角、阴影、对齐方式

【基础CSS】
- 用 CSS 变量：:root { --primary:; --font-title:; --font-body:; --radius:; --shadow:; }
- 重置：* { margin:0; padding:0; box-sizing:border-box; }
- 每个 slide 用 flex 或 grid 布局

【设计模式示例】

封面页排版：
- 大标题居中或左对齐，36-52px，font-weight:800
- 副标题在标题下方，20-24px，opacity:0.7
- 背景用渐变或色块，加几何装饰元素（圆形、线条、色块）
- 底部放日期/作者等小字

内容页排版：
- 左侧或顶部放页面标题，24-32px
- 要点用卡片、列表或分栏布局
- 善用图标（Unicode: ✦ ◈ ◎ ▸ ● ★ ▪）做视觉引导
- 数据用大数字+小标签的组合展示
- 底部留页码位置（bottom:18px）

结尾页排版：
- 居中大字"谢谢""Thank You""Q&A"
- 可加联系方式或二维码占位
- 背景与封面呼应

【配色原则】
- 主色：标题、强调、按钮
- 辅助色：背景、卡片、分割线
- 文字色：确保对比度 WCAG AA（深底浅字/浅底深字）
- 渐变：linear-gradient / radial-gradient 增加层次感

【内容约束】
- 内容高度 ≤ 85%（约610px），底部留页码
- 每页布局要有变化，避免千篇一律
- 你必须只输出完整的HTML代码，不要有任何解释文字"""


def build_html_prompt(
    title: str,
    outline: list,
    pages: int,
    style: str,
    color_scheme: str,
    user_text: str,
    custom_colors: list[str] | None = None,
    custom_style: str = "",
    font_scheme: str = "",
    layout_density: str = "",
    bg_style: str = "",
    page_number: str = "",
    border_radius: str = "",
    shadow_level: str = "",
    content_align: str = "",
    extra_options: dict | None = None,
) -> str:
    """构建HTML生成提示词 - 运行时拼接字体方案"""
    outline_lines = []
    for i, item in enumerate(outline):
        if isinstance(item, dict):
            t = item.get("title", f"第{i+1}页")
            details = item.get("details", [])
            detail_text = "\n".join(f"    - {d}" for d in details)
            outline_lines.append(f"  第{i+1}页: {t}\n{detail_text}")
        else:
            outline_lines.append(f"  第{i+1}页: {item}")
    outline_text = "\n".join(outline_lines)

    # 配色
    color_desc = f"预设配色: {color_scheme}"
    if custom_colors:
        color_desc += f"\n用户自定义色值（最高优先级）: {', '.join(custom_colors)}"

    # 风格
    style_desc = f"预设风格: {style}"
    if custom_style:
        style_desc += f"\n用户自定义风格（最高优先级）: {custom_style}"

    # 字体方案（只拼接选中的）
    font_section = _build_font_section(font_scheme, style)

    # 用户自定义元素
    user_elements = []
    if layout_density:
        user_elements.append(f"- 布局密度: {layout_density}")
    if bg_style:
        user_elements.append(f"- 背景样式: {bg_style}")
    if page_number:
        user_elements.append(f"- 页码样式: {page_number}")
    if border_radius:
        user_elements.append(f"- 圆角大小: {border_radius}")
    if shadow_level:
        user_elements.append(f"- 阴影强度: {shadow_level}")
    if content_align:
        user_elements.append(f"- 内容对齐: {content_align}")
    if extra_options:
        for k, v in extra_options.items():
            if v:
                user_elements.append(f"- {k}: {v}")

    user_elements_text = ""
    if user_elements:
        user_elements_text = "\n【用户自定义元素（必须优先采用）】\n" + "\n".join(user_elements)

    return f"""请根据以下方案生成视觉精美、打印导出友好的HTML格式PPT：

【PPT标题】{title}

【大纲（共{pages}页）】
{outline_text}

【配置】
- 页数: {pages}
- {style_desc}
- {color_desc}

{font_section}
{user_elements_text}

【用户原始内容】
{user_text}

⚠️ 关键约束（违反会导致导出失败）：
1. 每个 .slide 恰好 1280×720 像素，overflow:hidden
2. 所有内容在 slide 内部可见，不溢出
3. 必须包含 @page 和 @media print 打印样式
4. 必须在 <head> 中引入上面的 Google Fonts
5. 生成完整的 {pages} 页HTML，每页布局要有变化

请直接输出完整的HTML代码。"""
