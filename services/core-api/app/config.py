from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración del core-api, leída desde variables de entorno."""

    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "*"

    # Comunicación con los otros microservicios
    ANALYSIS_SERVICE_URL: str = "http://analysis-service:8002"
    RECOMMENDATION_SERVICE_URL: str = "http://recommendation-service:8003"
    INTERNAL_API_KEY: str = "clave-interna-solo-desarrollo"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
