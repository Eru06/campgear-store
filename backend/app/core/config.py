from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database — must be set via .env or environment variable
    database_url: str

    # JWT — must be set via .env or environment variable (no default = fail-safe)
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Keycloak OIDC
    keycloak_client_id: str = "ecommerce-backend"
    keycloak_client_secret: str = ""
    keycloak_auth_url: str = ""
    keycloak_token_url: str = ""
    keycloak_userinfo_url: str = ""
    keycloak_redirect_uri: str = "https://shop.matcsecdesignd.com/api/v1/auth/sso/callback"
    keycloak_verify_ssl: bool = False

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    upload_dir: str = "/data/uploads"
    frontend_url: str = "https://shop.matcsecdesignd.com"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
