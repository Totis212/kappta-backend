import sqlite3
import os
import json
import requests

TURSO_URL = os.environ.get("TURSO_URL", "")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")

def get_http_url():
    if TURSO_URL:
        return TURSO_URL.replace("libsql://", "https://")
    return ""

def get_connection():
    if TURSO_URL:
        return TursoConnection(get_http_url(), TURSO_AUTH_TOKEN)
    else:
        conn = sqlite3.connect("kappta.db")
        conn.row_factory = sqlite3.Row
        return conn

def sync_connection(conn):
    pass

class TursoRow:
    def __init__(self, values, columns):
        for i, col in enumerate(columns):
            setattr(self, col, values[i])
    
    def __getitem__(self, key):
        if isinstance(key, str):
            return getattr(self, key)
        return None
    
    def __repr__(self):
        return dict(self.__dict__).__repr__()

class TursoConnection:
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.results = []
        self.columns = []
    
    def cursor(self):
        return self
    
    def execute(self, sql, params=None):
        if params is None:
            params = []
        
        url = self.url + "/v2/pipeline"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        body = {
            "requests": [
                {
                    "type": "execute",
                    "stmt": {
                        "sql": sql,
                        "args": [{"type": "text", "value": str(p) if p is not None else None} for p in params]
                    }
                },
                {
                    "type": "close"
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code != 200:
            raise Exception(f"Turso error: {response.text}")
        
        data = response.json()
        
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            if "response" in result and "result" in result["response"]:
                res = result["response"]["result"]
                if "rows" in res and "cols" in res:
                    self.results = []
                    self.columns = [col["name"] for col in res["cols"]]
                    for row in res["rows"]:
                        values = []
                        for val in row:
                            if val is None:
                                values.append(None)
                            elif isinstance(val, dict) and "value" in val:
                                values.append(val["value"])
                            else:
                                values.append(val)
                        self.results.append(TursoRow(values, self.columns))
                else:
                    self.results = []
                    self.columns = []
            else:
                self.results = []
                self.columns = []
        else:
            self.results = []
            self.columns = []
    
    def fetchone(self):
        if self.results:
            row = self.results[0]
            self.results = self.results[1:]
            return row
        return None
    
    def fetchall(self):
        rows = self.results
        self.results = []
        return rows
    
    def commit(self):
        pass
    
    def close(self):
        pass
    
    @property  
    def lastrowid(self):
        if self.results:
            return None
        return None

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
print("Base de datos conectada a Turso via HTTP")