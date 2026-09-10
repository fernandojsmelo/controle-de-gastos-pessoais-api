import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "gastos.db"


class ErroDominio(Exception):
    def __init__(self, mensagem: str):
        self.mensagem = mensagem
        super().__init__(mensagem)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


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
            valor REAL NOT NULL,
            tipo TEXT NOT NULL,
            categoria_id INTEGER REFERENCES categorias(id)
        )
        """
    )
    colunas = {row["name"] for row in conn.execute("PRAGMA table_info(transacoes)")}
    if "categoria_id" not in colunas:
        conn.execute("ALTER TABLE transacoes ADD COLUMN categoria_id INTEGER REFERENCES categorias(id)")
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


def criar_transacao(
    data: str, descricao: str, valor: float, tipo: str, categoria_id: int | None = None
) -> dict:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO transacoes (data, descricao, valor, tipo, categoria_id) VALUES (?, ?, ?, ?, ?)",
            (data, descricao, valor, tipo, categoria_id),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ErroDominio(f"categoria_id {categoria_id} não existe")
    transacao_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM transacoes WHERE id = ?", (transacao_id,)).fetchone()
    conn.close()
    return dict(row)


def listar_transacoes(categoria_id: int | None = None) -> list[dict]:
    conn = get_connection()
    if categoria_id is None:
        rows = conn.execute("SELECT * FROM transacoes ORDER BY data DESC, id DESC").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM transacoes WHERE categoria_id = ? ORDER BY data DESC, id DESC",
            (categoria_id,),
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def atualizar_transacao(
    id: int, data: str, descricao: str, valor: float, tipo: str, categoria_id: int | None = None
) -> dict | None:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE transacoes SET data = ?, descricao = ?, valor = ?, tipo = ?, categoria_id = ? WHERE id = ?",
            (data, descricao, valor, tipo, categoria_id, id),
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
    return dict(row)


def remover_transacao(id: int) -> bool:
    conn = get_connection()
    cursor = conn.execute("DELETE FROM transacoes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0
