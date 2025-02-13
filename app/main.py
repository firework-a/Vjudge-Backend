from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from app.core.config import settings
from app.api.api import api_router
import redis.asyncio as redis
import logging
from contextlib import asynccontextmanager

# Configure logging to suppress specific warnings
logging.getLogger("aiomysql.cursors").setLevel(logging.ERROR)

# Redis connection
redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await redis_client.ping()
        yield
    finally:
        # Shutdown
        await redis_client.close()

app = FastAPI(
    title="VJudge Backend",
    description="Backend API for Virtual Judge Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 测试环境放开所有来源，生产环境需要指定源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
register_tortoise(
    app,
    db_url=settings.DB_URL,
    modules={"models": ["app.models"]},
    generate_schemas=False,  # 禁用schemas生成，因为表已存在
    add_exception_handlers=True,
)

# Include API router
app.include_router(api_router, prefix="/api")
