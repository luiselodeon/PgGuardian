"""
PgGuardian — Detectores de Configuración PostgreSQL

Módulo encargado de analizar configuraciones críticas del servidor
relacionadas con rendimiento y uso de memoria.

Incluye:
- Detección de work_mem bajo
- Evaluación de uso de archivos temporales
- Validación de configuración contra workload observado
- Generación de hallazgos y recomendaciones

"""

# Valor mínimo utilizado como referencia inicial para work_mem (16 MB)
MIN_WORK_MEM_KB = 16384


# PostgreSQL utiliza work_mem como límite base para operaciones de sort y hash antes de comenzar a escribir archivos temporales en disco.
def get_work_mem(conn):
    """
    Consulta el valor actual de work_mem desde pg_settings.
    """

    sql = """
    SELECT name, setting, unit
    FROM pg_settings
    WHERE name = 'work_mem';
    """

    try:

        # Ejecutar consulta
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchone()

    except Exception as error:
        print(f"Error al consultar work_mem: {error}")
        return None


# Validar si work_mem tiene un valor bajo
def evaluate_work_mem(conn):
    """
    Evalúa si work_mem podría ser insuficiente para el workload
    y operaciones de sort/hash.
    """

    result = get_work_mem(conn)

    # Si no hubo resultado se termina la validación
    if not result:
        return None

    name, setting, unit = result

    # Conversión inicial del valor obtenido
    work_mem_kb = int(setting)

    # 16384 kB = 16 MB
    # Este valor se toma como referencia inicial para marcar una configuración potencialmente baja.
    if unit == "kB" and work_mem_kb < MIN_WORK_MEM_KB:

        finding = {
            "category": "Configuración",
            "title": "work_mem bajo",
            "severity": "MEDIUM",
            "evidence": f"work_mem actual: {work_mem_kb} {unit}",
            "recommendation": (
                "Evaluar aumentar work_mem de forma controlada, "
                "ya que operaciones como ORDER BY, GROUP BY, DISTINCT "
                "o Hash Join pueden escribir archivos temporales "
                "si no caben completamente en memoria."
            ),
            "sql_fix": "ALTER SYSTEM SET work_mem = '64MB';"
        }

        return finding

    return None


# Referencia PostgreSQL: https://www.postgresql.org/docs/current/runtime-config-resource.html

def check_pg_stat_statements_limit(conn):
    """
    Verifica si el limite de tracking de queries es suficiente.
    Si pg_stat_statements.max es muy bajo, se pierden metricas por 'eviction'.
    Este parametro requiere reinicio del servidor para surtir efecto.
    """
    query = """
    SELECT
        'pg_stat_statements.max' AS parameter,
        s.setting AS configured_value,
        EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements') AS extension_loaded,
        'pg_stat_statements.max controla cuantas queries unicas son trackeadas. '
        || 'Valores < 1000 causan eviction frecuente y perdida de visibilidad '
        || 'sobre el workload real de la base de datos.' AS description,
        'Subir a 5000-10000. Cambio requiere reinicio del servidor.' AS recommendation,
        '-- En postgresql.conf:' || chr(10)
        || 'pg_stat_statements.max = 5000' || chr(10)
        || '-- Reiniciar PostgreSQL despues del cambio' AS suggested_action,
        'pg_stat_statements.max muy bajo (tracking insuficiente)' AS finding_id,
        CASE
            WHEN s.setting::int < 500 THEN 'MEDIUM'
            ELSE 'LOW'
        END AS severity
    FROM pg_settings s
    WHERE s.name = 'pg_stat_statements.max'
      AND s.setting::int < 1000
      AND EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements');
    """
    results = []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            results = cur.fetchall()
    except Exception as e:
        print(f"Error en detector Pg Statement Limit: {e}")
        raise e
    return results


def check_slow_query_logging(conn):
    """
    Verifica si el registro de consultas lentas está habilitado

    Si log_min_duration_statement es -1, PostgreSQL no registra ninguna
    consulta por su duración, dificultando el diagnóstico de rendimiento.
    """
    slow_query_logging = []

    sql = """
    SELECT name, setting, unit, short_desc 
    FROM pg_settings 
    WHERE name = 'log_min_duration_statement';
    """

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            config = cur.fetchone()

            if config and config['setting'] == '-1':
                slow_query_logging.append({
                    "category": "Configuración de Servidor",
                    "title": "Registro de queries lentas desactivado",
                    "severity": "MEDIUM",
                    "evidence": f"El parámetro '{config['name']}' tiene el valor de '{config['setting']}'.",
                    "recommendation": (
                        "Establecer 'log_min_duration_statement' en 1000ms"
                    ),
                    "sql_fix": "ALTER SYSTEM SET log_min_duration_statement = '1000ms'; SELECT pg_reload_conf();"
                })

    except Exception as e:
        print(f"Error al verificar configuración de logs: {e}")

    return slow_query_logging