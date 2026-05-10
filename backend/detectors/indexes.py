import psycopg2
from psycopg2 import extras

"""
PgGuardian — Auditoría de Índices

Módulo encargado de analizar pg_index y pg_stat_user_indexes 
para detectar índices duplicados, no usados o faltantes 
en llaves foráneas.

Incluye: 

"""

def check_missing_partial_indexes(conn):
    """
    Identifica columnas con un sesgo extremo de datos (un valor que domine >85%)
    en tablas grandes (mayor a 10k filas) que no cuentan con un índice parcial para optimizar las consultas de la minoría de datos
    """
    query = """
    SELECT 
        s.tablename AS table_name,
        s.attname AS column_name,
        c.reltuples::bigint AS estimated_rows,
        (s.most_common_vals::text::text[])[1] AS dominant_value,
 
        round( (s.most_common_freqs[1] * 100)::numeric, 2) AS percent_occurrence,
        s.n_distinct AS estimated_distinct

    FROM pg_stats s
    JOIN pg_class c 
        ON c.relname = s.tablename
    JOIN pg_namespace n 
        ON n.oid = c.relnamespace 
        AND n.nspname = s.schemaname

    WHERE 
        s.schemaname NOT LIKE 'pg_%%'
        AND s.schemaname <> 'information_schema'
 
        AND c.reltuples > 10000

        AND s.most_common_freqs IS NOT NULL
        AND array_length(s.most_common_freqs, 1) > 0

        AND s.most_common_freqs[1] > 0.85

        AND NOT EXISTS (
            SELECT 1 
            FROM pg_index i 
            WHERE i.indrelid = c.oid
              AND i.indpred IS NOT NULL
              AND pg_get_expr(i.indpred, i.indrelid) ILIKE '%%' || s.attname || '%%'
        )

    ORDER BY s.most_common_freqs[1] DESC;
    """

    missing_partial = []
    
    try:
        with conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            missing_partial = cur.fetchall()
    except Exception as e:
        print(f"Error al detectar oportunidades de índices parciales: {e}")
        raise e
    return missing_partial



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


# Función para detectar índices que no se han usado 
def check_unused_indexes(conn):
    """
    Identifica índices que consumen recursos pero no se utilizan.
    
    Analiza las estadísticas acumuladas desde el último reset de estadísticas
    o desde la creación de la base de datos.
    """
        
    query = """
    SELECT 
        relname AS table_name,
        indexrelname AS index_name,
        idx_scan,
        pg_size_pretty(pg_relation_size(indexrelid)) AS size
    FROM 
        pg_stat_user_indexes
    WHERE 
        idx_scan = 0 
        AND idx_tup_read = 0   
        AND idx_tup_fetch = 0  
        AND indexrelname NOT LIKE '%_pkey' 
    ORDER BY 
        pg_relation_size(indexrelid) DESC;
    """
    
    unused_indexes = []
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            unused_indexes = cur.fetchall()
            
    except Exception as e:
        print(f"Error en el detector de índices no usados: {e}")
        raise e
        
    return unused_indexes


def check_covering_index_candidates(conn):
    """
    Analiza pg_stat_statements para identificar SELECTs frecuentes que 
    podrían convertirse en Index-Only Scans mediante el uso de la cláusula INCLUDE.
    Requiere la extensión pg_stat_statements habilitada.
    """

    query = """
    SELECT 
        LEFT(query, 200) AS query_sample,
        calls AS total_executions,
        round(total_exec_time::numeric, 2) AS total_time_ms,
        round( (total_exec_time / NULLIF(calls, 0))::numeric, 2 ) AS avg_time_ms,
        
        temp_blks_written AS temp_blocks,
        CASE 
            WHEN (shared_blks_hit + shared_blks_read) > 0 
                THEN round(
                    100.0 * shared_blks_hit / (shared_blks_hit + shared_blks_read), 2
                )
            ELSE 100 
        END AS cache_hit_pct
 
    FROM pg_stat_statements
 
    WHERE 
        query ILIKE 'SELECT%%'
        AND query ~ 'WHERE\\s+\\S+\\s*=\\s*\\$[0-9]'
        AND query NOT ILIKE 'SELECT *%%'
        AND query NOT ILIKE 'SELECT count(*)%%'
        AND calls >= 5
        AND query NOT ILIKE '%%pg_stat%%'
        AND query NOT ILIKE '%%pg_class%%'
        AND query NOT ILIKE '%%pg_index%%'
        AND query NOT ILIKE '%%information_schema%%'
 
    ORDER BY total_exec_time DESC
    LIMIT 15;
"""
    covering_candidates = []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            covering_candidates = cur.fetchall()
    
    except Exception as e:
        print(f"Error en el detector de Covering Indexes: {e}")
        raise e
    return covering_candidates


