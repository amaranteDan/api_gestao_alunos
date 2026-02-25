"""Dependências (Dependency Injection) para as rotas."""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import decode_access_token
from app.db.mongodb import get_database
from app.core.logger import logger


# Esquema OAuth2 para autenticação
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    """
    Dependency para obter o usuário atual a partir do token JWT.
    
    Args:
        token: Token JWT do header Authorization
        
    Returns:
        str: Username do usuário autenticado
        
    Raises:
        HTTPException: Se o token for inválido ou não contém 'sub'
    """
    payload = decode_access_token(token)
    username: str = payload.get("sub")
    
    if username is None:
        logger.warning("Token sem campo 'sub'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: campo 'sub' ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Usuário autenticado: {username}")
    return username


# Type aliases para dependency injection
CurrentUser = Annotated[str, Depends(get_current_user)]
Database = Annotated[AsyncIOMotorDatabase, Depends(get_database)]
