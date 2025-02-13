from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from typing import Annotated
from app.core.security import verify_password, create_access_token, get_password_hash, add_token_to_blacklist
from app.core.config import settings
from app.models import User
from app.schemas import UserResponse, UserCreate, Token
from app.api.deps import get_current_user
from jose import jwt

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    # Check if user already exists
    if await User.get_or_none(email=user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = await User.create(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        nick_name=user_data.nick_name,
        phone=user_data.phone,
        is_admin=False,
        solved=0
    )
    
    return {
        "userId": user.id,
        "nickName": user.nick_name,
        "email": user.email,
        "phone": user.phone,
        "solved": user.solved,
        "isAdmin": user.is_admin,
        "avatar": user.avatar
    }

@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await User.get_or_none(email=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Annotated[User, Depends(get_current_user)]):
    return {
        "userId": current_user.id,
        "nickName": current_user.nick_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "solved": current_user.solved,
        "isAdmin": current_user.is_admin,
        "avatar": current_user.avatar
    }

@router.post("/logout")
async def logout(request: Request, current_user: Annotated[User, Depends(get_current_user)]):
    # Get the token from the Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Get token expiration time
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")
        if exp:
            # Calculate remaining time until expiration
            exp_time = datetime.fromtimestamp(exp)
            remaining_time = exp_time - datetime.now(datetime.timezone.utc)
            if remaining_time.total_seconds() > 0:
                # Add token to blacklist with the remaining time
                add_token_to_blacklist(token, remaining_time)
    except Exception:
        pass  # If token is invalid, no need to blacklist it
    
    return {"message": "Successfully logged out"}
