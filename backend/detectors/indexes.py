"""
PgGuardian — Auditoría de Índices

Módulo encargado de analizar pg_index y pg_stat_user_indexes 
para detectar índices duplicados, no usados o faltantes 
en llaves foráneas.

Incluye: 

"""

import psycopg2
from psycopg2 import extras


# Función para detectar llaves foráneas sin índice
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


# Función para detectar índices duplicados
def check_duplicate_indexes(conn):
    """
    Identifica índices duplicados ignorando los esquemas de sistema de PostgreSQL.
    """
    query = """
    SELECT 
        indrelid::regclass AS table_name,
        array_to_string(array_agg(a.attname ORDER BY x.pos), ', ') AS columns,
        string_agg(i.relname, ', ') AS index_names,
        COUNT(*) AS count
    FROM (
        SELECT indrelid, indexrelid, indkey, generate_subscripts(indkey, 1) AS pos 
        FROM pg_index
    ) AS x
    JOIN pg_attribute a ON a.attrelid = x.indrelid AND a.attnum = x.indkey[x.pos]
    JOIN pg_class i ON i.oid = x.indexrelid
    JOIN pg_namespace n ON n.oid = i.relnamespace
    WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
    GROUP BY indrelid, indkey
    HAVING COUNT(*) > 1;
    """
    
    duplicate_indexes = []
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            duplicate_indexes = cur.fetchall()
            
    except Exception as e:
        print(f"Error al detectar índices duplicados: {e}")
        raise e
        
    return duplicate_indexes
