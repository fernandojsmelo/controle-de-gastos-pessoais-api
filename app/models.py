from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

TipoTransacao = Literal["entrada", "saida"]


class TransacaoCreate(BaseModel):
    data: date
    descricao: str
    valor: float = Field(gt=0)
    tipo: TipoTransacao


class Transacao(TransacaoCreate):
    id: int
