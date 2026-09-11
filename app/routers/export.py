import csv
import io
from datetime import date

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from app.routers.transacoes import resolver_transacoes

router = APIRouter()

COLUNAS_CSV = ["id", "data", "descricao", "valor", "tipo", "categoria_id"]


@router.get("/export.csv")
def exportar_csv(
    categoria: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    valor_min: float | None = None,
    valor_max: float | None = None,
):
    resultado = resolver_transacoes(
        categoria=categoria,
        data_inicio=data_inicio,
        data_fim=data_fim,
        valor_min=valor_min,
        valor_max=valor_max,
    )
    if isinstance(resultado, JSONResponse):
        return resultado

    buffer = io.StringIO()
    escritor = csv.DictWriter(buffer, fieldnames=COLUNAS_CSV)
    escritor.writeheader()
    for transacao in resultado:
        escritor.writerow({coluna: transacao[coluna] for coluna in COLUNAS_CSV})

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"},
    )
