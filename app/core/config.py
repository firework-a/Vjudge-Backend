from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Vjudge Backend"

    # Baseprefix
    BASE_PREFIX: str = os.getenv("BASE_PREFIX","/api/v1")
    
    # Database
    DB_USERNAME: str = os.getenv("DB_USERNAME", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "root")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str = os.getenv("DB_NAME", "vjudge")
    DB_TEST_NAME: str = os.getenv("DB_TEST_NAME", "vjudge_test")
    DB_URL : str = f"mysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    TEST_DB_URL: str = f"mysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_TEST_NAME}"
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Server
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    class Config:
        env_file = ".env"

settings = Settings()
