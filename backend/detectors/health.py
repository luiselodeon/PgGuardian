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
            rows = cur.fetchall()

        for row in rows:
            row = dict(row)
            schema = row.get('schemaname', '')
            table = row.get('table_name', '')
            size_mb = float(row.get('size_mb', 0))
            inserts = row.get('total_inserts_history', 0)
            delete_pct = float(row.get('delete_ratio_pct', 0))

            reasons = []
            if size_mb > 500:
                reasons.append(f"pesa {size_mb:.1f} MB (umbral: 500 MB)")
            if inserts > 100000:
                reasons.append(f"tiene {inserts:,} inserts históricos")
            if delete_pct < 5:
                reasons.append(f"ratio de eliminación bajo ({delete_pct:.1f}%), sin política de retención aparente")

            reason_str = "; ".join(reasons) if reasons else "es candidata por su crecimiento"
            row['evidence'] = (
                f"La tabla '{schema}.{table}' ({row.get('total_table_size', '')}) {reason_str}."
            )
            row['sql_recommendation'] = (
                f"-- Convertir a tabla particionada (ejemplo por rango de fecha):\n"
                f"CREATE TABLE {schema}.{table}_partitioned\n"
                f"    (LIKE {schema}.{table} INCLUDING ALL)\n"
                f"    PARTITION BY RANGE (created_at);\n\n"
                f"CREATE TABLE {schema}.{table}_2024\n"
                f"    PARTITION OF {schema}.{table}_partitioned\n"
                f"    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');"
            )
            partition_candidates.append(row)

    except Exception as e:
        print(f"Error al analizar los candidatos a particionamiento: {e}")
        raise e

    return partition_candidates


def check_idle_in_transaction(conn):
    """
    Detecta sesiones que estan en estado 'idle in transaction'.
    Estas sesiones bloquean la limpieza de tuples muertos y pueden
    causar problemas severos de rendimiento y bloat.
    """
    query = """
    SELECT 
        'pg_stat_activity' AS parameter,
        pid AS configured_value,
    
        -- Describe que PID está causando el bloqueo, su estado y cuánto tiempo lleva activo en minutos.
        'La conexión (PID ' || pid || ') está bloqueando recursos. '
        || 'Estado actual: ' || state
        || '. Tiempo activa/inactiva: '
        || ROUND(EXTRACT(EPOCH FROM (NOW() - state_change)) / 60, 2)
        || ' minutos.' AS description,
    
        -- Se recomienda terminar la conexión con ese PID.
        'Terminar la conexión con pg_terminate_backend(' || pid || ') '
        || 'o configurar idle_in_transaction_session_timeout.' AS recommendation,
    
        'Conexión de larga duración detectada' AS finding_id,
    
        -- Si el bloqueo lleva dos minutos activo, se determina como severidad alta.
        -- Si el bloqueo lleva un minuto activo, se clasifica como serveridad media.
        CASE
            WHEN state_change < NOW() - INTERVAL '2 minutes' THEN 'HIGH'
            WHEN state_change < NOW() - INTERVAL '1 minute' THEN 'MEDIUM'
        END AS severity,
        pid AS session_pid,
        state AS session_state,
        ROUND(EXTRACT(EPOCH FROM (NOW() - state_change)) / 60, 2) AS idle_minutes
    FROM pg_stat_activity 
    WHERE 
         -- Detecta transacciones olvidadas (IDLE) o consultas activas excesivamente largas.
        (state = 'idle in transaction' OR state = 'active')
        AND state_change < NOW() - INTERVAL '1 minute'
        AND pid <> pg_backend_pid()
        -- Filtro para sólo reportar si es el usuario de la tienda.
        AND usename = 'tienda_user';
    """
    results = []
    try:
        # Uso de RealDictCursor para que los resultados sean accesibles por nombre de columna
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

        for row in rows:
            row = dict(row)
            pid = row.get('session_pid', row.get('configured_value', '?'))
            state = row.get('session_state', 'desconocido')
            idle_min = row.get('idle_minutes', 0)

            row['evidence'] = (
                f"La sesión PID {pid} lleva {idle_min} minutos en estado '{state}', "
                f"bloqueando recursos de vacuuming y potencialmente otras transacciones."
            )
            row['sql_recommendation'] = (
                f"-- Opción 1: Terminar la sesión problemática\n"
                f"SELECT pg_terminate_backend({pid});\n\n"
                f"-- Opción 2: Prevenir futuras sesiones colgadas\n"
                f"ALTER SYSTEM SET idle_in_transaction_session_timeout = '5min';\n"
                f"SELECT pg_reload_conf();"
            )
            results.append(row)

    except Exception as e:
        print(f"Error en detector Idle in Transaction: {e}")
        raise e
    return results
