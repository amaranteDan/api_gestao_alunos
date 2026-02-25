"""Router de gestão de alunos."""
from typing import Optional
from fastapi import APIRouter, Query, status

from app.schemas.aluno import (
    AlunoCreate,
    AlunoUpdate,
    AlunoResponse,
    AlunoListResponse,
    MessageResponse
)
from app.services.aluno_service import AlunoService
from app.api.deps import CurrentUser, Database
from app.core.config import settings
from app.core.logger import logger

router = APIRouter(prefix="/alunos", tags=["Gestão de Alunos"])


@router.post(
    "",
    response_model=AlunoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Novo Aluno",
    description="""
    Cria um novo registro de aluno no sistema escolar.
    
    ### Autenticação Requerida:
    - Token JWT válido no header: `Authorization: Bearer {token}`
    
    ### Validações Implementadas:
    - **Nome**: 2-100 caracteres, apenas letras e espaços, auto-capitalização
    - **Idade**: Entre 5 e 100 anos
    - **Hobbies (gostaDe)**: 1-10 itens, sem duplicatas, máximo 50 caracteres cada
    - **Matérias**: Notas entre 0 e 10
    
    ### Exemplo de Uso:
    ```json
    {
      "nome": "Maria Silva",
      "idade": 14,
      "gostaDe": ["leitura", "matemática", "vôlei"],
      "naEscola": true,
      "materias": {
        "português": 9.5,
        "matemática": 10.0,
        "história": 8.5
      }
    }
    ```
    
    ### Retorno:
    - **201 Created**: Aluno criado com sucesso (inclui ID gerado)
    - **400 Bad Request**: Dados inválidos (validação falhou)
    - **401 Unauthorized**: Token inválido ou ausente
    - **422 Unprocessable Entity**: Erro de validação dos campos
    - **503 Service Unavailable**: Erro de conexão com banco de dados
    """,
    responses={
        201: {
            "description": "Aluno criado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "id": "507f1f77bcf86cd799439011",
                        "nome": "Maria Silva",
                        "idade": 14,
                        "gostaDe": ["leitura", "matemática", "vôlei"],
                        "naEscola": True,
                        "materias": {
                            "português": 9.5,
                            "matemática": 10.0,
                            "história": 8.5
                        }
                    }
                }
            }
        },
        400: {
            "description": "Dados inválidos",
            "content": {
                "application/json": {
                    "example": {"detail": "Nome deve conter apenas letras e espaços"}
                }
            }
        },
        401: {
            "description": "Não autenticado",
            "content": {
                "application/json": {
                    "example": {"detail": "Token inválido"}
                }
            }
        }
    }
)
async def criar_aluno(
    aluno_data: AlunoCreate,
    db: Database,
    current_user: CurrentUser
):
    """
    Cria um novo aluno no sistema.
    
    Requer autenticação JWT válida.
    """
    logger.info(f"Usuário {current_user} criando novo aluno: {aluno_data.nome}")
    
    service = AlunoService(db)
    aluno_criado = await service.create_aluno(aluno_data)
    
    logger.info(f"Aluno criado com ID: {aluno_criado.id}")
    return aluno_criado


@router.get(
    "",
    response_model=AlunoListResponse,
    summary="Listar Todos os Alunos",
    description="""
    Retorna a lista de alunos cadastrados com suporte a paginação e filtros.
    
    ### Autenticação Requerida:
    - Token JWT válido no header: `Authorization: Bearer {token}`
    
    ### Funcionalidades:
    - **Paginação**: Use `skip` e `limit` para navegar pelos resultados
    - **Filtros opcionais**:
      - `nome`: Busca parcial case-insensitive (ex: "silva" encontra "João Silva")
      - `idade`: Busca por idade exata
      - `na_escola`: Filtra por status de matrícula (true/false)
    
    ### Parâmetros de Paginação:
    - **skip**: Número de registros a pular (default: 0)
    - **limit**: Máximo de registros por página (default: 10, máx: 100)
    
    ### Exemplos de Uso:
    - Listar primeiros 10: `GET /alunos`
    - Página 2 (registros 10-19): `GET /alunos?skip=10&limit=10`
    - Buscar por nome: `GET /alunos?nome=silva`
    - Alunos de 12 anos: `GET /alunos?idade=12`
    - Alunos matriculados: `GET /alunos?na_escola=true`
    - Combinar filtros: `GET /alunos?idade=12&na_escola=true&limit=5`
    
    ### Retorno:
    ```json
    {
      "total": 42,
      "skip": 0,
      "limit": 10,
      "alunos": [...]
    }
    ```
    """,
    responses={
        200: {
            "description": "Lista de alunos retornada com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "total": 42,
                        "skip": 0,
                        "limit": 10,
                        "alunos": [
                            {
                                "id": "507f1f77bcf86cd799439011",
                                "nome": "João Silva",
                                "idade": 12,
                                "gostaDe": ["futebol", "games"],
                                "naEscola": True,
                                "materias": {
                                    "português": 8.5,
                                    "matemática": 9.0,
                                    "história": 7.5
                                }
                            }
                        ]
                    }
                }
            }
        },
        401: {
            "description": "Não autenticado",
            "content": {
                "application/json": {
                    "example": {"detail": "Token inválido"}
                }
            }
        }
    }
)
async def listar_alunos(
    db: Database,
    current_user: CurrentUser,
    skip: int = Query(
        default=0,
        ge=0,
        description="Número de registros a pular (para paginação)"
    ),
    limit: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Número máximo de registros a retornar (máx: {settings.MAX_PAGE_SIZE})"
    ),
    nome: Optional[str] = Query(
        default=None,
        description="Filtrar por nome (busca parcial, case-insensitive)"
    ),
    idade: Optional[int] = Query(
        default=None,
        ge=5,
        le=100,
        description="Filtrar por idade exata"
    ),
    na_escola: Optional[bool] = Query(
        default=None,
        description="Filtrar por status de matrícula na escola"
    )
):
    """
    Lista todos os alunos com suporte a paginação e filtros.
    
    Requer autenticação JWT válida.
    """
    logger.info(
        f"Usuário {current_user} listando alunos "
        f"(skip={skip}, limit={limit}, nome={nome}, idade={idade}, na_escola={na_escola})"
    )
    
    service = AlunoService(db)
    alunos, total = await service.get_alunos(
        skip=skip,
        limit=limit,
        nome=nome,
        idade=idade,
        na_escola=na_escola
    )
    
    return AlunoListResponse(
        total=total,
        skip=skip,
        limit=limit,
        alunos=alunos
    )


