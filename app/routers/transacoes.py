from datetime import date

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse

from app.database import (
    atualizar_transacao,
    buscar_categoria_por_nome,
    criar_transacao,
    listar_transacoes,
    remover_transacao,
)
from app.models import Transacao, TransacaoCreate

router = APIRouter()


def resolver_transacoes(
    categoria: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    valor_min: float | None = None,
    valor_max: float | None = None,
) -> list[dict] | JSONResponse:
    """Aplica os filtros da Aula 5 e devolve a lista de transações, ou uma
    JSONResponse 422 se os filtros forem inválidos. Compartilhado entre
    `GET /transacoes` e `GET /export.csv`."""
    if data_inicio is not None and data_fim is not None and data_inicio > data_fim:
        return JSONResponse(status_code=422, content={"erro": "data_inicio não pode ser depois de data_fim"})
    if valor_min is not None and valor_max is not None and valor_min > valor_max:
        return JSONResponse(status_code=422, content={"erro": "valor_min não pode ser maior que valor_max"})

    categoria_id = None
    if categoria is not None:
        if categoria.isdigit():
            categoria_id = int(categoria)
        else:
            encontrada = buscar_categoria_por_nome(categoria)
            if encontrada is None:
                return []
            categoria_id = encontrada["id"]

    return listar_transacoes(
        categoria_id=categoria_id,
        data_inicio=data_inicio.isoformat() if data_inicio else None,
        data_fim=data_fim.isoformat() if data_fim else None,
        valor_min=valor_min,
        valor_max=valor_max,
    )


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
def listar(
    categoria: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    valor_min: float | None = None,
    valor_max: float | None = None,
):
    return resolver_transacoes(
        categoria=categoria,
        data_inicio=data_inicio,
        data_fim=data_fim,
        valor_min=valor_min,
        valor_max=valor_max,
    )


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
