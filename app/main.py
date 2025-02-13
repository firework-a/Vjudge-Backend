from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from app.core.config import settings
from app.api.api import api_router
import redis.asyncio as redis
from contextlib import asynccontextmanager
from app.core.log_config import setup_logger

# 配置日志
logger = setup_logger()

# Redis connection
redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    try:
        await redis_client.ping()
        logger.info("Redis connection established successfully.")
        yield
    except Exception as exp:
        logger.error(f"Failed to establish Redis connection: {exp}")
    finally:
        # Shutdown
        try:
            await redis_client.close()
            logger.info("Redis connection closed.")
        except Exception as exp:
            logger.error(f"Failed to close Redis connection: {exp}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Virtual Judge Platform",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/ping")
def health_check():
    """Health check."""
    logger.info("Health check request received.")
    return {"message": "Hello I am working!"}


# 请求日志中间件
@app.middleware("http")
async def request_log_middleware(request: Request, call_next):
    try:
        # 获取请求信息
        client_ip = request.client.host
        client_port = request.client.port
        method = request.method
        path = request.url.path
        http_version = request.scope.get("http_version", "HTTP/1.1")
        auth_header = request.headers.get("Authorization", "(No Token)")
        token = auth_header.split(" ")[-1] if auth_header != "(No Token)" else "(No Token)"

        # 获取当前时间戳
        current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        # 获取查询参数
        query_params = request.query_params
        query_string = f"?{query_params}" if query_params else ""

        # 获取请求体（如果存在）
        request_body = await request.body()
        body = request_body.decode("utf-8") if request_body else "(No Body)"

        # 调用下一个中间件或处理函数
        response = await call_next(request)

        # 获取响应状态码
        status_code = response.status_code

        # 构造日志消息
        log_message = (
            f"{current_time} - {client_ip}:{client_port} - "
            f"\"{method} {path}{query_string} HTTP/{http_version}\" {status_code} - Bearer {token} - Body: {body}"
        )

        # 记录日志
        logger.info(log_message)

        return response
    except Exception as exp:
        logger.error(f"Error processing request: {exp}")
        raise


# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],  # 测试环境放开所有来源，生产环境需要指定源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
try:
    register_tortoise(
        app,
        db_url=settings.DB_URL,
        modules={"models": ["app.models"]},
        generate_schemas=False,  # 禁用schemas生成，因为表已存在
        add_exception_handlers=True,
    )
    logger.info("Database configuration completed successfully.")
except Exception as e:
    logger.error(f"Failed to configure database: {e}")

# Include API router
app.include_router(api_router, prefix=settings.BASE_PREFIX)