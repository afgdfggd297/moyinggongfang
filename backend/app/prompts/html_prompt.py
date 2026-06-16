"""HTML PPT 生成提示词 - 多字体 + 用户自定义版"""

HTML_SYSTEM_PROMPT = """你是一个专业的PPT设计与HTML生成器。根据方案生成视觉精美、打印导出友好的HTML格式PPT。

⚠️ 最重要的要求：打印和导出必须正确！ ⚠️
生成的HTML将被程序自动截图为图片嵌入PPTX文件。因此：
- 每个幻灯片的内容必须完整显示在 1280×720 像素区域内
- 不能有任何内容溢出、被裁切、或显示不全
- 每页内容量适中，不能太少（空白页）也不能太多（溢出）
- 所有文字必须可见，不能被其他元素遮挡

【必须严格遵守的结构规则】
1. 整个HTML是一个页面，每个幻灯片是一个 <div class="slide">
2. 每个 .slide 必须：width:1280px; height:720px; position:relative; overflow:hidden;
3. 每个 .slide 必须有 page-break-after: always
4. body 必须有：@page { size: 1280px 720px; margin: 0; }
5. body 必须有 @media print { .slide { box-shadow:none; page-break-after:always; margin:0; } }
6. 所有内容必须在 .slide 容器内部
7. 在 <head> 中用 <link> 引入 Google Fonts

【字体方案库 - 根据风格选择，用户指定时以用户为准】

◇ 方案A - 现代无衬线（business/minimal/default）
  引入: Noto+Sans+SC:wght@300;400;500;700;900,Inter:wght@300;400;500;600;700;800,JetBrains+Mono:wght@400;500;700
  标题: 'Noto Sans SC','Inter',sans-serif  weight:700-900
  正文: 'Noto Sans SC','Inter',sans-serif  weight:400-500
  标签: 'JetBrains Mono',monospace

◇ 方案B - 人文衬线（academic/literary）
  引入: Noto+Serif+SC:wght@400;600;700;900,Playfair+Display:wght@400;700;900,Source+Sans+3:wght@300;400;600
  标题: 'Noto Serif SC','Playfair Display',serif  weight:700-900
  正文: 'Source Sans 3','Noto Serif SC',serif  weight:400
  引用: 'Noto Serif SC',serif  font-style:italic

◇ 方案C - 圆润可爱（creative/children）
  引入: ZCOOL+KuaiLe,Noto+Sans+SC:wght@400;700,Pacifico
  标题: 'ZCOOL KuaiLe','Noto Sans SC',cursive  weight:700
  正文: 'Noto Sans SC',sans-serif  weight:400
  装饰: 'Pacifico',cursive（仅英文装饰）

◇ 方案D - 科技未来（tech/cyber/futuristic）
  引入: Orbitron:wght@400;700;900,Rajdhani:wght@300;400;500;600;700,Noto+Sans+SC:wght@300;400;700
  标题: 'Orbitron','Noto Sans SC',sans-serif  weight:700-900  letter-spacing:2px
  正文: 'Rajdhani','Noto Sans SC',sans-serif  weight:400-500
  数据: 'Orbitron',monospace

◇ 方案E - 手写文艺（artistic/poetry/emotional）
  引入: Ma+Shan+Zheng,Liu+Jian+Mao+Cao,Noto+Sans+SC:wght@300;400;700
  标题: 'Ma Shan Zheng',cursive  weight:400（毛笔书法感）
  正文: 'Noto Sans SC',sans-serif  weight:300-400
  点缀: 'Liu Jian Mao Cao',cursive（行草装饰）

◇ 方案F - 高端商务（luxury/premium/formal）
  引入: Cormorant+Garamond:wght@400;600;700;900,Noto+Serif+SC:wght@400;700,Montserrat:wght@300;400;500;600;700
  标题: 'Cormorant Garamond','Noto Serif SC',serif  weight:700-900  letter-spacing:1px
  正文: 'Montserrat','Noto Sans SC',sans-serif  weight:300-400
  小字: 'Montserrat',sans-serif  weight:500  text-transform:uppercase  letter-spacing:2px

◇ 方案G - 极简留白（zen/minimal/whitespace）
  引入: Noto+Sans+SC:wght@100;300;400;700,Inter:wght@200;300;400;600
  标题: 'Noto Sans SC','Inter',sans-serif  weight:100-300（超细体）letter-spacing:4px
  正文: 'Noto Sans SC','Inter',sans-serif  weight:300  line-height:2
  数字: 'Inter',sans-serif  font-weight:200  font-size:较大

【排版规范】
- 大标题: 36-52px, font-weight: 700-900, letter-spacing: 根据风格调整
- 副标题: 20-30px, font-weight: 400-500
- 正文: 16-20px, line-height: 1.6-1.8
- 小字/标签: 12-14px, font-weight: 500-600
- 中英文混排：英文字体放前面，中文字体做 fallback

【用户自定义元素 - 最高优先级】
当用户指定了以下元素时，必须严格按照用户要求执行，不要用默认值覆盖：
- 字体：用户指定的字体优先于风格方案
- 布局密度：稀疏/适中/紧凑
- 背景：纯色/渐变/图案/透明
- 页码：位置/样式/是否显示
- 圆角大小
- 阴影强度
- 动画效果

【基础CSS结构】
- 用 CSS 变量：:root { --primary:; --font-title:; --font-body:; --radius:; --shadow:; }
- 重置：* { margin:0; padding:0; box-sizing:border-box; }
- 每个 slide 用 flex 或 grid 布局

【设计质量要求】
- 封面页：视觉冲击力，大标题 + 副标题 + 装饰
- 内容页：层次分明，标题 + 要点 + 可视化元素
- 结尾页：简洁收尾
- 每页布局不同，避免千篇一律
- 善用色块、圆角卡片、渐变、阴影
- 使用图标（Unicode: ✦ ◈ ◎ ▸ ● ★ ▪ 等）

【配色方案】
- 主色：标题、强调
- 辅助色：背景、卡片
- 文字色：确保对比度（WCAG AA）
- 渐变：linear-gradient / radial-gradient

【内容布局约束】
- 内容高度 ≤ 85%（约610px），底部留页码
- 页码：bottom:18px
- 优先 flex 布局，少用绝对定位

你必须只输出完整的HTML代码，不要有任何解释文字。"""


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
    """构建HTML生成提示词"""
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

    # 用户自定义元素
    user_elements = []
    if font_scheme:
        user_elements.append(f"- 字体方案: {font_scheme}")
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
{user_elements_text}

【用户原始内容】
{user_text}

⚠️ 关键约束（违反会导致导出失败）：
1. 每个 .slide 恰好 1280×720 像素，overflow:hidden
2. 所有内容在 slide 内部可见，不溢出
3. 必须包含 @page 和 @media print 打印样式
4. 必须在 <head> 中引入 Google Fonts
5. 根据风格选择字体方案（A-G），用户指定字体时以用户为准
6. 生成完整的 {pages} 页HTML

请直接输出完整的HTML代码。"""