def check_obsolete_stats(conn):
    """
    Identifica tablas donde la estimación del Planner (pg_class) difiere 
    significativamente del conteo del recolector de estadísticas (pg_stat_user_tables).
    Detecta divergencias que causan planes de ejecución subóptimos.
    """

    query = """
    WITH stats_completions AS (
        SELECT
            psu.schemaname AS schema_name,
            psu.relname AS table_name,
            c.reltuples::bigint AS planner_estimate, 
            psu.n_live_tup AS stats_live_tuples,
            CASE
                WHEN psu.n_live_tup > 0 AND c.reltuples > 0 
                    THEN round (
                         
                        GREATEST(c.reltuples, psu.n_live_tup)::numeric / 
                        LEAST(c.reltuples, psu.n_live_tup)::numeric, 2)
                ELSE NULL
            END AS divergence_ratio
        FROM pg_stat_user_tables psu
        JOIN pg_class c ON c.relname = psu.relname
        JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = psu.schemaname
        WHERE n.nspname NOT LIKE 'pg_%%' 
        AND c.relkind = 'r' 
    )   
    SELECT *,
        CASE 
            WHEN divergence_ratio > 10 THEN 'CRITICAL'
            WHEN divergence_ratio > 5 THEN 'WARNING'
            ELSE 'OK'
        END AS stats_severity
    FROM stats_completions
    WHERE (divergence_ratio > 5) OR (planner_estimate = 0 AND stats_live_tuples > 100) 
    ORDER BY divergence_ratio DESC NULLS LAST;
    """
    obsolete_stats = []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            obsolete_stats = cur.fetchall()
    
    except Exception as e:
        print(f"Error en el detector de Obsolete Stats: {e}")
        raise e
    return obsolete_stats


def check_leading_wildcard_searches(conn):
    """
    Detecta el uso de LIKE/ILIKE con wildcard al inicio (%%texto%%).
    Estas consultas invalidan los indices B-Tree y fuerzan Sequential Scans,
    impactando severamente el I/O del servidor.
    """
    
    # usamos %% para escapar el simbolo % de cara a psycopg2
    # también \\\\s para que el backslash llegue integro al motor de regex de postgres
    query = """
    SELECT
        LEFT(pss.query, 250) AS query_sample,
        pss.calls AS total_executions,
        round(pss.total_exec_time::numeric, 2) AS total_time_ms,
        round((pss.total_exec_time / NULLIF(pss.calls, 0))::numeric, 2) AS avg_ms,

        CASE
            WHEN pss.query ~* 'LIKE\\\\s+''%%[^'']++%%'''
                THEN 'LIKE con wildcard inicial: LIKE %%texto%% (sensible)'
            WHEN pss.query ~* 'ILIKE\\\\s+''%%[^'']++%%'''
                THEN 'ILIKE con wildcard inicial: ILIKE %%texto%% (insensible)'
            ELSE 'Patron LIKE/ILIKE ineficiente detectado'
        END AS anti_pattern_type,

        CASE
            WHEN pss.calls > 100 AND (pss.total_exec_time / NULLIF(pss.calls, 0)) > 500
                THEN 'HIGH'
            WHEN pss.calls > 50 OR (pss.total_exec_time / NULLIF(pss.calls, 0)) > 1000
                THEN 'MEDIUM'
            ELSE 'LOW'
        END AS severity

    FROM pg_stat_statements pss

    WHERE
        (pss.query ~* 'LIKE\\\\s+''%%[^'']++%%''' OR pss.query ~* 'ILIKE\\\\s+''%%[^'']++%%''')
        AND pss.calls >= 2
        AND pss.query NOT ILIKE '%%pg_%%'
        AND pss.query NOT ILIKE '%%information_schema%%'

    ORDER BY pss.total_exec_time DESC
    LIMIT 15;
    """
    
    results = []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            results = cur.fetchall()
    except Exception as e:
        # En caso de error, mostramos el H-ID para facilitar el debug
        print(f"Error en detector de Wildcards: {e}")
        raise e
        
    return results