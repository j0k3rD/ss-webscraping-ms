from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str
    JWT_ALGORITHM: str
    SS_WEB_PORT: int
    ACCESS_TOKEN_EXPIRY: int
    REFRESH_TOKEN_EXPIRY: int
    INTERNAL_API_KEY: str
    SERVICE_TO_SERVICE_SECRET: str
    BROWSER: str
    KEY_ANTICAPTCHA: str
    BACKEND_URL: str
    ENDPOINT_PROXY: str
    REDIS_URL: str
    PROCESSOR_ID: str
    GOOGLE_APPLICATION_CREDENTIALS: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


Config = Settings()


broker_url = Config.REDIS_URL
result_backend = Config.REDIS_URL
broker_connection_retry_on_startup = True
