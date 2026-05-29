import libsql
import sqlite3
import os

TURSO_URL = os.environ.get("TURSO_URL", "")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")

def get_connection():
    if TURSO_URL:
        conn = libsql.connect("file:kappta.db", sync_url=TURSO_URL, auth_token=TURSO_AUTH_TOKEN)
        conn.sync()
    else:
        conn = libsql.connect("kappta.db")
    conn.row_factory = sqlite3.Row
    return conn

def sync_connection(conn):
    if TURSO_URL:
        conn.sync()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Usuarios (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT UNIQUE NOT NULL,
            Password TEXT NOT NULL,
            Nomina REAL DEFAULT 0,
            Periodo TEXT DEFAULT 'quincenal'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Categorias (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nombre TEXT NOT NULL,
            Presupuesto REAL DEFAULT 0,
            UsuarioId INTEGER,
            EsAhorro INTEGER DEFAULT 0,
            Seleccionada INTEGER DEFAULT 0,
            FOREIGN KEY (UsuarioId) REFERENCES Usuarios(Id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Gastos (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            CategoriaId INTEGER,
            Descripcion TEXT,
            Monto REAL,
            Fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            UsuarioId INTEGER,
            FOREIGN KEY (CategoriaId) REFERENCES Categorias(Id),
            FOREIGN KEY (UsuarioId) REFERENCES Usuarios(Id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Ahorro (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            UsuarioId INTEGER UNIQUE,
            Meta REAL DEFAULT 0,
            Acumulado REAL DEFAULT 0,
            FOREIGN KEY (UsuarioId) REFERENCES Usuarios(Id)
        )
    ''')

    conn.commit()
    sync_connection(conn)
    conn.close()

init_db()
print("Base de datos conectada a Turso")