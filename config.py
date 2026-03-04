import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    GEMINI_KEY: str = os.getenv("GEMINI_API_KEY")
    GROQ_KEY: str = os.getenv("GROQ_API_KEY")
    BASE_MODEL: str = os.getenv("MODEL_PATH")
    ADAPTERS: str = os.getenv("ADAPTER_PATH")
    DEVICE: str = "cuda"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.2

settings = Settings()