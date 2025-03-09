# app/main
from contextlib import asynccontextmanager

import fastapi_cdn_host
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse
from tortoise import Tortoise

from app.api.api import api_router
from app.api.utils import construct_log_message, get_redis_client, close_redis_client
from app.core.config import settings
from app.core.log_config import setup_logger
from app.core.tortoise_orm_config import TORTOISE_ORM  # 导入 TORTOISE_ORM 配置

# 配置日志
logger = setup_logger()

# 配置速率限制器
limiter = Limiter(key_func=get_remote_address)

# FastAPI 应用的生命周期管理
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 初始化 Tortoise-ORM
    try:
        await Tortoise.init(config=TORTOISE_ORM)  # 使用导入的配置
        await Tortoise.generate_schemas()
        logger.info("Tortoise ORM 已成功初始化")
    except Exception as e:
        logger.error(f"Tortoise ORM 初始化失败: {e}")
        # 不要在这里停止，继续尝试其他初始化

    # Redis 连接
    try:
        await get_redis_client()
        logger.info("Redis连接已成功建立")
    except Exception as exp:
        logger.error(f"建立Redis连接失败: {exp}")
        # 不要在这里停止，继续运行

    yield

    # 关闭所有连接
    try:
        await Tortoise.close_connections()
        logger.info("Tortoise ORM 已关闭")
    except Exception as e:
        logger.error(f"Tortoise ORM 关闭失败: {e}")

    try:
        await close_redis_client()
        logger.info("Redis连接已关闭")
    except Exception as exp:
        logger.error(f"关闭Redis连接失败: {exp}")

# 初始化 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Virtual Judge Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# 使用 fastapi_cdn_host 优化文档
fastapi_cdn_host.patch_docs(app)

# 注册速率限制异常处理器
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    retry_after = exc.headers.get("Retry-After", "未知")
    return JSONResponse(
        status_code=429,
        content={"detail": "请求过于频繁，请稍后再试", "retry_after": retry_after},
        headers={"Retry-After": retry_after},
    )

# 请求日志中间件
@app.middleware("http")
async def request_log_middleware(request: Request, call_next):
    try:
        request_body = await request.body()
        body = request_body.decode("utf-8") if request_body else "(No Body)"
        response = await call_next(request)
        log_message = construct_log_message(request, response, body)
        logger.info(log_message)
        return response
    except Exception as exp:
        logger.error(f"处理请求时出错: {exp}")
        raise

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,# type:ignore
    allow_origins=["*"],  # 测试环境放开所有来源，生产环境需要指定源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 示例路由：健康检查
@app.get("/ping")
@limiter.limit(settings.RATE_LIMIT_GENERAL)
async def health_check(request: Request):
    """存活检查"""
    return {"message": "服务运行正常!"}

# 包含 API 路由
app.include_router(api_router, prefix=settings.BASE_PREFIX)