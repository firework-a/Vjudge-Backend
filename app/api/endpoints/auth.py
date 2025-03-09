# app/api/endpoints/auth
import logging

from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from jwt import ExpiredSignatureError
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_current_user, generate_unique_uid
from app.core.config import settings
from app.core.security import verify_password, create_access_token, get_password_hash, add_token_to_blacklist
from app.models import User
from app.schemas import UserResponse, UserCreate, Token

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(request: Request, user_data: UserCreate):
    try:
        # 检查用户是否已存在
        if await User.get_or_none(email=user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

        # 创建新用户
        user = await User.create(
            email=user_data.email,
            uid=await generate_unique_uid(),
            password_hash=get_password_hash(user_data.password),
            nick_name=user_data.nick_name,
            phone=user_data.phone
        )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        return {
            "code": status.HTTP_201_CREATED,
            "msg": "注册成功",
            "data": Token(access_token=access_token)
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册时发生错误，请稍后重试"
        )


@router.post("/login", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(request: Request, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    try:
        user = await User.get_or_none(email=form_data.username)
        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        return Token(access_token=access_token)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"登录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录时发生错误，请稍后重试"
        )


@router.get("/me")
@limiter.limit(settings.RATE_LIMIT_GENERAL)
async def get_current_user_info(
        request: Request,
        current_user: Annotated[User, Depends(get_current_user)]
):
    try:
        return {
            "code": status.HTTP_200_OK,
            "msg": "成功获取用户信息",
            "data": UserResponse(
                uid=current_user.uid,
                email=current_user.email,
                nick_name=current_user.nick_name,
                phone=current_user.phone,
                gender=current_user.gender,
                avatar=current_user.avatar,
                is_admin=current_user.is_admin,
                created_at=current_user.created_at
            )
        }
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败，请稍后重试"
        )


@router.post("/logout", dependencies=[Depends(get_current_user)])
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def logout(request: Request):
    try:
        # 从Authorization头获取token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("无效的认证头格式")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证头",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split(" ")[1]

        try:
            # 验证token是否有效
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

            # 获取token剩余过期时间
            exp = payload.get("exp")
            if exp:
                exp_time = datetime.fromtimestamp(exp, timezone.utc)
                remaining_time = exp_time - datetime.now(timezone.utc)
                if remaining_time.total_seconds() > 0:
                    # 将token加入黑名单
                    await add_token_to_blacklist(token, remaining_time)
                    logger.info(f"Token成功加入黑名单，剩余有效期: {remaining_time.total_seconds()}秒")

            return {"message": "已成功注销"}

        except ExpiredSignatureError:
            logger.warning("Token已过期")
            return {"message": "Token已过期，无需注销"}
        except JWTError as e:
            logger.warning(f"无效的Token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"注销失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注销时发生错误，请稍后重试"
        )
