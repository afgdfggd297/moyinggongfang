"""Seed script to populate default system templates.

Run this module directly or import and call ``seed_default_templates()``
to insert 5 built-in system templates into the database.
"""
import asyncio
import json
import logging

from sqlalchemy import select

from app.db.database import async_session_factory
from app.db.models import Template

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATES = [
    {
        "name": "商务汇报",
        "description": "适用于企业季度汇报、年度总结等正式商务场景。简洁大方的布局，突显数据与关键成果。",
        "category": "business",
        "style": "business",
        "color_scheme": "blue",
        "is_system": True,
        "outline_template": json.dumps({
            "slides": [
                {"title": "封面", "layout": "title", "content": "公司季度汇报"},
                {"title": "目录", "layout": "toc", "content": "汇报大纲"},
                {"title": "业绩概览", "layout": "two_column", "content": "本季度核心指标"},
                {"title": "数据分析", "layout": "chart", "content": "关键数据对比"},
                {"title": "重点项目", "layout": "cards", "content": "项目进展与成果"},
                {"title": "团队表现", "layout": "two_column", "content": "团队绩效总结"},
                {"title": "下一步计划", "layout": "timeline", "content": "未来工作规划"},
                {"title": "谢谢", "layout": "ending", "content": "感谢聆听"},
            ]
        }, ensure_ascii=False),
    },
    {
        "name": "学术答辩",
        "description": "专为毕业论文答辩、学术会议演讲设计。清晰的逻辑结构，适合呈现研究成果与论证过程。",
        "category": "academic",
        "style": "academic",
        "color_scheme": "green",
        "is_system": True,
        "outline_template": json.dumps({
            "slides": [
                {"title": "封面", "layout": "title", "content": "论文题目与作者信息"},
                {"title": "研究背景", "layout": "content", "content": "研究问题与动机"},
                {"title": "文献综述", "layout": "two_column", "content": "相关研究梳理"},
                {"title": "研究方法", "layout": "diagram", "content": "研究设计与方法论"},
                {"title": "实验结果", "layout": "chart", "content": "数据与实验结果"},
                {"title": "讨论分析", "layout": "two_column", "content": "结果讨论与意义"},
                {"title": "结论", "layout": "content", "content": "主要发现与贡献"},
                {"title": "致谢", "layout": "ending", "content": "感谢导师与同学"},
            ]
        }, ensure_ascii=False),
    },
    {
        "name": "创意提案",
        "description": "面向广告、设计、品牌等创意行业。大胆的视觉风格，适合展示创意概念与灵感方案。",
        "category": "creative",
        "style": "creative",
        "color_scheme": "purple",
        "is_system": True,
        "outline_template": json.dumps({
            "slides": [
                {"title": "封面", "layout": "title", "content": "创意提案标题"},
                {"title": "品牌洞察", "layout": "full_image", "content": "市场与用户洞察"},
                {"title": "创意概念", "layout": "hero", "content": "核心创意阐述"},
                {"title": "视觉方案", "layout": "gallery", "content": "设计稿展示"},
                {"title": "执行计划", "layout": "timeline", "content": "项目推进时间线"},
                {"title": "预算概览", "layout": "table", "content": "费用明细"},
                {"title": "团队介绍", "layout": "cards", "content": "核心团队成员"},
                {"title": "谢谢", "layout": "ending", "content": "期待合作"},
            ]
        }, ensure_ascii=False),
    },
    {
        "name": "极简风格",
        "description": "以内容为核心的极简设计。大量留白、精炼文字，适合高效传达信息的各类场景。",
        "category": "general",
        "style": "minimal",
        "color_scheme": "gray",
        "is_system": True,
        "outline_template": json.dumps({
            "slides": [
                {"title": "封面", "layout": "title", "content": "演讲标题"},
                {"title": "核心观点", "layout": "single_point", "content": "一句话核心信息"},
                {"title": "背景", "layout": "content", "content": "问题背景"},
                {"title": "方案", "layout": "two_column", "content": "解决思路"},
                {"title": "关键数据", "layout": "numbers", "content": "三组核心数据"},
                {"title": "行动建议", "layout": "content", "content": "下一步行动"},
                {"title": "结尾", "layout": "ending", "content": "谢谢"},
            ]
        }, ensure_ascii=False),
    },
    {
        "name": "科技发布",
        "description": "适用于产品发布会、技术分享、Demo Day 等科技主题。现代感强，突出技术创新与产品亮点。",
        "category": "tech",
        "style": "tech",
        "color_scheme": "dark",
        "is_system": True,
        "outline_template": json.dumps({
            "slides": [
                {"title": "开场", "layout": "title", "content": "产品/技术名称"},
                {"title": "痛点", "layout": "problem", "content": "行业痛点分析"},
                {"title": "我们的方案", "layout": "hero", "content": "技术方案概述"},
                {"title": "核心功能", "layout": "feature_grid", "content": "产品功能亮点"},
                {"title": "技术架构", "layout": "diagram", "content": "系统架构图"},
                {"title": "Demo", "layout": "full_image", "content": "产品演示"},
                {"title": "性能数据", "layout": "chart", "content": "Benchmark 对比"},
                {"title": "路线图", "layout": "timeline", "content": "未来规划"},
                {"title": "谢谢", "layout": "ending", "content": "Thank You"},
            ]
        }, ensure_ascii=False),
    },
]


async def seed_default_templates() -> None:
    """Insert default system templates if they don't already exist."""
    async with async_session_factory() as session:
        try:
            # Check if system templates already exist
            result = await session.execute(
                select(Template).where(Template.is_system == True).limit(1)
            )
            if result.scalar_one_or_none() is not None:
                logger.info("[seed] System templates already exist, skipping seed.")
                return

            for tpl_data in DEFAULT_TEMPLATES:
                template = Template(**tpl_data)
                session.add(template)

            await session.commit()
            logger.info("[seed] Created %d default system templates.", len(DEFAULT_TEMPLATES))

        except Exception:
            await session.rollback()
            logger.error("[seed] Failed to seed templates.", exc_info=True)
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_default_templates())
