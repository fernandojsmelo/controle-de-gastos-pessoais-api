from fastapi import APIRouter

from app.database import criar_categoria, listar_categorias
from app.models import Categoria, CategoriaCreate

router = APIRouter()


@router.post("/categorias", response_model=Categoria, status_code=201)
def criar(categoria: CategoriaCreate) -> dict:
    return criar_categoria(nome=categoria.nome)


@router.get("/categorias", response_model=list[Categoria])
def listar() -> list[dict]:
    return listar_categorias()
