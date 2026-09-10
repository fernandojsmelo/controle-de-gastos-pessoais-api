from fastapi import APIRouter

from app.database import criar_transacao, listar_transacoes
from app.models import Transacao, TransacaoCreate

router = APIRouter()


@router.post("/transacoes", response_model=Transacao, status_code=201)
def criar(transacao: TransacaoCreate) -> dict:
    return criar_transacao(
        data=transacao.data.isoformat(),
        descricao=transacao.descricao,
        valor=round(transacao.valor, 2),
        tipo=transacao.tipo,
    )


@router.get("/transacoes", response_model=list[Transacao])
def listar() -> list[dict]:
    return listar_transacoes()
