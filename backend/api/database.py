"""
PgGuardian — Gestión de conexión a PostgreSQL

Provee un generador de conexiones psycopg2 para usar como
dependencia de FastAPI. Lee credenciales desde variables de entorno.
"""

import os
import psycopg2


def get_connection():
    """
    Generador que crea una conexión a PostgreSQL,
    la entrega al endpoint, y la cierra automáticamente al terminar.
    Hace rollback si ocurre un error.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "tiendadb"),
            user=os.getenv("DB_USER", "tienda_user"),
            password=os.getenv("DB_PASSWORD", "tienda_pass"),
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
        )
        # Autocommit para que los detectores que crean extensiones no fallen
        conn.autocommit = True
        yield conn
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()