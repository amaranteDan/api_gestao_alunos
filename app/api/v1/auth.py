"""Router de autenticação."""
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.token import Token
from app.core.security import create_access_token, verify_password
from app.core.config import settings
from app.core.exceptions import InvalidCredentialsException
from app.core.logger import logger
from app.api.deps import Database, get_current_user, CurrentUser

router = APIRouter(prefix="/auth", tags=["Autenticação"])


async def autenticar_usuario(db, username: str, password: str) -> dict:
    """
    Autentica um usuário buscando no MongoDB e verificando a senha com bcrypt.
    """
    usuario = await db.usuarios.find_one({"username": username})

    if not usuario:
        logger.warning(f"Tentativa de login com usuário inexistente: {username}")
        raise InvalidCredentialsException()

    if not usuario.get("is_active", True):
        logger.warning(f"Tentativa de login de usuário inativo: {username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo. Aguarde aprovação do administrador."
        )

    if not verify_password(password, usuario["hashed_password"]):
        logger.warning(f"Tentativa de login com senha incorreta: {username}")
        raise InvalidCredentialsException()

    logger.info(f"Login bem-sucedido: {username}")
    return usuario


@router.post(
    "/token",
    response_model=Token,
    summary="Obter Token de Acesso",
    description=f"""
    Endpoint para autenticação e obtenção de token JWT.

    ### Processo:
    1. Envie username e password via form-data
    2. Se as credenciais forem válidas, receba um token JWT
    3. Use o token no header `Authorization: Bearer {{token}}` para acessar rotas protegidas

    ### Segurança:
    - Token expira em {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutos (configurável)
    - Token é assinado com algoritmo {settings.ALGORITHM}
    - Senhas armazenadas com hash bcrypt
    """,
    responses={
        200: {
            "description": "Autenticação bem-sucedida",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {"description": "Credenciais inválidas", "content": {"application/json": {"example": {"detail": "Usuário ou senha incorretos"}}}},
        403: {"description": "Usuário inativo", "content": {"application/json": {"example": {"detail": "Usuário inativo. Aguarde aprovação do administrador."}}}},
        422: {"description": "Erro de validação dos dados"}
    }
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Database
):
    logger.info(f"Tentativa de login: {form_data.username}")

    usuario = await autenticar_usuario(db, form_data.username, form_data.password)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario["username"], "role": usuario.get("role", "user")},
        expires_delta=access_token_expires
    )

    logger.info(f"Token gerado com sucesso para: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/me",
    summary="Obter Usuário Atual",
    description="""
    Retorna informações do usuário atualmente autenticado.

    ### Autenticação Requerida:
    - Inclua o token JWT no header: `Authorization: Bearer {{token}}`
    """,
    responses={
        200: {
            "description": "Informações do usuário autenticado",
            "content": {
                "application/json": {
                    "example": {
                        "username": "admin",
                        "full_name": "Administrador do Sistema",
                        "role": "admin",
                        "email": "admin@escola.com"
                    }
                }
            }
        },
        401: {"description": "Token inválido ou ausente"}
    }
)
# ✅ Correto
async def get_current_user_info(
    current_user: CurrentUser,  # já retorna o username (string)
    db: Database
):
    usuario = await db.usuarios.find_one({"username": current_user})

    if not usuario:
        raise InvalidCredentialsException()

    return {
        "username": usuario["username"],
        "full_name": usuario.get("full_name", "Usuário"),
        "email": usuario.get("email", ""),
        "role": usuario.get("role", "user"),
        "is_active": usuario.get("is_active", True)
    }