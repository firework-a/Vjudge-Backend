# app/api/utils
from datetime import datetime
from typing import Optional
from starlette.requests import Request
from redis.asyncio.client import Redis
import logging

logger = logging.getLogger(__name__)

from app.core.config import settings


# 构造日志消息的辅助函数
def construct_log_message(request: Request, response, body: str) -> str:
    client_ip = request.client.host
    client_port = request.client.port
    method = request.method
    path = request.url.path
    http_version = request.scope.get("http_version", "HTTP/1.1")
    auth_header = request.headers.get("Authorization", "(No Token)")
    token = auth_header.split(" ")[-1] if auth_header != "(No Token)" else "(No Token)"
    query_params = request.query_params
    query_string = f"?{query_params}" if query_params else ""
    status_code = response.status_code
    current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    return (
        f"{current_time} - {client_ip}:{client_port} - "
        f"\"{method} {path}{query_string} HTTP/{http_version}\" {status_code} - Bearer {token} - Body: {body}"
    )

# Redis 客户端单例
_redis_client: Optional[Redis] = None

async def get_redis_client() -> Redis:
    """
    获取 Redis 客户端实例的异步函数。
    使用单例模式确保只创建一个连接。
    返回一个支持异步操作的 Redis 客户端实例。
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            encoding='utf-8',
            retry_on_timeout=True,
            socket_timeout=5,  # 连接超时
            socket_connect_timeout=5,  # 建立连接超时
            max_connections=20,  # 最大连接数
            health_check_interval=10,  # 健康检查间隔
            socket_keepalive=True  # 保持连接
        )
        # 验证连接是否成功
        try:
            await _redis_client.ping()
            logger.info("成功连接到Redis服务器")
        except ConnectionError as e:
            _redis_client = None
            logger.error(f"无法连接到Redis服务器: {e}")
            raise ConnectionError(f"无法连接到Redis服务器: {e}")
        except Exception as e:
            _redis_client = None
            logger.error(f"Redis连接时发生意外错误: {e}")
            raise ConnectionError(f"Redis连接时发生意外错误: {e}")
    return _redis_client

async def close_redis_client() -> None:
    """
    关闭 Redis 客户端连接的异步函数。
    确保在应用关闭时正确释放资源。
    """
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None