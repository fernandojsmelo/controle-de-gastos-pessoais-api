from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

TipoTransacao = Literal["entrada", "saida"]


class TransacaoCreate(BaseModel):
    data: date
    descricao: str
    valor: float = Field(gt=0)
    tipo: TipoTransacao

    @field_validator("descricao")
    @classmethod
    def descricao_nao_vazia(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("descricao não pode ser vazia")
        return valor


class Transacao(TransacaoCreate):
    id: int
