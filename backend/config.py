from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_api_key: str
    anthropic_api_key: str
    dashboard_user: str = "admin"
    dashboard_password: str = "changeme"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8"}


settings = Settings()
