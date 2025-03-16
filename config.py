from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str
    API_V1_STR: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    DATABASE_URL: str
    MEDIA_ROOT: str
    OPENAI_API_KEY: str

    class Config:
        env_file = ".env"  # Load environment variables from .env file

settings = Settings()
