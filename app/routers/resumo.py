from fastapi import APIRouter, Query

from app.database import calcular_saldo, calcular_totais_mes, resumo_por_categoria
from app.models import Resumo, Saldo

router = APIRouter()


@router.get("/saldo", response_model=Saldo)
def saldo() -> dict:
    entradas, saidas = calcular_saldo()
    return {
        "entradas": round(entradas, 2),
        "saidas": round(saidas, 2),
        "saldo": round(entradas - saidas, 2),
    }


@router.get("/resumo", response_model=Resumo)
def resumo(mes: str = Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")) -> dict:
    entradas, saidas = calcular_totais_mes(mes)
    return {
        "mes": mes,
        "entradas": round(entradas, 2),
        "saidas": round(saidas, 2),
        "saldo": round(entradas - saidas, 2),
        "por_categoria": resumo_por_categoria(mes),
    }
