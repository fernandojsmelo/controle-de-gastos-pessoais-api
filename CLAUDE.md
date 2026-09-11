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
`/docs`. Dashboard visual em `/` ou `/dashboard`. O arquivo do banco
(`gastos.db`) é criado automaticamente na raiz do projeto na primeira
inicialização, se não existir.

### Deploy

Configurações sensíveis a ambiente vêm de variáveis de ambiente (ver
`.env.example`): `PORT` (porta do Uvicorn, default `8000`), `HOST` (default
`0.0.0.0`) e `DATABASE_PATH` (caminho do arquivo SQLite, default
`gastos.db` na raiz). Fora da máquina local, rode com:

```bash
python -m app.main
```

que lê `HOST`/`PORT` do ambiente e sobe o Uvicorn programaticamente (em vez
de `uvicorn app.main:app --reload`, usado só em desenvolvimento).

## Como rodar os testes

```bash
pytest
```

A suíte (`tests/`) usa o `TestClient` do FastAPI com um banco SQLite
temporário por teste (fixture `client` em `tests/conftest.py`, troca
`database.DB_PATH` via `monkeypatch` antes de abrir o cliente) — nunca toca
o `gastos.db` de desenvolvimento. `conftest.py` na raiz do projeto (vazio)
só garante que `app` seja importável independente de como o `pytest` for
invocado. CI (`.github/workflows/tests.yml`) roda essa mesma suíte a cada
`push`/`pull_request` para `main`.

## Estrutura de pastas

```
SDD1/
├── CLAUDE.md
├── requirements.txt        # versões fixas (==) das dependências diretas
├── .gitignore
├── .env.example           # variáveis de ambiente suportadas (PORT, HOST, DATABASE_PATH)
├── .github/
│   └── workflows/
│       └── tests.yml       # CI: roda pytest a cada push/PR para main
├── conftest.py           # garante "app" importável nos testes
├── gastos.db             # criado em runtime, ignorado no Git
├── app/
│   ├── main.py            # instância do FastAPI, startup (init_db), handler de erro 422 e entrypoint de deploy (`python -m app.main`)
│   ├── database.py         # conexão SQLite (get_connection) e criação do banco (init_db)
│   ├── models.py           # schemas Pydantic (request/response)
│   ├── routers/             # rotas da API, um módulo por recurso
│   └── static/               # assets estáticos servidos pelo FastAPI (dashboard.html)
├── tests/
│   ├── conftest.py         # fixture client (TestClient + banco temporário)
│   └── test_api.py         # suíte pytest (fluxos principais + casos de erro)
├── docs/                    # roteiro de prompts do curso, aula a aula
├── specs/                   # uma spec por aula (fonte de verdade do escopo)
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
- **Aula 4 — `por_categoria` do resumo inclui só `saida`:** a spec pede
  "quebra de **gastos** por categoria" — "gasto" é despesa, então entradas
  não entram nessa quebra (mas contam nos totais `entradas`/`saldo` do mês
  normalmente). Transações sem `categoria_id` também ficam de fora de
  `por_categoria` (não há o que agrupar), mas continuam nos totais gerais.
  `categoria` no resultado é o **nome**, não o id — mais legível num resumo.
- **Aula 5 — período/valor invertidos como "erro de validação":** `data_inicio
  > data_fim` e `valor_min > valor_max` não são erros de tipo (o Pydantic já
  valida isso), então o router de `GET /transacoes` retorna
  `JSONResponse(422, {"erro": ...})` manualmente para esses dois casos,
  mesmo formato do handler global — não criamos uma exceção nova só para
  isso (diferente do `ErroDominio`, reservado a violações detectadas pelo
  SQLite).
- **Aula 6 — filtros do `/export.csv` reaproveitam `/transacoes`:** a lógica
  de resolução e validação dos filtros da Aula 5 (incluindo os 422 de
  período/valor invertidos) foi extraída para
  `resolver_transacoes()` em `app/routers/transacoes.py`, usada tanto por
  `GET /transacoes` quanto por `GET /export.csv` — evita duas implementações
  divergentes do mesmo filtro.
- **Aula 6 — colunas do CSV:** `id, data, descricao, valor, tipo,
  categoria_id`, os mesmos campos do schema `Transacao` (sem juntar o nome
  da categoria) — mantém o CSV como espelho direto do registro armazenado.
- **Aula 6 — dashboard sem endpoint novo:** o HTML em `app/static/dashboard.html`
  consome `GET /saldo` e `GET /resumo?mes=<mês atual>` (calculado no
  cliente) para montar o gráfico de gastos por categoria e o saldo atual —
  a spec pede consumir "os endpoints existentes", então nenhuma agregação
  nova foi criada no backend só para o dashboard.
- **Aula 6 — deploy via `python -m app.main`:** `HOST`/`PORT` (Uvicorn) e
  `DATABASE_PATH` (SQLite) viram configuráveis por variável de ambiente,
  com os mesmos defaults de desenvolvimento quando não definidas. Não há
  credenciais no projeto hoje; `.env.example` documenta as variáveis sem
  valores sensíveis, e `.env` real já está no `.gitignore`.
- **Aula 6 — botão "+ Nova transação" no dashboard:** `app/static/dashboard.html`
  ganhou um formulário (data, valor, tipo, categoria, descrição) que chama
  `POST /transacoes` direto do navegador — não é um endpoint novo, só um
  cliente a mais do `POST /transacoes` que já existia. Erros 422 do backend
  são exibidos inline; sucesso atualiza saldo e gráfico sem recarregar a
  página.
- **Pós-projeto — `DELETE /categorias/{id}` bloqueia se a categoria estiver
  em uso:** decisão explícita (não é comportamento óbvio de uma FK) —
  remover a categoria de uma transação existente silenciosamente
  (`categoria_id = NULL`) alteraria dado histórico do usuário sem ele pedir.
  Em vez disso, `remover_categoria` retorna 422 `{"erro": "Categoria em uso,
  não pode ser removida"}`; o usuário precisa reatribuir/remover as
  transações primeiro. `PUT /categorias/{id}` segue o mesmo padrão de
  `PUT /transacoes/{id}`: nome duplicado → 422, id inexistente → 404.
- **Pós-projeto — dinheiro guardado em centavos (inteiro), não reais
  (float):** a coluna `valor` em `transacoes` passou a guardar centavos
  (`INTEGER`) via `reais_para_centavos`/`centavos_para_reais`
  (`app/database.py`). O contrato da API não muda — `POST`/`PUT
  /transacoes`, `GET /saldo`, `GET /resumo` e `GET /export.csv` continuam
  recebendo/devolvendo reais em float — só a soma interna (`SUM` em
  `calcular_saldo`, `calcular_totais_mes`, `resumo_por_categoria`) deixa de
  acumular erro de ponto flutuante (ex.: três lançamentos de `0.10` somando
  `0.30000000000000004` em vez de `0.30`). Bancos existentes são migrados
  automaticamente e uma única vez em `init_db()`, controlado por `PRAGMA
  user_version` (mesmo padrão de migração idempotente já usado para a
  coluna `categoria_id`).
