from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "vetty-assignment-api"
    app_version: str = "1.0.0"
    app_description: str = "Vetty Assignment API"
    app_author: str = "Ibrahim Khan"
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    cache_ttl_seconds: int = 60
    api_key: str = "something"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()