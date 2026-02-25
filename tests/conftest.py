"""Fixtures compartilhadas para testes."""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.core.config import settings
from app.db.mongodb import MongoDB


@pytest.fixture(scope="session")
def event_loop():
    """Cria um event loop para testes assíncronos."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """
    Cria uma conexão com banco de dados de teste.
    
    Usa um banco diferente para não interferir nos dados de desenvolvimento.
    """
    test_db_name = f"{settings.MONGO_DB_NAME}_test"
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[test_db_name]
    
    yield db
    
    # Cleanup: remove banco de teste após testes
    await client.drop_database(test_db_name)
    client.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP para testes de integração.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_token(client: AsyncClient) -> str:
    """
    Token de autenticação para testes.
    
    Faz login e retorna o token JWT.
    """
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "root_admin"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
async def auth_headers(auth_token: str) -> dict:
    """
    Headers com token de autenticação para testes.
    """
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def aluno_data() -> dict:
    """
    Dados de exemplo para criação de aluno.
    """
    return {
        "nome": "João Teste",
        "idade": 12,
        "gostaDe": ["futebol", "games"],
        "naEscola": True,
        "materias": {
            "português": 8.5,
            "matemática": 9.0,
            "história": 7.5
        }
    }
