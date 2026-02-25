"""Configurações da aplicação."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Configurações centralizadas da aplicação."""
    
    # Informações da API
    APP_NAME: str = "API Sistema Escolar"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "Interface completa para gestão de alunos, notas e autenticação. Desenvolvido para automação escolar com segurança e escalabilidade."
    
    # Ambiente
    ENVIRONMENT: str = Field(default="development", validation_alias="ENVIRONMENT")
    DEBUG: bool = Field(default=True, validation_alias="DEBUG")
    
    # Segurança
    SECRET_KEY: str = Field(..., validation_alias="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", validation_alias="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Database
    MONGO_URI: str = Field(..., validation_alias="MONGO_URI")
    MONGO_DB_NAME: str = Field(default="escola", validation_alias="MONGO_DB_NAME")
    
    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        validation_alias="CORS_ORIGINS"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(default="logs/app.log", validation_alias="LOG_FILE")
    
    # Paginação
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Valida se a SECRET_KEY tem tamanho adequado."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY deve ter no mínimo 32 caracteres para segurança adequada")
        return v
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS de string para lista."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        """Configuração do Pydantic Settings."""
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Instância global de configurações
settings = Settings()
