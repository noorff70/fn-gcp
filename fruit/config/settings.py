from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    ENVIRONMENT: str = "dev"

    model_config = SettingsConfigDict(
        env_file=".env.dev",
        extra="ignore"
    )

settings = Settings()