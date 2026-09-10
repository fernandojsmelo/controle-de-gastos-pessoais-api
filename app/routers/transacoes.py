from fastapi import APIRouter, HTTPException, Response

from app.database import (
    atualizar_transacao,
    buscar_categoria_por_nome,
    criar_transacao,
    listar_transacoes,
    remover_transacao,
)
from app.models import Transacao, TransacaoCreate

router = APIRouter()


@router.post("/transacoes", response_model=Transacao, status_code=201)
def criar(transacao: TransacaoCreate) -> dict:
    return criar_transacao(
        data=transacao.data.isoformat(),
        descricao=transacao.descricao,
        valor=round(transacao.valor, 2),
        tipo=transacao.tipo,
        categoria_id=transacao.categoria_id,
    )


@router.get("/transacoes", response_model=list[Transacao])
def listar(categoria: str | None = None) -> list[dict]:
    if categoria is None:
        return listar_transacoes()
    if categoria.isdigit():
        return listar_transacoes(categoria_id=int(categoria))
    encontrada = buscar_categoria_por_nome(categoria)
    if encontrada is None:
        return []
    return listar_transacoes(categoria_id=encontrada["id"])


@router.put("/transacoes/{id}", response_model=Transacao)
def atualizar(id: int, transacao: TransacaoCreate) -> dict:
    atualizada = atualizar_transacao(
        id=id,
        data=transacao.data.isoformat(),
        descricao=transacao.descricao,
        valor=round(transacao.valor, 2),
        tipo=transacao.tipo,
        categoria_id=transacao.categoria_id,
    )
    if atualizada is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return atualizada


@router.delete("/transacoes/{id}", status_code=204)
def remover(id: int) -> Response:
    if not remover_transacao(id):
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return Response(status_code=204)
