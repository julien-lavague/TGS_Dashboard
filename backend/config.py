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
    # Dashboard tab: GCP workloads (Cloud Run, Cloud Scheduler) health.
    gcp_project: str = "thegoodspots"
    gcp_region: str = "europe-west4"
    # Service-account key (raw JSON or base64) with read-only access; required
    # on Railway. Empty locally -> ADC, then the logged-in gcloud CLI.
    gcp_service_account_json: str = ""

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8"}


settings = Settings()
