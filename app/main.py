from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routers import transacoes

app = FastAPI(title="Controle de Gastos Pessoais")
app.include_router(transacoes.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    primeiro_erro = exc.errors()[0]
    mensagem = primeiro_erro.get("msg", "Dados inválidos")
    return JSONResponse(status_code=422, content={"erro": mensagem})
