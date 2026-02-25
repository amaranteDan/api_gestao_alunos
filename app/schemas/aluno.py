"""Schemas para entidade Aluno."""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Materias(BaseModel):
    """
    Schema para notas das matérias.
    
    Todas as notas devem estar entre 0 e 10.
    """
    
    portugues: float = Field(
        ...,
        alias="português",
        ge=0,
        le=10,
        description="Nota de Português (0-10)",
        examples=[8.5]
    )
    matematica: float = Field(
        ...,
        alias="matemática",
        ge=0,
        le=10,
        description="Nota de Matemática (0-10)",
        examples=[9.0]
    )
    historia: float = Field(
        ...,
        alias="história",
        ge=0,
        le=10,
        description="Nota de História (0-10)",
        examples=[7.5]
    )
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "português": 8.5,
                    "matemática": 9.0,
                    "história": 7.5
                }
            ]
        }
    )


class AlunoBase(BaseModel):
    """
    Schema base para Aluno (usado em criação e atualização completa).
    """
    
    nome: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nome completo do aluno",
        examples=["Toninho Silva"]
    )
    idade: int = Field(
        ...,
        ge=5,
        le=100,
        description="Idade do aluno (5-100 anos)",
        examples=[12]
    )
    gostaDe: List[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Lista de hobbies ou interesses do aluno (1-10 itens)",
        examples=[["futebol", "games", "leitura"]]
    )
    naEscola: bool = Field(
        ...,
        description="Indica se o aluno está matriculado na escola",
        examples=[True]
    )
    materias: Materias = Field(
        ...,
        description="Notas do aluno nas matérias"
    )
    
    @field_validator("gostaDe")
    @classmethod
    def validate_hobbies(cls, v: List[str]) -> List[str]:
        """Valida lista de hobbies: não vazia, sem duplicatas, tamanho adequado."""
        if not v:
            raise ValueError("Lista de hobbies não pode estar vazia")
        
        # Remove duplicatas mantendo ordem
        unique_hobbies = []
        for hobby in v:
            if hobby.strip() and hobby not in unique_hobbies:
                unique_hobbies.append(hobby.strip())
        
        if not unique_hobbies:
            raise ValueError("Hobbies não podem ser strings vazias")
        
        # Valida tamanho de cada hobby
        for hobby in unique_hobbies:
            if len(hobby) > 50:
                raise ValueError(f"Hobby '{hobby}' excede o tamanho máximo de 50 caracteres")
        
        return unique_hobbies
    
    @field_validator("nome")
    @classmethod
    def validate_nome(cls, v: str) -> str:
        """Valida e normaliza o nome do aluno."""
        nome = v.strip()
        
        if not nome:
            raise ValueError("Nome não pode estar vazio")
        
        if not all(c.isalpha() or c.isspace() for c in nome):
            raise ValueError("Nome deve conter apenas letras e espaços")
        
        # Capitaliza cada palavra
        return " ".join(word.capitalize() for word in nome.split())
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "nome": "Toninho Silva",
                    "idade": 12,
                    "gostaDe": ["futebol", "games", "leitura"],
                    "naEscola": True,
                    "materias": {
                        "português": 8.5,
                        "matemática": 9.0,
                        "história": 7.5
                    }
                }
            ]
        }
    )


class AlunoCreate(AlunoBase):
    """
    Schema para criação de novo aluno (POST).
    
    Herda todos os campos de AlunoBase.
    """
    pass


class AlunoUpdate(BaseModel):
    """
    Schema para atualização parcial de aluno (PATCH).
    
    Todos os campos são opcionais.
    """
    
    nome: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Nome completo do aluno",
        examples=["Toninho Silva"]
    )
    idade: Optional[int] = Field(
        None,
        ge=5,
        le=100,
        description="Idade do aluno (5-100 anos)",
        examples=[13]
    )
    gostaDe: Optional[List[str]] = Field(
        None,
        min_length=1,
        max_length=10,
        description="Lista de hobbies ou interesses do aluno",
        examples=[["futebol", "música"]]
    )
    naEscola: Optional[bool] = Field(
        None,
        description="Indica se o aluno está matriculado na escola",
        examples=[False]
    )
    materias: Optional[Materias] = Field(
        None,
        description="Notas do aluno nas matérias"
    )
    
    @field_validator("gostaDe")
    @classmethod
    def validate_hobbies(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Valida lista de hobbies se fornecida."""
        if v is None:
            return v
        
        if not v:
            raise ValueError("Lista de hobbies não pode estar vazia")
        
        unique_hobbies = []
        for hobby in v:
            if hobby.strip() and hobby not in unique_hobbies:
                unique_hobbies.append(hobby.strip())
        
        if not unique_hobbies:
            raise ValueError("Hobbies não podem ser strings vazias")
        
        for hobby in unique_hobbies:
            if len(hobby) > 50:
                raise ValueError(f"Hobby '{hobby}' excede o tamanho máximo de 50 caracteres")
        
        return unique_hobbies
    
    @field_validator("nome")
    @classmethod
    def validate_nome(cls, v: Optional[str]) -> Optional[str]:
        """Valida e normaliza o nome se fornecido."""
        if v is None:
            return v
        
        nome = v.strip()
        
        if not nome:
            raise ValueError("Nome não pode estar vazio")
        
        if not all(c.isalpha() or c.isspace() for c in nome):
            raise ValueError("Nome deve conter apenas letras e espaços")
        
        return " ".join(word.capitalize() for word in nome.split())
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "idade": 13,
                    "naEscola": False
                },
                {
                    "materias": {
                        "português": 9.0,
                        "matemática": 8.5,
                        "história": 8.0
                    }
                }
            ]
        }
    )


class AlunoResponse(AlunoBase):
    """
    Schema de resposta para Aluno.
    
    Inclui o ID do MongoDB convertido para string.
    """
    
    id: str = Field(
        ...,
        description="ID único do aluno (ObjectId do MongoDB)",
        examples=["507f1f77bcf86cd799439011"]
    )
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "507f1f77bcf86cd799439011",
                    "nome": "Toninho Silva",
                    "idade": 12,
                    "gostaDe": ["futebol", "games", "leitura"],
                    "naEscola": True,
                    "materias": {
                        "português": 8.5,
                        "matemática": 9.0,
                        "história": 7.5
                    }
                }
            ]
        }
    )


class AlunoListResponse(BaseModel):
    """
    Schema de resposta para listagem de alunos com paginação.
    """
    
    total: int = Field(
        ...,
        description="Total de alunos no banco de dados",
        examples=[42]
    )
    skip: int = Field(
        ...,
        description="Número de registros pulados",
        examples=[0]
    )
    limit: int = Field(
        ...,
        description="Número máximo de registros retornados",
        examples=[10]
    )
    alunos: List[AlunoResponse] = Field(
        ...,
        description="Lista de alunos"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total": 42,
                    "skip": 0,
                    "limit": 10,
                    "alunos": [
                        {
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
                    ]
                }
            ]
        }
    )


class MessageResponse(BaseModel):
    """
    Schema genérico para respostas de mensagem.
    """
    
    message: str = Field(
        ...,
        description="Mensagem de resposta",
        examples=["Operação realizada com sucesso"]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"message": "Aluno criado com sucesso"},
                {"message": "Aluno atualizado com sucesso"},
                {"message": "Aluno removido com sucesso"}
            ]
        }
    )
