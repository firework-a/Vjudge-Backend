# app/api/deps
import logging
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from nanoid.generate import generate
from redis.asyncio.client import Redis

from app.api.utils import get_redis_client
from app.core.config import settings
from app.core.security import is_token_blacklisted
from app.models import User

# Redis 中存储 UID 池的键名
UID_POOL_KEY = 'vj_uid_pool'
# UID 池的最大容量
UID_POOL_SIZE = 1000
# 补充 UID 池的阈值
UID_POOL_THRESHOLD = 100
# 最大重试次数
MAX_RETRIES = 3

# 配置日志
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def fill_uid_pool() -> None:
    """填充 UID 池，确保池中始终有足够的 UID"""
    client: Redis = await get_redis_client()
    current_size = await client.scard(UID_POOL_KEY) # type:ignore
    while current_size < UID_POOL_SIZE:
        # 仅使用数字 0 - 9 作为字符集，生成 10 位的短 UID
        alphabet = '0123456789'
        uid = generate(alphabet, 10)
        # 直接使用 get_or_none 检查用户是否存在
        if not await User.get_or_none(uid=uid): # type:ignore
            # 将生成的 UID 添加到 Redis 集合中
            await client.sadd(UID_POOL_KEY, uid) # type:ignore
            current_size += 1


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """获取当前用户信息"""
    try:
        # 检查 token 是否在黑名单中
        if await is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="登录已过期，请重新登录",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="登录已过期，请重新登录",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await User.get_or_none(email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="登录已过期，请重新登录",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except JWTError as jwt_err:
        logger.error(f"JWT error in get_current_user: {jwt_err}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """获取当前管理员用户信息"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前用户权限不足"
        )
    return current_user


async def get_uid_from_pool() -> Optional[str]:
    """从 Redis 池中获取一个 UID"""
    client: Redis = await get_redis_client()
    try:
        # 使用 spop 操作并处理返回值
        result = await client.spop(UID_POOL_KEY) # type:ignore

        if result is None:
            # 如果池为空，返回 None
            return None
        elif isinstance(result, str):
            # 如果返回值是字符串，直接返回
            return result
        else:
            # 其他情况（理论上不会发生），返回 None
            return None
    except Exception as e:
        logger.error(f"从 Redis 获取 UID 失败: {e}")
        return None


async def generate_unique_uid() -> Optional[str]:
    """生成唯一的用户 UID"""
    retries = 0
    while retries < MAX_RETRIES:
        try:
            client: Redis = await get_redis_client()
            # 检查池中的 UID 数量
            current_size = await client.scard(UID_POOL_KEY) # type:ignore
            if current_size < UID_POOL_THRESHOLD:
                await fill_uid_pool()
            
            # 尝试从池中获取 UID
            uid = await get_uid_from_pool()
            if uid:
                return uid

            # 如果获取失败，重新填充并重试
            await fill_uid_pool()
            retries += 1
            
        except Exception as e:
            logger.error(f"生成 UID 时发生错误: {e}")
            retries += 1
    
    # 如果重试次数用完仍然失败，生成一个新的 UID
    logger.warning("从 Redis 池获取 UID 失败，直接生成新 UID")
    while True:
        try:
            uid = generate('0123456789', 10)
            # 直接使用 get_or_none 检查用户是否存在
            if not await User.get_or_none(uid=uid): # type:ignore
                return uid
        except Exception as e:
            logger.error(f"生成新 UID 时发生错误: {e}")
            continue
