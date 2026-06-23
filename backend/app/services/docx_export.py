"""DOCX 导出服务 - 使用 python-docx 生成 Word 文档"""
import re
import logging
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class DocxExportService:
    """HTML 转 DOCX 导出服务"""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _setup_styles(self, doc: Document):
        """设置文档样式"""
        # 设置正文样式
        style = doc.styles['Normal']
        font = style.font
        font.name = '宋体'
        font.size = Pt(12)
        font.color.rgb = RGBColor(0x33, 0x33, 0x33)

        # 设置段落格式
        paragraph_format = style.paragraph_format
        paragraph_format.space_after = Pt(6)
        paragraph_format.line_spacing = 1.5

    def _add_heading(self, doc: Document, text: str, level: int):
        """添加标题"""
        heading = doc.add_heading(text, level=level)
        # 设置中文字体
        for run in heading.runs:
            run.font.name = '黑体'

    def _add_paragraph(self, doc: Document, text: str, bold: bool = False):
        """添加段落"""
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold = bold
        run.font.name = '宋体'
        run.font.size = Pt(12)

    def _add_list(self, doc: Document, items: list, ordered: bool = False):
        """添加列表"""
        for i, item in enumerate(items):
            if ordered:
                p = doc.add_paragraph(f"{i+1}. {item}")
            else:
                p = doc.add_paragraph(f"• {item}")
            p.style = doc.styles['List Bullet']

    def _add_table(self, doc: Document, headers: list, rows: list):
        """添加表格"""
        table = doc.add_table(rows=1, cols=len(headers))
        table.style = 'Table Grid'

        # 表头
        for i, header in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = header
            # 设置表头样式
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.bold = True

        # 数据行
        for row_data in rows:
            row = table.add_row()
            for i, cell_text in enumerate(row_data):
                row.cells[i].text = str(cell_text)

    def _parse_html_content(self, html_content: str) -> list:
        """解析HTML内容为结构化数据"""
        soup = BeautifulSoup(html_content, 'html.parser')
        elements = []

        for elem in soup.children:
            if isinstance(elem, Tag):
                if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    level = int(elem.name[1])
                    elements.append({
                        'type': 'heading',
                        'level': level,
                        'text': elem.get_text().strip()
                    })
                elif elem.name == 'p':
                    elements.append({
                        'type': 'paragraph',
                        'text': elem.get_text().strip()
                    })
                elif elem.name in ['ul', 'ol']:
                    items = [li.get_text().strip() for li in elem.find_all('li')]
                    elements.append({
                        'type': 'list',
                        'ordered': elem.name == 'ol',
                        'items': items
                    })
                elif elem.name == 'table':
                    headers = [th.get_text().strip() for th in elem.find_all('th')]
                    rows = []
                    for tr in elem.find_all('tr')[1:]:
                        row = [td.get_text().strip() for td in tr.find_all('td')]
                        rows.append(row)
                    elements.append({
                        'type': 'table',
                        'headers': headers,
                        'rows': rows
                    })

        return elements

    def html_to_docx(self, html_content: str, title: str, plan_id: str) -> str:
        """将HTML内容转换为DOCX文件"""
        try:
            doc = Document()
            self._setup_styles(doc)

            # 添加文档标题
            doc.add_heading(title, level=0)

            # 解析HTML内容
            elements = self._parse_html_content(html_content)

            for elem in elements:
                elem_type = elem.get('type')

                if elem_type == 'heading':
                    self._add_heading(doc, elem['text'], elem['level'])
                elif elem_type == 'paragraph':
                    text = elem['text']
                    if text:
                        self._add_paragraph(doc, text)
                elif elem_type == 'list':
                    items = elem.get('items', [])
                    if items:
                        self._add_list(doc, items, elem.get('ordered', False))
                elif elem_type == 'table':
                    headers = elem.get('headers', [])
                    rows = elem.get('rows', [])
                    if headers and rows:
                        self._add_table(doc, headers, rows)

            # 保存文件
            filename = f"docx_{plan_id}.docx"
            filepath = self.upload_dir / filename
            doc.save(str(filepath))

            logger.info("[docx_export] 导出成功: %s", filepath)
            return str(filepath)

        except Exception as e:
            logger.error("[docx_export] 导出失败: %s", str(e))
            raise

    def html_to_docx_sync(self, html_content: str, title: str, plan_id: str) -> str:
        """同步版本的导出方法"""
        return self.html_to_docx(html_content, title, plan_id)


# 全局实例
docx_export_service = DocxExportService()
