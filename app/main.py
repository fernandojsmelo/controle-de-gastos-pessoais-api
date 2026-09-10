from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.database import ErroDominio, init_db
from app.routers import categorias, transacoes

app = FastAPI(title="Controle de Gastos Pessoais")
app.include_router(transacoes.router)
app.include_router(categorias.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    primeiro_erro = exc.errors()[0]
    mensagem = primeiro_erro.get("msg", "Dados inválidos")
    return JSONResponse(status_code=422, content={"erro": mensagem})


@app.exception_handler(ErroDominio)
async def erro_dominio_handler(request: Request, exc: ErroDominio) -> JSONResponse:
    return JSONResponse(status_code=422, content={"erro": exc.mensagem})
