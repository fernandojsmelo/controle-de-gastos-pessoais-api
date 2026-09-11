import csv
import io


def criar_transacao(client, **overrides):
    corpo = {
        "data": "2026-05-10",
        "descricao": "Transação de teste",
        "valor": 100.0,
        "tipo": "saida",
    }
    corpo.update(overrides)
    return client.post("/transacoes", json=corpo)


def criar_categoria(client, nome):
    return client.post("/categorias", json={"nome": nome})


# --- transações: CRUD básico ---


def test_criar_transacao_retorna_201_com_id(client):
    resposta = criar_transacao(client)
    assert resposta.status_code == 201
    assert "id" in resposta.json()


def test_listar_transacoes_ordenadas_por_data_desc(client):
    criar_transacao(client, data="2026-01-10", descricao="Mais antiga")
    criar_transacao(client, data="2026-02-15", descricao="Mais recente")

    resposta = client.get("/transacoes")
    assert resposta.status_code == 200
    descricoes = [t["descricao"] for t in resposta.json()]
    assert descricoes == ["Mais recente", "Mais antiga"]


def test_atualizar_transacao(client):
    id_criada = criar_transacao(client).json()["id"]

    resposta = client.put(
        f"/transacoes/{id_criada}",
        json={"data": "2026-06-01", "descricao": "Atualizada", "valor": 50.0, "tipo": "entrada"},
    )
    assert resposta.status_code == 200
    assert resposta.json()["descricao"] == "Atualizada"


def test_atualizar_transacao_inexistente_404(client):
    resposta = client.put(
        "/transacoes/999",
        json={"data": "2026-06-01", "descricao": "X", "valor": 50.0, "tipo": "entrada"},
    )
    assert resposta.status_code == 404


def test_excluir_transacao(client):
    id_criada = criar_transacao(client).json()["id"]

    resposta = client.delete(f"/transacoes/{id_criada}")
    assert resposta.status_code == 204
    assert client.get("/transacoes").json() == []


def test_excluir_transacao_inexistente_404(client):
    resposta = client.delete("/transacoes/999")
    assert resposta.status_code == 404


# --- transações: validação ---


def test_criar_transacao_valor_invalido_422(client):
    resposta = criar_transacao(client, valor=0)
    assert resposta.status_code == 422
    assert "erro" in resposta.json()


def test_criar_transacao_tipo_invalido_422(client):
    resposta = criar_transacao(client, tipo="invalido")
    assert resposta.status_code == 422


def test_criar_transacao_data_invalida_422(client):
    resposta = criar_transacao(client, data="10-05-2026")
    assert resposta.status_code == 422


def test_criar_transacao_descricao_vazia_422(client):
    resposta = criar_transacao(client, descricao="   ")
    assert resposta.status_code == 422


# --- categorias ---


def test_criar_categoria_e_listar(client):
    resposta = criar_categoria(client, "alimentacao")
    assert resposta.status_code == 201

    assert [c["nome"] for c in client.get("/categorias").json()] == ["alimentacao"]


def test_criar_categoria_duplicada_422(client):
    criar_categoria(client, "alimentacao")
    resposta = criar_categoria(client, "alimentacao")
    assert resposta.status_code == 422
    assert "erro" in resposta.json()


# --- filtros ---


def test_filtrar_transacoes_por_categoria_nome_e_id(client):
    categoria_id = criar_categoria(client, "transporte").json()["id"]
    criar_transacao(client, descricao="Uber", categoria_id=categoria_id)
    criar_transacao(client, descricao="Sem categoria")

    por_nome = client.get("/transacoes?categoria=transporte").json()
    por_id = client.get(f"/transacoes?categoria={categoria_id}").json()

    assert [t["descricao"] for t in por_nome] == ["Uber"]
    assert [t["descricao"] for t in por_id] == ["Uber"]


def test_filtrar_categoria_inexistente_retorna_lista_vazia(client):
    criar_transacao(client)
    assert client.get("/transacoes?categoria=inexistente").json() == []
    assert client.get("/transacoes?categoria=999").json() == []


def test_filtrar_por_periodo(client):
    criar_transacao(client, data="2026-01-01", descricao="Janeiro")
    criar_transacao(client, data="2026-03-01", descricao="Março")

    resposta = client.get("/transacoes?data_inicio=2026-02-01&data_fim=2026-04-01")
    assert [t["descricao"] for t in resposta.json()] == ["Março"]


def test_filtrar_apenas_data_inicio(client):
    criar_transacao(client, data="2026-01-01", descricao="Janeiro")
    criar_transacao(client, data="2026-03-01", descricao="Março")

    resposta = client.get("/transacoes?data_inicio=2026-02-01")
    assert [t["descricao"] for t in resposta.json()] == ["Março"]


def test_filtrar_apenas_data_fim(client):
    criar_transacao(client, data="2026-01-01", descricao="Janeiro")
    criar_transacao(client, data="2026-03-01", descricao="Março")

    resposta = client.get("/transacoes?data_fim=2026-02-01")
    assert [t["descricao"] for t in resposta.json()] == ["Janeiro"]


def test_filtrar_por_faixa_de_valor(client):
    criar_transacao(client, valor=50, descricao="Barato")
    criar_transacao(client, valor=500, descricao="Caro")

    resposta = client.get("/transacoes?valor_min=100&valor_max=1000")
    assert [t["descricao"] for t in resposta.json()] == ["Caro"]


