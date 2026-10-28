from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./supply_chain.db"
    api_base_url: str = "http://localhost:8000"
    safety_stock_days: int = 7
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
