from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_api_key: str
    # Only used by the (now-unused) AI topic-analysis feature. Defaulted so a
    # missing key doesn't crash startup; set a real key to re-enable that route.
    anthropic_api_key: str = "unused"
    dashboard_user: str = "admin"
    dashboard_password: str = "changeme"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8"}


settings = Settings()
