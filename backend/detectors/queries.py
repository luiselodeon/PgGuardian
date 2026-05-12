"""
PgGuardian — Detectores de Queries Problemáticas

Módulo encargado de analizar consultas con impacto negativo en rendimiento mediante métricas de pg_stat_statements y uso de archivos temporales.

Incluye:
- Detección de queries con temp_blks_written
- Identificación de posibles sort spills
- Evaluación de operaciones de sort/hash con uso de disco
- Clasificación básica de severidad

Referencias:
https://www.postgresql.org/docs/current/pgstatstatements.html
https://www.postgresql.org/docs/current/sql-explain.html
https://www.postgresql.org/docs/current/monitoring-stats.html
https://klouddb.io/temporary-files-in-postgresql-steps-to-identify-and-fix-temp-file-issues/
https://www.mssqltips.com/sqlservertip/8295/postgresql-monitoring-with-pg-stat-statements/
"""

# Tamaño normal de bloque temporal en PostgreSQL (8 KB)
BLOCK_SIZE = 8192
# Umbrales iniciales para clasificar uso de archivos temporales
MEDIUM_TEMP_MB = 10
HIGH_TEMP_MB = 100
# Umbral inicial para detectar queries con tiempo acumulado alto
MIN_TOTAL_EXEC_TIME_MS = 1000


# Revisar si pg_stat_statements está habilitado
def check_pg_stat_statements(conn):
    """
    Verifica si pg_stat_statements está habilitado en la base de datos.
    """

    sql = """
    SELECT EXISTS (
        SELECT 1
        FROM pg_extension
        WHERE extname = 'pg_stat_statements'
    );
    """

    try:

        # Ejecutar consulta
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchone()[0] # True o False

    except Exception as error:
        print(f"Error al verificar pg_stat_statements: {error}")
        return False


# Convertir bloques temporales a MB
def temp_blocks_to_mb(temp_blocks):
    """
    Convierte bloques temporales a MB aproximados.
    """

    # temp_blks_written se reporta en bloques, por eso se multiplica por BLOCK_SIZE
    return round((temp_blocks * BLOCK_SIZE) / 1024 / 1024, 2)

# Obtener queries que escribieron datos temporales en disco
def get_temp_queries(conn):
    """
    Consulta las queries que tienen temp_blks_written mayor a cero.
    """

    sql = """
     SELECT query,
           calls,
           total_exec_time,
           mean_exec_time,
           temp_blks_read,
           temp_blks_written
    FROM pg_stat_statements
    WHERE temp_blks_written > 0
    ORDER BY temp_blks_written DESC
    LIMIT 5;
    """

    try:

        # Ejecutar consulta
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()  # Queries encontradas

    except Exception as error:
        print(f"No se pudieron consultar los bloques temporales: {error}")
        return []


# Clasificar el impacto según los MB escritos a disco (severidad aproximada del spill detectado)
def get_spill_severity(temp_mb):
    """
    Regresa una severidad simple según el tamaño del spill.
    """

    # Spill alto
    if temp_mb >= HIGH_TEMP_MB:
        return "HIGH"

    # Spill medio
    if temp_mb >= MEDIUM_TEMP_MB:
        return "MEDIUM"

    # Spill bajo
    return "LOW"


# Evaluar queries que pudieron hacer spill a disco (posibles operaciones de sort/hash que usaron disco)
def evaluate_temp_spills(conn):
    """
    Evalúa queries con posible uso de archivos temporales usando pg_stat_statements.
    """

    findings = []

    # Si pg_stat_statements no está habilitado no es posible revisar temp_blks_written
    if not check_pg_stat_statements(conn):

        findings.append({

            "category": "Queries problemáticas",
            "title": "pg_stat_statements no está habilitado",
            "severity": "LOW",
            "evidence": (
                "No se encontró la extensión pg_stat_statements."
            ),
            "recommendation": (
                "Habilitar pg_stat_statements para revisar queries"
                "lentas y uso de archivos temporales."
            ),
            "sql_fix": (
                "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
            )
        })

        return findings

    # Obtener queries con bloques temporales
    rows = get_temp_queries(conn)

    for query, calls, total_exec_time, mean_exec_time, temp_blks_read, temp_blks_written in rows:

        # Conversión aproximada de bloques temporales a MB, 
        temp_mb = temp_blocks_to_mb(temp_blks_written)

        findings.append({

            "category": "Queries problemáticas",
            "title": "Uso de archivos temporales detectado",
            "severity": get_spill_severity(temp_mb),
            "evidence": (
                f"La query escribió {temp_blks_written} bloques temporales, "
                f"aproximadamente {temp_mb} MB en disco."
            ),
            "recommendation": (
                "Revisar si la consulta usa ORDER BY, GROUP BY, DISTINCT, "
                "Merge Join o Hash Join. También revisar si work_mem es suficiente."
            ),
            "sql_fix": (
                "Revisar EXPLAIN ANALYZE antes de ajustar work_mem."
            ),
            # Limitar tamaño del query para evitar respuestas muy largas
            "query_sample": query[:300],
            "calls": calls,
            "total_exec_time": round(total_exec_time, 2),
            "mean_exec_time": round(mean_exec_time, 2),
            "temp_blks_read": temp_blks_read,
            "temp_blks_written": temp_blks_written
        })

    return findings
