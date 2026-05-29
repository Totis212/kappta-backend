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

def convert_arg(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return {"type": "integer", "value": "1" if value else "0"}
    if isinstance(value, int):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    return {"type": "text", "value": str(value)}

class TursoRow:
    def __init__(self, values, columns):
        for i, col in enumerate(columns):
            setattr(self, col, values[i])
    
    def __getitem__(self, key):
        if isinstance(key, str):
            return getattr(self, key, None)
        elif isinstance(key, int):
            cols = list(self.__dict__.keys())
            if key < len(cols):
                return getattr(self, cols[key])
        return None
    
    def __len__(self):
        return len(self.__dict__)

class TursoCursor:
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.results = []
        self.columns = []
        self._lastrowid = None
        self._rowcount = 0
    
    def execute(self, sql, params=None):
        if params is None:
            params = []
        
        api_url = self.url + "/v2/pipeline"
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
                        "args": [convert_arg(p) for p in params]
                    }
                },
                {
                    "type": "close"
                }
            ]
        }
        
        response = requests.post(api_url, headers=headers, json=body)
        
        if response.status_code != 200:
            raise Exception(f"Turso error: {response.text}")
        
        data = response.json()
        
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            if "response" in result and "result" in result["response"]:
                res = result["response"]["result"]
                self._rowcount = res.get("affected_row_count", 0)
                self._lastrowid = res.get("last_insert_rowid", None)
                if "rows" in res and "cols" in res:
                    self.columns = [col["name"] for col in res["cols"]]
                    self.results = []
                    for row in res["rows"]:
                        values = []
                        for val in row:
                            if val is None:
                                values.append(None)
                            elif isinstance(val, dict) and "value" in val:
                                v = val["value"]
                                t = val.get("type", "text")
                                if t == "integer" and v is not None:
                                    values.append(int(v))
                                elif t == "float" and v is not None:
                                    values.append(float(v))
                                else:
                                    values.append(v)
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
    
    @property
    def lastrowid(self):
        return self._lastrowid
    
    @property
    def rowcount(self):
        return self._rowcount
    
    def close(self):
        pass

class TursoConnection:
    def __init__(self, url, token):
        self.url = url
        self.token = token
    
    def cursor(self):
        return TursoCursor(self.url, self.token)
    
    def commit(self):
        pass
    
    def close(self):
        pass

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