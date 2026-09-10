# Controle de Gastos Pessoais

## Descrição

API para controle de gastos pessoais: permite registrar transações (entradas e
saídas), organizá-las por categoria e consultar o histórico. O projeto é
construído incrementalmente, aula a aula, seguindo specs em `specs/`.

## Stack

- Python 3.11+
- FastAPI
- SQLite, acessado via `sqlite3` da biblioteca padrão (sem ORM)
- Pydantic (schemas de request/response e validação)

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

O servidor sobe em `http://127.0.0.1:8000`. Documentação interativa em
`/docs`. O arquivo do banco (`gastos.db`) é criado automaticamente na raiz do
projeto na primeira inicialização, se não existir.

## Estrutura de pastas

```
SDD1/
├── CLAUDE.md
├── requirements.txt
├── .gitignore
├── gastos.db            # criado em runtime, ignorado no Git
├── app/
│   ├── main.py           # instância do FastAPI, startup (init_db) e handler de erro 422
│   ├── database.py        # conexão SQLite (get_connection) e criação do banco (init_db)
│   ├── models.py          # schemas Pydantic (request/response)
│   └── routers/            # rotas da API, um módulo por recurso
├── docs/                   # roteiro de prompts do curso, aula a aula
├── specs/                  # uma spec por aula (fonte de verdade do escopo)
└── .claude/
    └── commands/
        └── implementar-spec.md  # slash command /implementar-spec
```

## Convenções

- Datas sempre em ISO `YYYY-MM-DD`.
- Valores monetários com 2 casas decimais.
- Campo `tipo` de transação sempre `"entrada"` ou `"saida"`.
- Erros de validação retornam HTTP 422 com corpo `{ "erro": "<mensagem clara>" }`
  (implementado globalmente via `exception_handler` de `RequestValidationError`
  em `app/main.py` — não repetir esse tratamento rota a rota).
- Banco SQLite em arquivo local, criado na inicialização do servidor se não existir.
- Código organizado em módulos (rotas em `app/routers/`, schemas em
  `app/models.py`, acesso a dados em `app/database.py`).
- Acesso ao SQLite via `sqlite3` puro (não SQLModel/ORM) — decisão tomada para
  manter controle direto do SQL, necessário para agregações e filtros
  dinâmicos com parâmetros vinculados nas aulas futuras.
- Cada aula implementa apenas a spec correspondente em `specs/`; escopo de
  aulas futuras não deve ser adiantado.
- Commit ao final de cada aula, com a spec correspondente versionada junto.

## Decisões registradas

- **Aula 2 — validação de escrita:** `valor > 0`, `tipo` válido e `data` ISO
  válida são validados via tipos do Pydantic (`Field(gt=0)`, `Literal`,
  `date`) desde a Aula 1; `descricao` não vazia foi adicionada na Aula 2 via
  `field_validator` (faz `strip()` e rejeita string vazia). Todas essas regras
  valem tanto para `POST` quanto para `PUT`, pois os dois reutilizam o mesmo
  schema `TransacaoCreate`.
- **Aula 2 — formato do 404:** `PUT`/`DELETE` em `id` inexistente retornam
  404 no formato padrão do FastAPI (`{"detail": "..."}`). O `{"erro": ...}`
  do CLAUDE.md vale só para 422 de validação — não foi estendido a outros
  status, para não inventar convenção que a spec não pediu.
- **Aula 3 — `categoria_id` é opcional:** transações podem existir sem
  categoria. Decisão forçada pela própria spec, que exige manter
  compatibilidade com as transações da Aula 1/2 (sem categoria); tornar o
  campo obrigatório exigiria migrar dados antigos para algo que nenhum
  critério de aceite pede.
- **Aula 3 — filtro por categoria inexistente retorna lista vazia (200),
  não 404:** `GET /transacoes?categoria=...` é uma busca numa coleção, não
  a busca de um recurso por id — lista vazia é a resposta natural de uma
  busca sem resultados. Também evita ambiguidade quando a Aula 5 combinar
  `categoria` com outros filtros (período, valor): não há "qual filtro
  errou" a decidir, só resultado vazio.
