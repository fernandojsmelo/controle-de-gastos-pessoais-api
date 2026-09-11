import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).resolve().parent.parent / "gastos.db"))


class ErroDominio(Exception):
    def __init__(self, mensagem: str):
        self.mensagem = mensagem
        super().__init__(mensagem)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def reais_para_centavos(valor: float) -> int:
    return round(valor * 100)


def centavos_para_reais(centavos: int) -> float:
    return round(centavos / 100, 2)


def _com_valor_em_reais(row: sqlite3.Row) -> dict:
    transacao = dict(row)
    transacao["valor"] = centavos_para_reais(transacao["valor"])
    return transacao


def init_db() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            categoria_id INTEGER REFERENCES categorias(id)
        )
        """
    )
    colunas = {row["name"] for row in conn.execute("PRAGMA table_info(transacoes)")}
    if "categoria_id" not in colunas:
        conn.execute("ALTER TABLE transacoes ADD COLUMN categoria_id INTEGER REFERENCES categorias(id)")

    # Migração única: bancos criados antes desta mudança guardavam `valor` em
    # reais (float). A partir daqui, `valor` guarda centavos (inteiro) para
    # eliminar erro de arredondamento de ponto flutuante acumulado nas somas
    # de saldo/resumo.
    versao = conn.execute("PRAGMA user_version").fetchone()[0]
    if versao == 0:
        conn.execute("UPDATE transacoes SET valor = CAST(ROUND(valor * 100) AS INTEGER)")
        conn.execute("PRAGMA user_version = 1")

    conn.commit()
    conn.close()


def criar_categoria(nome: str) -> dict:
    conn = get_connection()
    try:
        cursor = conn.execute("INSERT INTO categorias (nome) VALUES (?)", (nome,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ErroDominio(f"Categoria '{nome}' já existe")
    categoria_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM categorias WHERE id = ?", (categoria_id,)).fetchone()
    conn.close()
    return dict(row)


def listar_categorias() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categorias ORDER BY nome").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def buscar_categoria_por_nome(nome: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM categorias WHERE nome = ?", (nome,)).fetchone()
    conn.close()
    return dict(row) if row else None


def atualizar_categoria(id: int, nome: str) -> dict | None:
    conn = get_connection()
    try:
        cursor = conn.execute("UPDATE categorias SET nome = ? WHERE id = ?", (nome, id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ErroDominio(f"Categoria '{nome}' já existe")
    if cursor.rowcount == 0:
        conn.close()
        return None
    row = conn.execute("SELECT * FROM categorias WHERE id = ?", (id,)).fetchone()
    conn.close()
    return dict(row)


def remover_categoria(id: int) -> bool:
    conn = get_connection()
    em_uso = conn.execute("SELECT 1 FROM transacoes WHERE categoria_id = ? LIMIT 1", (id,)).fetchone()
    if em_uso is not None:
        conn.close()
        raise ErroDominio("Categoria em uso, não pode ser removida")
    cursor = conn.execute("DELETE FROM categorias WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def criar_transacao(
    data: str, descricao: str, valor: float, tipo: str, categoria_id: int | None = None
) -> dict:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO transacoes (data, descricao, valor, tipo, categoria_id) VALUES (?, ?, ?, ?, ?)",
            (data, descricao, reais_para_centavos(valor), tipo, categoria_id),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ErroDominio(f"categoria_id {categoria_id} não existe")
    transacao_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM transacoes WHERE id = ?", (transacao_id,)).fetchone()
    conn.close()
    return _com_valor_em_reais(row)


def listar_transacoes(
    categoria_id: int | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    valor_min: float | None = None,
    valor_max: float | None = None,
    limite: int | None = None,
    offset: int | None = None,
) -> list[dict]:
    condicoes = []
    parametros: list = []
    if categoria_id is not None:
        condicoes.append("categoria_id = ?")
        parametros.append(categoria_id)
    if data_inicio is not None:
        condicoes.append("data >= ?")
        parametros.append(data_inicio)
    if data_fim is not None:
        condicoes.append("data <= ?")
        parametros.append(data_fim)
    if valor_min is not None:
        condicoes.append("valor >= ?")
        parametros.append(reais_para_centavos(valor_min))
    if valor_max is not None:
        condicoes.append("valor <= ?")
        parametros.append(reais_para_centavos(valor_max))

    query = "SELECT * FROM transacoes"
    if condicoes:
        query += " WHERE " + " AND ".join(condicoes)
    query += " ORDER BY data DESC, id DESC"
    if limite is not None:
        query += " LIMIT ?"
        parametros.append(limite)
        if offset is not None:
            query += " OFFSET ?"
            parametros.append(offset)

    conn = get_connection()
    rows = conn.execute(query, parametros).fetchall()
    conn.close()
    return [_com_valor_em_reais(row) for row in rows]


def atualizar_transacao(
    id: int, data: str, descricao: str, valor: float, tipo: str, categoria_id: int | None = None
) -> dict | None:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE transacoes SET data = ?, descricao = ?, valor = ?, tipo = ?, categoria_id = ? WHERE id = ?",
            (data, descricao, reais_para_centavos(valor), tipo, categoria_id, id),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ErroDominio(f"categoria_id {categoria_id} não existe")
    if cursor.rowcount == 0:
        conn.close()
        return None
    row = conn.execute("SELECT * FROM transacoes WHERE id = ?", (id,)).fetchone()
    conn.close()
    return _com_valor_em_reais(row)


def remover_transacao(id: int) -> bool:
    conn = get_connection()
    cursor = conn.execute("DELETE FROM transacoes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def calcular_saldo() -> tuple[float, float]:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN valor ELSE 0 END), 0) AS entradas,
            COALESCE(SUM(CASE WHEN tipo = 'saida' THEN valor ELSE 0 END), 0) AS saidas
        FROM transacoes
        """
    ).fetchone()
    conn.close()
    return centavos_para_reais(row["entradas"]), centavos_para_reais(row["saidas"])


def calcular_totais_mes(mes: str) -> tuple[float, float]:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN valor ELSE 0 END), 0) AS entradas,
            COALESCE(SUM(CASE WHEN tipo = 'saida' THEN valor ELSE 0 END), 0) AS saidas
        FROM transacoes
        WHERE substr(data, 1, 7) = ?
        """,
        (mes,),
    ).fetchone()
    conn.close()
    return centavos_para_reais(row["entradas"]), centavos_para_reais(row["saidas"])


def resumo_por_categoria(mes: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT c.nome AS categoria, SUM(t.valor) AS total
        FROM transacoes t
        JOIN categorias c ON c.id = t.categoria_id
        WHERE substr(t.data, 1, 7) = ? AND t.tipo = 'saida'
        GROUP BY c.nome
        ORDER BY total DESC
        """,
        (mes,),
    ).fetchall()
    conn.close()
    return [{"categoria": row["categoria"], "total": centavos_para_reais(row["total"])} for row in rows]
