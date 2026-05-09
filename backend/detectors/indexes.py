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
 
        round( (s.most_common_freqs[1] * 100)::numeric, 2) AS percent_occurrence
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
