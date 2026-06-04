"""
Application configuration loaded from environment variables / .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    db_host:              str      = "localhost"
    db_port:              int      = 5432
    db_name:              str      = "pywarehouse"
    db_user:              str      = "pywarehouse_user"
    db_password:          str      = "changeme"
    database_url_override: str | None = None

    # App
    debug:       bool = False
    app_title:   str  = "PyWarehouse API"
    app_version: str  = "0.1.0"

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()