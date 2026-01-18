# database.py
import sqlite3
import hashlib

DB_NAME = 'loja_dados.db'


# --- SEGURANÇA ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False


# --- BANCO DE DADOS ---
def run_query(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute(query, params)
        if fetch:
            data = c.fetchall()
            return data
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro no Banco: {e}")
    finally:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Tabelas do Sistema
    c.execute(
        '''CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, preco REAL, quantidade INTEGER, minimo_alerta INTEGER DEFAULT 5)''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER, produto_nome TEXT, cliente_nome TEXT, qtd_vendida INTEGER, total REAL, valor_pago REAL DEFAULT 0, tipo_pagamento TEXT, data_venda DATE, data_recebimento DATE, status TEXT)''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, cpf TEXT, endereco TEXT)''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS caixa_movimentos (id INTEGER PRIMARY KEY AUTOINCREMENT, data DATE, tipo TEXT, descricao TEXT, valor REAL)''')

    # Tabela de Usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            nome_real TEXT,
            permissoes TEXT,
            mudar_senha INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

    # --- MIGRAÇÃO E CORREÇÃO (Onde estava o erro) ---
    try:
        run_query("ALTER TABLE usuarios ADD COLUMN nome_real TEXT")
    except:
        pass
    try:
        run_query("ALTER TABLE usuarios ADD COLUMN permissoes TEXT")
    except:
        pass
    try:
        run_query("ALTER TABLE usuarios ADD COLUMN mudar_senha INTEGER DEFAULT 0")
    except:
        pass

    # 1. Verifica se Admin existe
    users = run_query("SELECT * FROM usuarios WHERE username = 'admin'", fetch=True)

    if not users:
        # Se não existe, cria do zero
        senha_hash = make_hashes("123")
        run_query(
            "INSERT INTO usuarios (username, password, nome_real, permissoes, mudar_senha) VALUES (?, ?, ?, ?, ?)",
            ("admin", senha_hash, "Administrador", "admin", 0))
    else:
        # CORREÇÃO: Se já existe, FORÇA a permissão correta para garantir que não fique NULL
        run_query("UPDATE usuarios SET permissoes = 'admin', nome_real = 'Administrador' WHERE username = 'admin'")


def get_user_data(username):
    return run_query("SELECT password, nome_real, permissoes, mudar_senha FROM usuarios WHERE username = ?",
                     (username,), fetch=True)


def update_user_password(username, new_password):
    new_hash = make_hashes(new_password)
    run_query("UPDATE usuarios SET password = ?, mudar_senha = 0 WHERE username = ?", (new_hash, username))