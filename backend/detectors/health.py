"""
PgGuardian — Estado Operativo

Módulo encargado de monitorear pg_stat_activity para detectar transacciones 
inactivas persistentes (idle in transaction) 
y falta de políticas de retención.

Incluye: 
Detector de tablas candidatas a ser particionadas por si se llegase a cumplir alguna de las siguientes características:
No están particionadas
Tienen más de 100 000 inserts
Pesan más de 500 MB
No tienen una política de retención

"""
import psycopg2
from psycopg2 import extras

#Revisa tablas candidatas al particionamiento
def check_partitioning_candidates(conn):
    """
    Identifica tablas candidatas a ser particionadas debido a que no están particionadas,
    tienen un crecimiento significativo (más de 100 000 inserts), pesan más de 500 MB
    o no tienen una política de retención adecuada.

    Además, se prepara el esquema y la extensión pg_partman para la gestión de particiones.
    """

    # Query para crear el esquema e instalar la extensión de forma segura
    setup_query = """
    CREATE SCHEMA IF NOT EXISTS partman;
    CREATE EXTENSION IF NOT EXISTS pg_partman SCHEMA partman;
    """
    # Query que revisa si son candidatas o no
    query = """
    SELECT
        stat.schemaname,
        stat.relname AS table_name,
        pg_size_pretty(pg_total_relation_size(stat.relid)) AS total_table_size,
        pg_total_relation_size(stat.relid) / (1024*1024) AS size_mb,
        stat.n_tup_ins AS total_inserts_history,
        stat.n_tup_del AS total_deletes_history,
        -- Porcentaje de registros insertados que han sido eliminados
        CASE
            WHEN stat.n_tup_ins > 0 THEN ROUND((stat.n_tup_del::numeric / stat.n_tup_ins) * 100, 2)
            ELSE 0
        END AS delete_ratio_pct
    FROM pg_stat_user_tables stat
    JOIN pg_class c ON stat.relid = c.oid
    WHERE
        -- Tablas no particionadas
        c.relkind = 'r'
        OR c.relispartition = false

        -- Tablas con más de 100 000 inserts
        OR stat.n_tup_ins > 100000

        -- Tablas que pesen mas de 500 MB
        OR pg_total_relation_size(stat.relid) > 500 * 1024 * 1024

        -- Tablas sin politicas de retencion
        OR (
            stat.n_tup_ins = 0
            OR (stat.n_tup_del::numeric / stat.n_tup_ins) < 0.05
        )
    ORDER BY pg_total_relation_size(stat.relid) DESC;
    """

    partition_candidates = []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Creamos el schema e instalamos la extensión
            cur.execute(setup_query)

            # Query principal
            cur.execute(query)
            partition_candidates = cur.fetchall()

    except Exception as e:
        print(f"Error al analizar los candidatos a particionamiento: {e}")
        raise e

    return partition_candidates
