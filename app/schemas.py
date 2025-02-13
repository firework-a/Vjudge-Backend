from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    nick_name: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    nick_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class UserPasswordUpdate(BaseModel):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserResponse(UserBase):
    userId: int
    solved: int
    isAdmin: bool
    avatar: str

    class Config:
        from_attributes = True

class NoticeResponse(BaseModel):
    id: int
    title: str
    content: str
    time: datetime

    class Config:
        from_attributes = True

class SourceResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class TagResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    title: str
    difficulty: int
    source: str
    tags: List[str]

class QuestionResponse(QuestionBase):
    id: int

    class Config:
        from_attributes = True

class QuestionsResponse(BaseModel):
    questions: List[QuestionResponse]
    total: int
