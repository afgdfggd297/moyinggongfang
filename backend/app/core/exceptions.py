"""统一异常处理"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


# ═══ 业务异常 ═══

class AppError(Exception):
    """业务异常基类"""
    def __init__(self, message: str, code: str = "APP_ERROR"):
        self.message = message
        self.code = code


class NotFoundError(AppError):
    """资源不存在"""
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, code="NOT_FOUND")


class PlanNotFoundError(NotFoundError):
    """方案不存在"""
    def __init__(self):
        super().__init__("方案不存在")


class FileNotFoundError(NotFoundError):
    """文件不存在"""
    def __init__(self, message: str = "文件不存在"):
        super().__init__(message)


class BadRequestError(AppError):
    """请求参数错误"""
    def __init__(self, message: str = "请求参数错误"):
        super().__init__(message, code="BAD_REQUEST")


class EmptyContentError(BadRequestError):
    """内容为空"""
    def __init__(self):
        super().__init__("内容为空，生成可能未返回有效结果")


class SlideIndexError(BadRequestError):
    """幻灯片索引越界"""
    def __init__(self, max_index: int):
        super().__init__(f"slide_index 超出范围 (0-{max_index})")


class GenerateError(AppError):
    """生成失败"""
    def __init__(self, message: str = "生成失败"):
        super().__init__(message, code="GENERATE_ERROR")


class ExportError(AppError):
    """导出失败"""
    def __init__(self, message: str = "导出失败"):
        super().__init__(message, code="EXPORT_ERROR")


class AuthError(AppError):
    """认证失败"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, code="AUTH_ERROR")


class ConflictError(AppError):
    """资源冲突"""
    def __init__(self, message: str = "资源冲突"):
        super().__init__(message, code="CONFLICT")


class ForbiddenError(AppError):
    """禁止访问"""
    def __init__(self, message: str = "禁止访问"):
        super().__init__(message, code="FORBIDDEN")


# ═══ 注册异常处理器 ═══

def register_exception_handlers(app: FastAPI):
    """注册全局异常处理器"""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        status_map = {
            NotFoundError: 404,
            BadRequestError: 400,
            AuthError: 401,
            ConflictError: 409,
            ForbiddenError: 403,
        }
        status = 400
        for exc_cls, code in status_map.items():
            if isinstance(exc, exc_cls):
                status = code
                break
        if isinstance(exc, (GenerateError, ExportError)):
            status = 500

        logger.warning("[app_error] %s %s -> %s: %s", request.method, request.url.path, exc.code, exc.message)
        return JSONResponse(
            status_code=status,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("[unhandled] %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误", "code": "INTERNAL_ERROR"},
        )
