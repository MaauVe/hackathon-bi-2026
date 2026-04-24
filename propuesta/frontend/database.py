import os
from sqlalchemy import create_engine
import pandas as pd
from dotenv import load_dotenv

# Buscar .env en la raíz (dos niveles arriba de este archivo)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "3306")
        db_name = os.getenv("DB_NAME")
        
        conn_str = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db_name}"
        _engine = create_engine(conn_str, pool_size=10, max_overflow=20)
    return _engine

def run_query(query):
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

def execute_statement(statement, params=None):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(statement, params)
