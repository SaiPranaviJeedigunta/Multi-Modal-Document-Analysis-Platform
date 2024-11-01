from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv
from typing import Optional

# Load the environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Research Document System"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "9vAnCuIEJS5XHcXoiaIIER1O1c730gTLx1P59wQCGPs")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    ALGORITHM: str = "HS256"
    
    # Snowflake
    SNOWFLAKE_USER: str = os.getenv("SNOWFLAKE_USER", "SAIPRANAVIJ")
    SNOWFLAKE_PASSWORD: str = os.getenv("SNOWFLAKE_PASSWORD", "Js@data1234")
    SNOWFLAKE_ACCOUNT: str = os.getenv("SNOWFLAKE_ACCOUNT", "il23236.us-east4.gcp")
    SNOWFLAKE_WAREHOUSE: str = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    SNOWFLAKE_DATABASE: str = os.getenv("SNOWFLAKE_DATABASE", "PUBLICATIONS_DB")
    SNOWFLAKE_SCHEMA: str = os.getenv("SNOWFLAKE_SCHEMA", "PUBLICATIONS_SCHEMA")
    
    # NVIDIA
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "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")
    
    # Storage
    VECTOR_STORE_PATH: str = "./data/vector_store"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Frontend/Backend URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8501")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

__all__ = ["Settings", "settings"]