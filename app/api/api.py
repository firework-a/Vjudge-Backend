from fastapi import APIRouter
from app.api.endpoints import auth, users, notices, sources, tags, questions

api_router = APIRouter()

# Auth routes
api_router.include_router(auth.router, tags=["auth"])

# User routes
api_router.include_router(users.router, prefix="/user", tags=["users"])

# Notice routes
api_router.include_router(notices.router, prefix="/notices", tags=["notices"])

# Source routes
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])

# Tag routes
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])

# Question routes
api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