@router.get(
    "/{aluno_id}",
    response_model=AlunoResponse,
    summary="Buscar Aluno por ID",
    description="""
    Retorna os dados detalhados de um aluno específico pelo ID.
    
    ### Autenticação Requerida:
    - Token JWT válido no header: `Authorization: Bearer {token}`
    
    ### Parâmetros:
    - **aluno_id**: ID único do aluno (ObjectId do MongoDB)
      - Deve ser um ObjectId válido de 24 caracteres hexadecimais
      - Exemplo: `507f1f77bcf86cd799439011`
    
    ### Retorno:
    - **200 OK**: Dados completos do aluno
    - **400 Bad Request**: ID inválido (não é um ObjectId válido)
    - **401 Unauthorized**: Token inválido ou ausente
    - **404 Not Found**: Aluno não encontrado com o ID fornecido
    """,
    responses={
        200: {
            "description": "Aluno encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "id": "507f1f77bcf86cd799439011",
                        "nome": "Toninho Silva",
                        "idade": 12,
                        "gostaDe": ["futebol", "games"],
                        "naEscola": True,
                        "materias": {
                            "português": 8.5,
                            "matemática": 9.0,
                            "história": 7.5
                        }
                    }
                }
            }
        },
        400: {
            "description": "ID inválido",
            "content": {
                "application/json": {
                    "example": {"detail": "ID '123' não é um ObjectId válido"}
                }
            }
        },
        404: {
            "description": "Aluno não encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Aluno com ID '507f1f77bcf86cd799439011' não foi encontrado"}
                }
            }
        }
    }
)
async def buscar_aluno(
    aluno_id: str,
    db: Database,
    current_user: CurrentUser
):
    """
    Busca um aluno específico por ID.
    
    Requer autenticação JWT válida.
    """
    logger.info(f"Usuário {current_user} buscando aluno: {aluno_id}")
    
    service = AlunoService(db)
    return await service.get_aluno_by_id(aluno_id)


@router.put(
    "/{aluno_id}",
    response_model=MessageResponse,
    summary="Substituir Aluno Completamente (PUT)",
    description="""
    Substitui **completamente** os dados de um aluno existente.
    
    ### ⚠️ Importante: PUT vs PATCH
    - **PUT** substitui o objeto inteiro (todos os campos devem ser fornecidos)
    - **PATCH** atualiza apenas campos específicos (use o endpoint PATCH se quiser atualizar parcialmente)
    
    ### Autenticação Requerida:
    - Token JWT válido no header: `Authorization: Bearer {token}`
    
    ### Comportamento:
    - Todos os dados antigos são descartados
    - Todos os campos do schema devem ser fornecidos
    - Validações aplicadas (mesmas da criação)
    
    ### Exemplo de Uso:
    ```json
    {
      "nome": "Toninho Silva Junior",
      "idade": 13,
      "gostaDe": ["futebol", "natação"],
      "naEscola": true,
      "materias": {
        "português": 9.0,
        "matemática": 9.5,
        "história": 8.0
      }
    }
    ```
    
    ### Retorno:
    - **200 OK**: Aluno atualizado com sucesso
    - **400 Bad Request**: ID inválido ou dados inválidos
    - **401 Unauthorized**: Token inválido
    - **404 Not Found**: Aluno não encontrado
    """,
    responses={
        200: {
            "description": "Aluno atualizado com sucesso",
            "content": {
                "application/json": {
                    "example": {"message": "Aluno atualizado com sucesso"}
                }
            }
        },
        404: {
            "description": "Aluno não encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Aluno com ID '...' não foi encontrado"}
                }
            }
        }
    }
)
async def substituir_aluno(
    aluno_id: str,
    aluno_data: AlunoCreate,
    db: Database,
    current_user: CurrentUser
):
    """
    Substitui completamente os dados de um aluno (PUT).
    
    Requer autenticação JWT válida.
    """
    logger.info(f"Usuário {current_user} substituindo aluno: {aluno_id}")
    
    service = AlunoService(db)
    await service.replace_aluno(aluno_id, aluno_data)
    
    return MessageResponse(message="Aluno atualizado com sucesso")


