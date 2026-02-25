"""Conexão e gerenciamento do MongoDB."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from app.core.config import settings
from app.core.logger import logger


class MongoDB:
    """
    Classe para gerenciar a conexão com MongoDB.
    
    Implementa padrão Singleton para garantir uma única conexão.
    """
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect_db(cls) -> None:
        """
        Estabelece conexão com MongoDB.
        
        Raises:
            Exception: Se houver erro na conexão
        """
        try:
            logger.info("Conectando ao MongoDB...")
            cls.client = AsyncIOMotorClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=10,
                minPoolSize=1,
            )
            
            # Testa a conexão
            await cls.client.admin.command('ping')
            
            cls.db = cls.client[settings.MONGO_DB_NAME]
            logger.info(f"Conexão com MongoDB estabelecida: {settings.MONGO_DB_NAME}")
            
            # Cria índices
            await cls._create_indexes()
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao MongoDB: {e}")
            raise
    
    @classmethod
    async def close_db(cls) -> None:
        """
        Fecha a conexão com MongoDB.
        """
        if cls.client:
            logger.info("Fechando conexão com MongoDB...")
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("Conexão com MongoDB fechada")
    
    @classmethod
    async def _create_indexes(cls) -> None:
        """
        Cria índices no banco de dados para otimizar queries.
        """
        try:
            # Índice para busca por nome (case-insensitive)
            await cls.db.alunos.create_index("nome")
            
            # Índice para busca por idade
            await cls.db.alunos.create_index("idade")
            
            # Índice para username (usuários) - único
            await cls.db.usuarios.create_index("username", unique=True)
            
            logger.info("Índices criados com sucesso")
        except Exception as e:
            logger.warning(f"Erro ao criar índices: {e}")
    
    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """
        Retorna a instância do banco de dados.
        
        Returns:
            AsyncIOMotorDatabase: Instância do banco de dados
            
        Raises:
            RuntimeError: Se o banco não estiver conectado
        """
        if cls.db is None:
            logger.error("Tentativa de acessar banco não conectado")
            raise RuntimeError("Banco de dados não conectado. Execute connect_db() primeiro.")
        return cls.db
    
    @classmethod
    async def health_check(cls) -> bool:
        """
        Verifica se a conexão com o banco está saudável.
        
        Returns:
            bool: True se a conexão está OK
        """
        try:
            if cls.client:
                await cls.client.admin.command('ping')
                return True
            return False
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return False


def get_database() -> AsyncIOMotorDatabase:
    """
    Função auxiliar para obter o banco de dados (dependency injection).
    
    Returns:
        AsyncIOMotorDatabase: Instância do banco de dados
    """
    return MongoDB.get_db()
