from fastapi import APIRouter, HTTPException, status, Depends
from app.api.deps import Database, CurrentUser
from bson import ObjectId
from typing import List

router = APIRouter(prefix="/usuarios", tags=["Gestão de Usuários"])

async def verificar_admin(username: CurrentUser, db: Database):
    """Dependência auxiliar para garantir que apenas admins acessem estas rotas."""
    usuario = await db.usuarios.find_one({"username": username})
    if not usuario or usuario.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores."
        )
    return usuario

@router.get("/", summary="Listar todos os usuários")
async def listar_usuarios(db: Database, admin=Depends(verificar_admin)):
    usuarios = await db.usuarios.find({}, {"hashed_password": 0}).to_list(length=100)
    # Converte o _id do MongoDB para string para o JSON aceitar
    for u in usuarios:
        u["id"] = str(u.pop("_id"))
    return usuarios

@router.patch("/{username}/ativar", summary="Aprovar/Ativar um usuário")
async def ativar_usuario(username: str, db: Database, admin=Depends(verificar_admin)):
    """Muda o status de is_active para True."""
    resultado = await db.usuarios.update_one(
        {"username": username},
        {"$set": {"is_active": True}}
    )
    
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    return {"msg": f"Usuário {username} ativado com sucesso!"}

@router.patch("/{username}/desativar", summary="Bloquear um usuário")
async def desativar_usuario(username: str, db: Database, admin=Depends(verificar_admin)):
    """Muda o status de is_active para False."""
    if username == admin["username"]:
        raise HTTPException(status_code=400, detail="Você não pode desativar a si mesmo")
        
    await db.usuarios.update_one(
        {"username": username},
        {"$set": {"is_active": False}}
    )
    return {"msg": f"Usuário {username} desativado!"}