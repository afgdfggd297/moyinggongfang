"""PPT 生成器后端入口"""
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import register_exception_handlers
from app.api.v1.ppt import router as ppt_router
from app.api.v1.docx import router as docx_router
from app.api.v1.templates import router as templates_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.auth import router as auth_router

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    setup_logging()
    logger.info("应用启动中... version=%s", settings.APP_VERSION)

    # 初始化数据库表
    from app.db.database import init_db
    await init_db()
    logger.info("PostgreSQL 数据库表初始化完成")

    # 初始化 Redis 存储
    from app.services.redis_store import plan_store
    plan_store.init()

    # 初始化系统模板
    from app.db.seed_templates import seed_default_templates
    await seed_default_templates()

    # 初始化 LLM 服务
    from app.services.llm_service import llm_service
    await llm_service.initialize()

    logger.info("应用启动完成")
    yield
    logger.info("应用关闭中...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# 注册统一异常处理
register_exception_handlers(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
import os
static_dir = settings.STATIC_DIR
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 路由注册
app.include_router(auth_router, prefix="/api/v1")
app.include_router(ppt_router, prefix="/api/v1")
app.include_router(docx_router, prefix="/api/v1")
app.include_router(templates_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health")
async def health():
    return {"status": "ok"}
