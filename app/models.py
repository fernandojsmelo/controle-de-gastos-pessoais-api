from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

TipoTransacao = Literal["entrada", "saida"]


class TransacaoCreate(BaseModel):
    data: date
    descricao: str
    valor: float = Field(gt=0)
    tipo: TipoTransacao
    categoria_id: int | None = None

    @field_validator("descricao")
    @classmethod
    def descricao_nao_vazia(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("descricao não pode ser vazia")
        return valor


class Transacao(TransacaoCreate):
    id: int


class CategoriaCreate(BaseModel):
    nome: str


class Categoria(CategoriaCreate):
    id: int


class Saldo(BaseModel):
    entradas: float
    saidas: float
    saldo: float


class CategoriaResumo(BaseModel):
    categoria: str
    total: float


class Resumo(BaseModel):
    mes: str
    entradas: float
    saidas: float
    saldo: float
    por_categoria: list[CategoriaResumo]
