from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    database_url: str | None = None
    jwt_secret: str = "development-only-change-me"
    jwt_algorithm: str = "HS256"
    local_bridge_token: str | None = None
    model_provider: str | None = None
    model_name: str | None = None
    model_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_prefix="")


settings = Settings()
