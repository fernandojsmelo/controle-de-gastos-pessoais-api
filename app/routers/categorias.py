from fastapi import APIRouter, HTTPException, Response

from app.database import atualizar_categoria, criar_categoria, listar_categorias, remover_categoria
from app.models import Categoria, CategoriaCreate

router = APIRouter()


@router.post("/categorias", response_model=Categoria, status_code=201)
def criar(categoria: CategoriaCreate) -> dict:
    return criar_categoria(nome=categoria.nome)


@router.get("/categorias", response_model=list[Categoria])
def listar() -> list[dict]:
    return listar_categorias()


@router.put("/categorias/{id}", response_model=Categoria)
def atualizar(id: int, categoria: CategoriaCreate) -> dict:
    atualizada = atualizar_categoria(id=id, nome=categoria.nome)
    if atualizada is None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return atualizada


@router.delete("/categorias/{id}", status_code=204)
def remover(id: int) -> Response:
    if not remover_categoria(id):
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return Response(status_code=204)
