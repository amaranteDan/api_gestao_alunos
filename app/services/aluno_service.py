"""Service para lógica de negócio de Alunos."""
from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.schemas.aluno import AlunoCreate, AlunoUpdate, AlunoResponse
from app.core.exceptions import (
    AlunoNotFoundException,
    InvalidObjectIdException,
    DatabaseConnectionException
)
from app.core.logger import logger


class AlunoService:
    """
    Service para operações de negócio relacionadas a Alunos.
    
    Implementa o padrão Repository para separar lógica de negócio
    da camada de apresentação (routers).
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Inicializa o service com a conexão do banco.
        
        Args:
            db: Instância do banco de dados MongoDB
        """
        self.collection = db.alunos
    
    @staticmethod
    def _validate_object_id(aluno_id: str) -> ObjectId:
        """
        Valida e converte string para ObjectId.
        
        Args:
            aluno_id: ID do aluno como string
            
        Returns:
            ObjectId: ID convertido
            
        Raises:
            InvalidObjectIdException: Se o ID for inválido
        """
        if not ObjectId.is_valid(aluno_id):
            logger.warning(f"ObjectId inválido recebido: {aluno_id}")
            raise InvalidObjectIdException(aluno_id)
        return ObjectId(aluno_id)
    
    @staticmethod
    def _aluno_helper(aluno: dict) -> dict:
        """
        Converte documento MongoDB para formato de response.
        
        Args:
            aluno: Documento do MongoDB
            
        Returns:
            dict: Aluno formatado para response
        """
        return {
            "id": str(aluno["_id"]),
            "nome": aluno["nome"],
            "idade": aluno["idade"],
            "gostaDe": aluno["gostaDe"],
            "naEscola": aluno["naEscola"],
            "materias": aluno["materias"]
        }
    
    async def create_aluno(self, aluno_data: AlunoCreate) -> AlunoResponse:
        """
        Cria um novo aluno no banco de dados.
        
        Args:
            aluno_data: Dados do aluno a ser criado
            
        Returns:
            AlunoResponse: Aluno criado com ID
            
        Raises:
            DatabaseConnectionException: Se houver erro na inserção
        """
        try:
            aluno_dict = aluno_data.model_dump(by_alias=True)
            logger.info(f"Criando aluno: {aluno_dict.get('nome')}")
            
            result = await self.collection.insert_one(aluno_dict)
            
            if result.inserted_id:
                aluno_criado = await self.collection.find_one({"_id": result.inserted_id})
                logger.info(f"Aluno criado com sucesso: ID {result.inserted_id}")
                return AlunoResponse(**self._aluno_helper(aluno_criado))
            
            raise DatabaseConnectionException("Falha ao inserir aluno no banco")
            
        except DuplicateKeyError as e:
            logger.error(f"Aluno duplicado: {e}")
            raise DatabaseConnectionException("Já existe um aluno com esses dados")
        
        except PyMongoError as e:
            logger.error(f"Erro do MongoDB ao criar aluno: {e}")
            raise DatabaseConnectionException("Erro ao criar aluno no banco de dados")
        
        except Exception as e:
            logger.error(f"Erro inesperado ao criar aluno: {e}")
            raise DatabaseConnectionException("Erro inesperado ao criar aluno")
    
    async def get_alunos(
        self,
        skip: int = 0,
        limit: int = 10,
        nome: Optional[str] = None,
        idade: Optional[int] = None,
        na_escola: Optional[bool] = None
    ) -> tuple[List[AlunoResponse], int]:
        """
        Busca alunos com filtros e paginação.
        
        Args:
            skip: Número de registros a pular
            limit: Número máximo de registros
            nome: Filtro por nome (busca parcial, case-insensitive)
            idade: Filtro por idade exata
            na_escola: Filtro por status de matrícula
            
        Returns:
            tuple: (lista de alunos, total de registros)
        """
        try:
            # Constrói filtro
            filtro = {}
            if nome:
                filtro["nome"] = {"$regex": nome, "$options": "i"}
            if idade is not None:
                filtro["idade"] = idade
            if na_escola is not None:
                filtro["naEscola"] = na_escola
            
            logger.debug(f"Buscando alunos com filtro: {filtro}")
            
            # Busca total e documentos
            total = await self.collection.count_documents(filtro)
            cursor = self.collection.find(filtro).skip(skip).limit(limit)
            
            alunos = []
            async for aluno in cursor:
                alunos.append(AlunoResponse(**self._aluno_helper(aluno)))
            
            logger.info(f"Encontrados {len(alunos)} alunos de um total de {total}")
            return alunos, total
            
        except PyMongoError as e:
            logger.error(f"Erro do MongoDB ao buscar alunos: {e}")
            raise DatabaseConnectionException("Erro ao buscar alunos no banco de dados")
        
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar alunos: {e}")
            raise DatabaseConnectionException("Erro inesperado ao buscar alunos")
    
    async def get_aluno_by_id(self, aluno_id: str) -> AlunoResponse:
        """
        Busca um aluno por ID.
        
        Args:
            aluno_id: ID do aluno
            
        Returns:
            AlunoResponse: Dados do aluno
            
        Raises:
            InvalidObjectIdException: Se o ID for inválido
            AlunoNotFoundException: Se o aluno não for encontrado
        """
        object_id = self._validate_object_id(aluno_id)
        
        try:
            logger.debug(f"Buscando aluno por ID: {aluno_id}")
            aluno = await self.collection.find_one({"_id": object_id})
            
            if not aluno:
                logger.warning(f"Aluno não encontrado: {aluno_id}")
                raise AlunoNotFoundException(aluno_id)
            
            logger.info(f"Aluno encontrado: {aluno.get('nome')}")
            return AlunoResponse(**self._aluno_helper(aluno))
            
        except AlunoNotFoundException:
            raise
        
        except PyMongoError as e:
            logger.error(f"Erro do MongoDB ao buscar aluno: {e}")
            raise DatabaseConnectionException("Erro ao buscar aluno no banco de dados")
        
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar aluno: {e}")
            raise DatabaseConnectionException("Erro inesperado ao buscar aluno")
    
    async def replace_aluno(self, aluno_id: str, aluno_data: AlunoCreate) -> None:
        """
        Substitui completamente os dados de um aluno (PUT).
        
        Args:
            aluno_id: ID do aluno
            aluno_data: Novos dados completos do aluno
            
        Raises:
            InvalidObjectIdException: Se o ID for inválido
            AlunoNotFoundException: Se o aluno não for encontrado
        """
        object_id = self._validate_object_id(aluno_id)
        
        try:
            update_data = aluno_data.model_dump(by_alias=True)
            logger.info(f"Substituindo dados do aluno: {aluno_id}")
            
            result = await self.collection.replace_one(
                {"_id": object_id},
                update_data
            )
            
            if result.matched_count == 0:
                logger.warning(f"Aluno não encontrado para substituição: {aluno_id}")
                raise AlunoNotFoundException(aluno_id)
            
            logger.info(f"Aluno substituído com sucesso: {aluno_id}")
            
        except AlunoNotFoundException:
            raise
        
        except PyMongoError as e:
            logger.error(f"Erro do MongoDB ao substituir aluno: {e}")
            raise DatabaseConnectionException("Erro ao atualizar aluno no banco de dados")
        
        except Exception as e:
            logger.error(f"Erro inesperado ao substituir aluno: {e}")
            raise DatabaseConnectionException("Erro inesperado ao atualizar aluno")
    
    async def update_aluno(self, aluno_id: str, aluno_data: AlunoUpdate) -> None:
        """
        Atualiza parcialmente os dados de um aluno (PATCH).
        
        Args:
            aluno_id: ID do aluno
            aluno_data: Dados parciais para atualização
            
        Raises:
            InvalidObjectIdException: Se o ID for inválido
            AlunoNotFoundException: Se o aluno não for encontrado ou nenhum campo alterado
        """
        object_id = self._validate_object_id(aluno_id)
        
        # Filtra apenas campos fornecidos (não None)
        update_data = {
            k: v for k, v in aluno_data.model_dump(by_alias=True, exclude_unset=True).items()
            if v is not None
        }
        
        if not update_data:
            logger.warning(f"Nenhum campo fornecido para atualização: {aluno_id}")
            raise AlunoNotFoundException(aluno_id)
        
        try:
            logger.info(f"Atualizando campos do aluno {aluno_id}: {list(update_data.keys())}")
            
            result = await self.collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Aluno não encontrado para atualização: {aluno_id}")
                raise AlunoNotFoundException(aluno_id)
            
            logger.info(f"Aluno atualizado com sucesso: {aluno_id}")
            
        except AlunoNotFoundException:
            raise
        
        except PyMongoError as e:
            logger.error(f"Erro do MongoDB ao atualizar aluno: {e}")
            raise DatabaseConnectionException("Erro ao atualizar aluno no banco de dados")
        
        except Exception as e:
            logger.error(f"Erro inesperado ao atualizar aluno: {e}")
            raise DatabaseConnectionException("Erro inesperado ao atualizar aluno")
    
    async def delete_aluno(self, aluno_id: str) -> None:
        """
        Remove um aluno do banco de dados.
        
        Args:
            aluno_id: ID do aluno
            
        Raises:
            InvalidObjectIdException: Se o ID for inválido
            AlunoNotFoundException: Se o aluno não for encontrado
        """
        object_id = self._validate_object_id(aluno_id)
        
        try:
            logger.info(f"Removendo aluno: {aluno_id}")
            
            result = await self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count == 0:
                logger.warning(f"Aluno não encontrado para remoção: {aluno_id}")
                raise AlunoNotFoundException(aluno_id)
            
            logger.info(f"Aluno removido com sucesso: {aluno_id}")
            
        except AlunoNotFoundException:
            raise
        
        except PyMongoError as e:
            logger.error(f"Erro do MongoDB ao remover aluno: {e}")
            raise DatabaseConnectionException("Erro ao remover aluno do banco de dados")
        
        except Exception as e:
            logger.error(f"Erro inesperado ao remover aluno: {e}")
            raise DatabaseConnectionException("Erro inesperado ao remover aluno")
