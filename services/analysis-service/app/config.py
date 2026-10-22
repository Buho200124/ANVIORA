from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración del analysis-service. No usa base de datos: solo procesa texto."""

    INTERNAL_API_KEY: str = "clave-interna-solo-desarrollo"
    PRECARGAR_MODELO: bool = True
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