@router.patch(
    "/{aluno_id}",
    response_model=MessageResponse,
    summary="Atualizar Aluno Parcialmente (PATCH)",
    description="""
    Atualiza **apenas os campos especificados** de um aluno existente.
    
    ### ⚠️ Importante: PATCH vs PUT
    - **PATCH** atualiza apenas campos específicos (recomendado para atualizações parciais)
    - **PUT** substitui o objeto inteiro (use apenas se quiser substituir todos os dados)
    
    ### Autenticação Requerida:
    - Token JWT válido no header: `Authorization: Bearer {token}`
    
    ### Comportamento:
    - Apenas campos fornecidos são atualizados
    - Campos não fornecidos permanecem inalterados
    - Campos com valor `null` são ignorados
    - Validações aplicadas apenas nos campos fornecidos
    
    ### Exemplos de Uso:
    
    **Atualizar apenas idade:**
    ```json
    {
      "idade": 13
    }
    ```
    
    **Atualizar status de matrícula:**
    ```json
    {
      "naEscola": false
    }
    ```
    
    **Atualizar apenas notas de matemática:**
    ```json
    {
      "materias": {
        "português": 8.5,
        "matemática": 10.0,
        "história": 7.5
      }
    }
    ```
    
    **Atualizar múltiplos campos:**
    ```json
    {
      "idade": 13,
      "gostaDe": ["futebol", "natação", "xadrez"],
      "naEscola": true
    }
    ```
    
    ### Retorno:
    - **200 OK**: Campos atualizados com sucesso
    - **400 Bad Request**: ID inválido ou dados inválidos
    - **401 Unauthorized**: Token inválido
    - **404 Not Found**: Aluno não encontrado ou nenhum campo fornecido
    """,
    responses={
        200: {
            "description": "Campos atualizados com sucesso",
            "content": {
                "application/json": {
                    "example": {"message": "Campos atualizados"}
                }
            }
        },
        404: {
            "description": "Aluno não encontrado ou nenhum campo alterado",
            "content": {
                "application/json": {
                    "example": {"detail": "Aluno com ID '...' não foi encontrado"}
                }
            }
        }
    }
)
async def atualizar_aluno(
    aluno_id: str,
    aluno_data: AlunoUpdate,
    db: Database,
    current_user: CurrentUser
):
    """
    Atualiza parcialmente os dados de um aluno (PATCH).
    
    Requer autenticação JWT válida.
    """
    logger.info(f"Usuário {current_user} atualizando aluno: {aluno_id}")
    
    service = AlunoService(db)
    await service.update_aluno(aluno_id, aluno_data)
    
    return MessageResponse(message="Campos atualizados")


@router.delete(
    "/{aluno_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Remover Aluno",
    description="""
    Remove permanentemente um aluno do sistema.
    
    ### ⚠️ ATENÇÃO: Operação Irreversível
    - Esta ação **não pode ser desfeita**
    - Todos os dados do aluno serão permanentemente excluídos
    - Considere implementar soft delete em produção (marcar como inativo ao invés de remover)
    
    ### Autenticação Requerida:
    - Token JWT válido no header: `Authorization: Bearer {token}`
    
    ### Parâmetros:
    - **aluno_id**: ID único do aluno a ser removido
    
    ### Retorno:
    - **200 OK**: Aluno removido com sucesso
    - **400 Bad Request**: ID inválido
    - **401 Unauthorized**: Token inválido
    - **404 Not Found**: Aluno não encontrado
    
    ### Recomendação de Produção:
    Para ambientes de produção, considere implementar **soft delete**:
    - Adicione campo `ativo: boolean` no schema
    - Marque como `ativo: false` ao invés de remover
    - Filtre apenas alunos ativos nas listagens
    - Permite recuperação de dados e auditoria
    """,
    responses={
        200: {
            "description": "Aluno removido com sucesso",
            "content": {
                "application/json": {
                    "example": {"message": "Aluno removido"}
                }
            }
        },
        400: {
            "description": "ID inválido",
            "content": {
                "application/json": {
                    "example": {"detail": "ID '123' não é um ObjectId válido"}
                }
            }
        },
        404: {
            "description": "Aluno não encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Aluno com ID '...' não foi encontrado"}
                }
            }
        }
    }
)
async def remover_aluno(
    aluno_id: str,
    db: Database,
    current_user: CurrentUser
):
    """
    Remove um aluno do sistema.
    
    Requer autenticação JWT válida.
    ⚠️ Operação irreversível!
    """
    logger.warning(f"Usuário {current_user} removendo aluno: {aluno_id}")
    
    service = AlunoService(db)
    await service.delete_aluno(aluno_id)
    
    return MessageResponse(message="Aluno removido")
