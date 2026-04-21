from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database — used for local dev and docker-compose
    database_url: str = "postgresql+asyncpg://salon:salon@localhost:5432/salon_lyol"

    # Cloud SQL — set these in Cloud Run instead of database_url
    cloud_sql_instance: str = ""  # e.g. "project:region:instance"
    db_user: str = "salon"
    db_password: str = ""
    db_name: str = "salon_lyol"

    # Auth
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours — full working day

    # App
    environment: str = "development"
    debug: bool = False

    # CORS — comma-separated list of allowed origins
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
