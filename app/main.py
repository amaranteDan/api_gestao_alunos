"""
API Sistema Escolar - Aplicação Principal

Sistema completo de gestão de alunos com autenticação JWT,
validações robustas, logging estruturado e documentação completa.

Desenvolvido seguindo boas práticas REST e arquitetura em camadas.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import (
    AlunoNotFoundException,
    InvalidObjectIdException,
    DatabaseConnectionException,
    InvalidCredentialsException
)
from app.db.mongodb import MongoDB
from app.api.v1 import auth, alunos, usuarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    
    - Startup: Conecta ao banco de dados
    - Shutdown: Fecha conexões
    """
    # Startup
    logger.info("Iniciando aplicação...")
    logger.info(f"Ambiente: {settings.ENVIRONMENT}")
    logger.info(f"Debug: {settings.DEBUG}")
    
    try:
        await MongoDB.connect_db()
        logger.info("Aplicação iniciada com sucesso!")
    except Exception as e:
        logger.critical(f"Erro crítico ao iniciar aplicação: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Encerrando aplicação...")
    await MongoDB.close_db()
    logger.info("Aplicação encerrada!")


# Cria aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/documentacao",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,  # Oculta schemas no rodapé
        "syntaxHighlight.theme": "monokai",
        "filter": True,  # Adiciona busca
        "displayRequestDuration": True,  # Mostra tempo de resposta
        "persistAuthorization": True,  # Mantém token após refresh
    }
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers Globais
@app.exception_handler(AlunoNotFoundException)
async def aluno_not_found_handler(request: Request, exc: AlunoNotFoundException):
    """Handler para aluno não encontrado."""
    logger.warning(f"Aluno não encontrado: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(InvalidObjectIdException)
async def invalid_object_id_handler(request: Request, exc: InvalidObjectIdException):
    """Handler para ObjectId inválido."""
    logger.warning(f"ObjectId inválido: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(DatabaseConnectionException)
async def database_error_handler(request: Request, exc: DatabaseConnectionException):
    """Handler para erros de banco de dados."""
    logger.error(f"Erro de banco de dados: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(InvalidCredentialsException)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsException):
    """Handler para credenciais inválidas."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler para erros de validação Pydantic."""
    errors = exc.errors()
    logger.warning(f"Erro de validação: {errors}")
    
    # Formata erros de forma mais amigável
    formatted_errors = []
    for error in errors:
        formatted_errors.append({
            "campo": " -> ".join(str(loc) for loc in error["loc"]),
            "mensagem": error["msg"],
            "tipo": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Erro de validação dos dados fornecidos",
            "erros": formatted_errors
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler genérico para exceções não tratadas."""
    logger.error(f"Erro não tratado: {type(exc).__name__} - {str(exc)}", exc_info=True)
    
    # Em produção, não expor detalhes do erro
    if settings.ENVIRONMENT == "production":
        detail = "Erro interno do servidor. Contate o suporte."
    else:
        detail = f"Erro interno: {type(exc).__name__} - {str(exc)}"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail}
    )


# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para logging de todas as requisições.
    
    Registra método, path, IP e tempo de resposta.
    """
    logger.info(f"📥 {request.method} {request.url.path} - IP: {request.client.host}")
    
    response = await call_next(request)
    
    logger.info(
        f"📤 {request.method} {request.url.path} - "
        f"Status: {response.status_code}"
    )
    
    return response


# Rotas da API
app.include_router(auth.router, prefix="/api/v1")
app.include_router(alunos.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")


# Rota raiz
@app.get(
    "/",
    tags=["Sistema"],
    summary="Informações da API",
    description="Retorna informações básicas sobre a API e links úteis."
)
async def root():
    """
    Endpoint raiz da API.
    
    Retorna informações sobre a API e links para documentação.
    """
    return {
        "nome": settings.APP_NAME,
        "versao": settings.APP_VERSION,
        "status": "online",
        "documentacao": "/documentacao",
        "ambiente": settings.ENVIRONMENT,
        "mensagem": "API funcionando corretamente! Acesse /documentacao para ver os endpoints disponíveis."
    }


# Health Check
@app.get(
    "/health",
    tags=["Sistema"],
    summary="Health Check",
    description="Verifica o status de saúde da aplicação e suas dependências."
)
async def health_check():
    """
    Endpoint de health check para monitoramento.
    
    Verifica:
    - Status da aplicação
    - Conexão com MongoDB
    """
    db_healthy = await MongoDB.health_check()
    
    if not db_healthy:
        logger.error("Health check falhou: banco de dados inacessível")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "mensagem": "Banco de dados inacessível"
            }
        )
    
    return {
        "status": "healthy",
        "database": "connected",
        "mensagem": "Todos os serviços operacionais"
    }


# Readiness Check (para Kubernetes)
@app.get(
    "/ready",
    tags=["Sistema"],
    summary="Readiness Check",
    description="Verifica se a aplicação está pronta para receber tráfego."
)
async def readiness_check():
    """
    Endpoint de readiness para orquestração (Kubernetes).
    """
    try:
        db_healthy = await MongoDB.health_check()
        
        if db_healthy:
            return {"status": "ready"}
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready"}
        )
    except Exception as e:
        logger.error(f"Readiness check falhou: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "error": str(e)}
        )


# Customização da documentação OpenAPI
def custom_openapi():
    """
    Customiza o schema OpenAPI.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        routes=app.routes,
    )
    
    # Adiciona informações de segurança
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    # Adiciona informações de contato
    openapi_schema["info"]["contact"] = {
        "name": "Equipe de Desenvolvimento",
        "email": "dev@escola.com"
    }
    
    # Adiciona licença
    openapi_schema["info"]["license"] = {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Iniciando servidor de desenvolvimento...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
