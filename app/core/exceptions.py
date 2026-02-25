"""Exceções customizadas da aplicação."""
from fastapi import HTTPException, status


class AlunoNotFoundException(HTTPException):
    """Exceção lançada quando um aluno não é encontrado."""
    
    def __init__(self, aluno_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aluno com ID '{aluno_id}' não foi encontrado"
        )


class InvalidObjectIdException(HTTPException):
    """Exceção lançada quando um ObjectId é inválido."""
    
    def __init__(self, object_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID '{object_id}' não é um ObjectId válido"
        )


class AlunoDuplicadoException(HTTPException):
    """Exceção lançada quando tenta criar aluno duplicado."""
    
    def __init__(self, campo: str, valor: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um aluno com {campo} '{valor}'"
        )


class DatabaseConnectionException(HTTPException):
    """Exceção lançada quando há erro de conexão com o banco."""
    
    def __init__(self, detail: str = "Erro ao conectar com o banco de dados"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


class InvalidCredentialsException(HTTPException):
    """Exceção lançada quando as credenciais são inválidas."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )


class WeakPasswordException(HTTPException):
    """Exceção lançada quando a senha não atende aos requisitos."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Senha fraca. A senha deve ter no mínimo 8 caracteres, "
                "incluindo letras maiúsculas, minúsculas e números"
            )
        )
