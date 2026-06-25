from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "social-backend"
    database_url: str = "postgresql+psycopg2://mydata:mydata@localhost:5433/social_db"
    cors_origins: str = "http://localhost:3020"
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "mydata"
    subscriptions_api_url: str = "http://localhost:8002"
    poker_world_api_url: str = "http://localhost:8030"
    platform_internal_token: str = "mydata-internal-dev-token"
    nats_url: str = ""

    @property
    def jwks_url(self) -> str:
        return (
            f"{self.keycloak_url}/realms/{self.keycloak_realm}"
            "/protocol/openid-connect/certs"
        )

    @property
    def issuer(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}"

    class Config:
        env_file = ".env"


settings = Settings()
