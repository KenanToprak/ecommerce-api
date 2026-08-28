from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "E-Commerce API"
    PROJECT_VERSION: str = "1.0.0"
    
    # PostgreSQL connection string
    # We are setting a default value for now. In production, this should be read from a .env file.
    DATABASE_URL: str = "postgresql://postgres:Postgrekenan@localhost:5432/ecommerce_db"
    
    # JWT Settings
    SECRET_KEY: str = "super_secret_key_change_this_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