def test_filtrar_apenas_valor_min(client):
    criar_transacao(client, valor=50, descricao="Barato")
    criar_transacao(client, valor=500, descricao="Caro")

    resposta = client.get("/transacoes?valor_min=100")
    assert [t["descricao"] for t in resposta.json()] == ["Caro"]


def test_filtrar_apenas_valor_max(client):
    criar_transacao(client, valor=50, descricao="Barato")
    criar_transacao(client, valor=500, descricao="Caro")

    resposta = client.get("/transacoes?valor_max=100")
    assert [t["descricao"] for t in resposta.json()] == ["Barato"]


def test_filtros_combinados(client):
    categoria_id = criar_categoria(client, "alimentacao").json()["id"]
    criar_transacao(
        client, descricao="Mercado", data="2026-05-15", valor=200, categoria_id=categoria_id
    )
    criar_transacao(
        client, descricao="Mercado fora do periodo", data="2026-01-01", valor=200, categoria_id=categoria_id
    )
    criar_transacao(
        client, descricao="Mercado fora da faixa de valor", data="2026-05-15", valor=999, categoria_id=categoria_id
    )
    criar_transacao(
        client, descricao="Outra categoria", data="2026-05-15", valor=200
    )

    resposta = client.get(
        "/transacoes",
        params={
            "categoria": "alimentacao",
            "data_inicio": "2026-05-01",
            "data_fim": "2026-05-31",
            "valor_min": "100",
            "valor_max": "300",
        },
    )
    assert [t["descricao"] for t in resposta.json()] == ["Mercado"]


def test_filtro_periodo_invertido_422(client):
    resposta = client.get("/transacoes?data_inicio=2026-05-01&data_fim=2026-01-01")
    assert resposta.status_code == 422
    assert "erro" in resposta.json()


def test_filtro_valor_invertido_422(client):
    resposta = client.get("/transacoes?valor_min=1000&valor_max=100")
    assert resposta.status_code == 422
    assert "erro" in resposta.json()


def test_filtro_data_inicio_malformada_422(client):
    resposta = client.get("/transacoes?data_inicio=abcd")
    assert resposta.status_code == 422
    assert "erro" in resposta.json()


def test_filtro_valor_min_nao_numerico_422(client):
    resposta = client.get("/transacoes?valor_min=abc")
    assert resposta.status_code == 422
    assert "erro" in resposta.json()


# --- saldo e resumo ---


def test_saldo(client):
    criar_transacao(client, tipo="entrada", valor=1000)
    criar_transacao(client, tipo="saida", valor=300)

    resposta = client.get("/saldo")
    assert resposta.json() == {"entradas": 1000.0, "saidas": 300.0, "saldo": 700.0}


def test_resumo_mes_com_dados(client):
    categoria_id = criar_categoria(client, "alimentacao").json()["id"]
    criar_transacao(client, data="2026-08-05", tipo="entrada", valor=1000)
    criar_transacao(client, data="2026-08-10", tipo="saida", valor=150, categoria_id=categoria_id)
    criar_transacao(client, data="2026-07-01", tipo="saida", valor=999)  # fora do mês

    resposta = client.get("/resumo?mes=2026-08")
    corpo = resposta.json()
    assert corpo["entradas"] == 1000.0
    assert corpo["saidas"] == 150.0
    assert corpo["saldo"] == 850.0
    assert corpo["por_categoria"] == [{"categoria": "alimentacao", "total": 150.0}]


def test_resumo_mes_sem_dados(client):
    resposta = client.get("/resumo?mes=2026-12")
    assert resposta.json() == {
        "mes": "2026-12",
        "entradas": 0.0,
        "saidas": 0.0,
        "saldo": 0.0,
        "por_categoria": [],
    }


def test_resumo_mes_malformado_422(client):
    resposta = client.get("/resumo?mes=2026-13")
    assert resposta.status_code == 422
    assert "erro" in resposta.json()


# --- exportação CSV ---


def test_export_csv_retorna_csv_valido(client):
    criar_transacao(client, descricao="Aluguel", valor=1200, tipo="saida")
    criar_transacao(client, descricao="Salário", valor=3000, tipo="entrada")

    resposta = client.get("/export.csv")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("text/csv")

    linhas = list(csv.DictReader(io.StringIO(resposta.text)))
    assert len(linhas) == 2
    assert {"id", "data", "descricao", "valor", "tipo", "categoria_id"} == set(linhas[0].keys())
    descricoes = {linha["descricao"] for linha in linhas}
    assert descricoes == {"Aluguel", "Salário"}


def test_export_csv_aplica_filtro_de_categoria(client):
    categoria_id = criar_categoria(client, "mercado").json()["id"]
    criar_transacao(client, descricao="Compra no mercado", categoria_id=categoria_id)
    criar_transacao(client, descricao="Sem categoria")

    resposta = client.get(f"/export.csv?categoria=mercado")
    linhas = list(csv.DictReader(io.StringIO(resposta.text)))
    assert len(linhas) == 1
    assert linhas[0]["descricao"] == "Compra no mercado"


def test_export_csv_filtro_periodo_invertido_422(client):
    resposta = client.get("/export.csv?data_inicio=2026-05-10&data_fim=2026-01-01")
    assert resposta.status_code == 422
    assert "erro" in resposta.json()


# --- dashboard ---


def test_dashboard_raiz_e_rota_dedicada_servem_html(client):
    for caminho in ("/", "/dashboard"):
        resposta = client.get(caminho)
        assert resposta.status_code == 200
        assert resposta.headers["content-type"].startswith("text/html")
        assert "/saldo" in resposta.text
        assert "/resumo" in resposta.text
