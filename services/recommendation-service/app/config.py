from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración del recommendation-service, leída desde variables de entorno."""

    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "*"
    INTERNAL_API_KEY: str = "clave-interna-solo-desarrollo"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
