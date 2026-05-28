import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'kappta.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
    conn.close()

init_db()
print("Base de datos SQLite creada correctamente")