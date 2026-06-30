from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    APP_NAME: str = "MeetingMinutesAPI"
    APP_ENV : str = "development"
    SECRET_KEY: str 
    DATABASE_URL: str 
    REDIS_URL: str =  "redis://localhost:6379/0"
    CELERY_BROKER_URL : str 
    CELERY_RESULT_BACKEND : str 
    SUMMARIZER_TYPE: str = "mock"
    ACCESS_TOKEN_EXPIRE_MINUTES : int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS : int = 7  # 7 days

    HF_API_TOKEN: str = ""  # optional, empty default

    model_config = SettingsConfigDict(env_file=".env", extra = "ignore")


settings = Settings() # type: ignore
