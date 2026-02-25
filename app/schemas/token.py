"""Schemas para autenticação e tokens."""
from pydantic import BaseModel, Field


class Token(BaseModel):
    """
    Schema de resposta para token de autenticação.
    
    Attributes:
        access_token: Token JWT de acesso
        token_type: Tipo do token (sempre "bearer")
    """
    
    access_token: str = Field(
        ...,
        description="Token JWT para autenticação nas rotas protegidas",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(
        default="bearer",
        description="Tipo do token de autenticação",
        examples=["bearer"]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTcwODQ1MjAwMH0...",
                    "token_type": "bearer"
                }
            ]
        }
    }


class TokenPayload(BaseModel):
    """
    Schema do payload do token JWT.
    
    Attributes:
        sub: Subject (username do usuário)
        exp: Data de expiração (timestamp)
    """
    
    sub: str = Field(..., description="Username do usuário autenticado")
    exp: int = Field(..., description="Timestamp de expiração do token")
