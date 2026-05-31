from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = "Lazunex"
    app_version: str = "0.1.0"
    debug: bool = False
    database_url: str = Field(
        default="mysql+asyncmy://app_user:app_password@localhost:3306/app_db?charset=utf8mb4"
    )


settings = Settings()
