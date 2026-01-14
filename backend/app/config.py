from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret: str = Field(alias="JWT_SECRET")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    admin_email: str = Field(default="admin@example.com", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="Admin123!", alias="ADMIN_PASSWORD")

    class Config:
        case_sensitive = False

settings = Settings()
