"""DOCX 导出服务 - pypandoc (Markdown → DOCX)"""
from pathlib import Path
import pypandoc

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class DocxExportService:
    """Markdown → DOCX 导出服务（基于 pandoc）"""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        # pandoc 默认不支持中文段落缩进，用 reference-doc 可自定义样式
        self._reference_doc = None

    def markdown_to_docx(self, md_content: str, title: str, plan_id: str) -> str:
        """Markdown → DOCX（pandoc 一行搞定）"""
        try:
            filename = f"docx_{plan_id}.docx"
            filepath = self.upload_dir / filename

            # 在 Markdown 开头插入标题
            full_md = f"# {title}\n\n{md_content}"

            extra_args = [
                '--standalone',
                '--toc',                    # 自动生成目录
                '--toc-depth=3',
                '--metadata', f'title={title}',
            ]
            if self._reference_doc:
                extra_args += ['--reference-doc', str(self._reference_doc)]

            pypandoc.convert_text(
                full_md,
                'docx',
                format='md',
                outputfile=str(filepath),
                extra_args=extra_args,
            )

            logger.info("[docx_export] 导出成功: %s", filepath)
            return str(filepath)

        except Exception:
            logger.exception("[docx_export] 导出失败")
            raise

    def markdown_to_html(self, md_content: str) -> str:
        """Markdown → HTML（用于前端预览）"""
        return pypandoc.convert_text(md_content, 'html', format='md')

    def markdown_to_docx_sync(self, md_content: str, title: str, plan_id: str) -> str:
        """同步版本"""
        return self.markdown_to_docx(md_content, title, plan_id)


# 全局实例
docx_export_service = DocxExportService()
