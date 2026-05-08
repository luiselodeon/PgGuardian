"""
PgGuardian — Auditoría de Índices

Módulo encargado de analizar pg_index y pg_stat_user_indexes 
para detectar índices duplicados, no usados o faltantes 
en llaves foráneas.

Incluye: 

"""

import psycopg2
from psycopg2 import extras


def check_missing_indexes(conn):
    """
    Detecta llaves foráneas que no tengan un índice asociado.
    """
    query = """
    SELECT 
        conname AS constraint_name,
        conrelid::regclass AS table_name,
        a.attname AS column_name,
        confrelid::regclass AS referenced_table
    FROM 
        pg_constraint c
    JOIN 
        pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
    LEFT JOIN 
        pg_index i ON i.indrelid = c.conrelid 
                   AND a.attnum = i.indkey[0]
    WHERE 
        c.contype = 'f' 
        AND i.indexrelid IS NULL;
    """
    
    missing_indexes = []
    
    try:
        # Se usa RealDictCursor para que el resultado para que devuelva 
        # el resultado como diccionarios
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            missing_indexes = cur.fetchall()
            
    except Exception as e:
        print(f"Error al consultar los índices faltantes: {e}")        
        raise e
        
    return missing_indexes