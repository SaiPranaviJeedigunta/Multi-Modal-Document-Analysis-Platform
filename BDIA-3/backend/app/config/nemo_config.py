from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class NeMoConfig(BaseSettings):
    # Model settings
    NEMO_MODEL_PATH: str = os.getenv("NEMO_MODEL_PATH", "nvidia/nemo-multimodal-large")
    NEMO_CACHE_DIR: str = os.getenv("NEMO_CACHE_DIR", "./cache")
    MAX_INPUT_LENGTH: int = int(os.getenv("NEMO_MAX_INPUT_LENGTH", "1024"))
    MAX_OUTPUT_LENGTH: int = int(os.getenv("NEMO_MAX_OUTPUT_LENGTH", "512"))
    BATCH_SIZE: int = int(os.getenv("NEMO_BATCH_SIZE", "1"))
    TEMPERATURE: float = float(os.getenv("NEMO_TEMPERATURE", "0.7"))
    TOP_K: int = int(os.getenv("NEMO_TOP_K", "50"))
    TOP_P: float = float(os.getenv("NEMO_TOP_P", "0.9"))
    USE_GPU: bool = os.getenv("NEMO_USE_GPU", "false").lower() == "true"

    class Config:
        env_prefix = "NEMO_"
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

@lru_cache()
def get_nemo_config() -> NeMoConfig:
    return NeMoConfig()

nemo_config = get_nemo_config()

__all__ = ["NeMoConfig", "nemo_config"]