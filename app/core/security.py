# app/core/security
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
import logging
from fastapi import HTTPException
import asyncio

from app.api.utils import get_redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def add_token_to_blacklist(token: str, expires_delta: timedelta) -> None:
    """Add a token to the blacklist in Redis"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            client = await get_redis_client()
            await client.setex(f"blacklist_token:{token}", int(expires_delta.total_seconds()), "1")
            logger.info(f"Token成功加入黑名单，剩余有效期: {expires_delta.total_seconds()}秒")
            return
        except ConnectionError as e:
            logger.warning(f"Redis连接失败，尝试重试 ({attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"Redis连接失败，已达到最大重试次数")
                raise HTTPException(
                    status_code=503,
                    detail="暂时无法处理注销请求，请稍后重试"
                )
        except Exception as e:
            logger.error(f"将token添加到黑名单时发生错误: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="注销时发生错误，请稍后重试"
            )

async def is_token_blacklisted(token: str) -> bool:
    """Check if a token is in the blacklist"""
    try:
        client = await get_redis_client()
        exists = await client.exists(f"blacklist_token:{token}") 
        return bool(exists)
    except Exception as e:
        # 记录错误但不中断程序
        logger.error(f"检查 token 黑名单时发生错误: {e}")
        return False
