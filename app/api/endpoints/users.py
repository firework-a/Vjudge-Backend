from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.security import get_password_hash
from app.models import User
from app.schemas import UserUpdate, UserPasswordUpdate

router = APIRouter()

@router.post("/{id}/reset")
async def reset_info(
    id: int,
    user_update: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.id != id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = await User.get_or_none(id=id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if email is already taken by another user
    if user_update.email and user_update.email != user.email:
        existing_user = await User.get_or_none(email=user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update only provided fields
    if user_update.email:
        user.email = user_update.email
    if user_update.nick_name:
        user.nick_name = user_update.nick_name
    if user_update.phone:
        user.phone = user_update.phone
        
    await user.save()
    return {}

@router.post("/{id}/pass")
async def reset_password(
    id: int,
    password_update: UserPasswordUpdate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.id != id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    user = await User.get_or_none(id=id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到用户"
        )
    
    user.password_hash = get_password_hash(password_update.password)
    await user.save()
    return {}
