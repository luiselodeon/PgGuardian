"""
PgGuardian — Detectores de Configuración PostgreSQL

Módulo encargado de analizar configuraciones críticas del servidor relacionadas con rendimiento y uso de memoria.

Incluye:
- Detección de work_mem bajo
- Evaluación de uso de archivos temporales
- Validación de configuración contra workload observado
- Generación de hallazgos y recomendaciones

Nota:
La función setting_to_mb fue normalizada con apoyo de IA para que el detector pueda manejar mejor distintas unidades de memoria y quede más preparado si se prueba con otra base de datos o configuración.

Referencias:
https://www.postgresql.org/docs/current/view-pg-settings.html#:~:text=The%20view%20pg_settings%20provides%20access%20to%20run-time%20parameters,from%20SHOW%2C%20such%20as%20minimum%20and%20maximum%20values.
https://www.postgresql.org/docs/current/runtime-config-resource.html
https://www.postgresql.org/docs/current/pgstatstatements.html
https://www.postgresql.org/docs/current/runtime-config-logging.html
https://es.python-3.com/?p=21123
https://www.psycopg.org/docs/
"""

import psycopg2.extras

# Valores de referencia inicial para work_mem 
MIN_WORK_MEM_KB = 16384
MIN_WORK_MEM_MB = 16
MIN_SHARED_BUFFERS_MB = 256
MIN_PG_STAT_STATEMENTS = 1000

# Esta función se normalizó con ayuda de IA para convertir diferentes unidades de pg_settings a MB y no depender de una sola configuración.
def setting_to_mb(setting, unit):
    """
    Convierte valores de memoria de pg_settings a MB.
    """

    value = int(setting)

    # PostgreSQL puede devolver algunos parámetros en kB
    if unit == "kB":
        return value / 1024

    # Algunos parámetros pueden venir en bloques de 8kB
    if unit == "8kB":
        return (value * 8) / 1024

    # Si ya viene en MB
    if unit == "MB":
        return value

    # Fallback simple por si la unidad viene vacía u otra diferente
    return value



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
    Evalúa si work_mem podría ser insuficiente para el workload y operaciones de sort/hash.
    """
    result = get_work_mem(conn)

    if not result:
        return []

    name, setting, unit = result    # Obtener los valores regresados por pg_settings

    # Conversión del valor obtenido
    work_mem_mb = setting_to_mb(setting, unit) # Convertir el valor obtenido a MB para manejar una sola unidad

    
    if work_mem_mb < MIN_WORK_MEM_MB:   # Validar si work_mem está por debajo del valor mínimo definido
        return [{
            "category": "Configuración",
            "title": "work_mem bajo",
            "severity": "MEDIUM",
            "evidence": f"work_mem: {round(work_mem_mb, 2)} MB",
            "recommendation": (
                "Evaluar aumentar work_mem de forma controlada, ya que "
                "operaciones como ORDER BY, GROUP BY, DISTINCT o Hash Join "
                "pueden escribir archivos temporales si no caben en memoria."
            ),
            "sql_fix": "ALTER SYSTEM SET work_mem = '64MB';"
        }]
    return []
    
# shared_buffers funciona como cache principal de PostgreSQL
# solo se esta revisando si está demasiado bajo
def get_shared_buffers(conn):
    """
    Consulta el valor actual de shared_buffers desde pg_settings.
    """

    sql = """
    SELECT name, setting, unit
    FROM pg_settings
    WHERE name = 'shared_buffers';
    """

    try:
        with conn.cursor() as cur:   # Ejecutar consulta en PostgreSQL
            cur.execute(sql)
            return cur.fetchone()   # Regresar el primer resultado encontrado

    except Exception as error:
        print(f"Error al consultar shared_buffers: {error}")    # Mostrar error en caso de falla durante la consulta
        return None

# Validar si shared_buffers está bajo
def evaluate_shared_buffers(conn):
    """
    Evalúa si shared_buffers tiene un valor bajo.
    """

    result = get_shared_buffers(conn) # Obtener configuración actual de shared_buffers

    if not result:  # Si no hubo resultado se termina la validación
        return []

    name, setting, unit = result    # Obtener valores de pg_settings
    shared_buffers_mb = setting_to_mb(setting, unit) # Convertir valor obtenido a MB

    if shared_buffers_mb < MIN_SHARED_BUFFERS_MB:  # Validar si shared_buffers está por debajo del valor mínimo definido   

        return [{
            "category": "Configuración",
            "title": "shared_buffers bajo",
            "severity": "MEDIUM",
            "evidence": f"shared_buffers aproximado: {round(shared_buffers_mb, 2)} MB",
            "recommendation": (
                "Evaluar shared_buffers según la memoria disponible del servidor. "
                "Un valor muy bajo puede provocar más lecturas desde disco."
            ),
            "sql_fix": "ALTER SYSTEM SET shared_buffers = '256MB';"
        }]
 

# pg_stat_statements.max define cuántas queries diferentes se conservan
# Si es bajo, se puede perder visibilidad del workload
def get_pg_stat_statements_max(conn):
    """
    Consulta el valor actual de pg_stat_statements.max.
    """

    sql = """
    SELECT name, setting
    FROM pg_settings
    WHERE name = 'pg_stat_statements.max';
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchone()

    except Exception as error:
        print(f"Error al consultar pg_stat_statements.max: {error}")
        return None


# Validar si pg_stat_statements.max tiene un valor bajo
def evaluate_pg_stat_statements_max(conn):
    """
    Evalúa si pg_stat_statements.max podría ser insuficiente.
    """
    result = get_pg_stat_statements_max(conn) # Configuración actual
    if not result:
        return []

    name, setting = result  # Valores de pg_settings

    # Validar si el valor está por debajo del mínimo definido
    if int(setting) < MIN_PG_STAT_STATEMENTS:

        return [{

            "category": "Configuración",
            "title": "pg_stat_statements.max bajo",
            "severity": "MEDIUM",
            "evidence": (
                f"pg_stat_statements.max actual: {setting}"
            ),
            "recommendation": (
                "Aumentar este valor ayuda a conservar más historial "
                "de queries dentro de pg_stat_statements."
            ),
            "sql_fix": (
                "pg_stat_statements.max = 5000"
            )
        }]

    return []


# Si log_min_duration_statement está en -1,
# PostgreSQL no registra queries lentas.
# https://www.sqldat.com/es/ges/wul/1001017058.html#google_vignette
# https://rootfan.com/es/postgresql-sql-tuning/
def get_log_min_duration_statement(conn):
    """
    Consulta el valor actual de log_min_duration_statement.
    """

    sql = """
    SELECT name, setting
    FROM pg_settings
    WHERE name = 'log_min_duration_statement';
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchone()

    except Exception as error:
        print(f"Error al consultar log_min_duration_statement: {error}")
        return None


# Validar si el log de queries lentas está desactivado
def evaluate_log_min_duration_statement(conn):
    """
    Evalúa si el registro de queries lentas está desactivado.
    """
    result = get_log_min_duration_statement(conn)
    if not result:
        return []
    name, setting = result

    # Si el valor es -1, PostgreSQL no registra queries lentas
    if setting == "-1":

        return [{

            "category": "Configuración",
            "title": "log_min_duration_statement desactivado",
            "severity": "MEDIUM",
            "evidence": (
                "log_min_duration_statement está en -1"
            ),
            "recommendation": (
                "Activar el log de queries lentas ayuda a diagnosticar "
                "consultas problemáticas con más evidencia."
            ),
            "sql_fix": (
                "ALTER SYSTEM SET "
                "log_min_duration_statement = '1000';"
            )
        }]

    return []


# Ejecutar todos los detectores de configuración
def run_config_checks(conn):
    """
    Ejecuta las revisiones de configuración y regresa
    los hallazgos encontrados.
    """

    findings = []

    # Lista de validaciones configuradas actualmente
    checks = [
        evaluate_work_mem,
        evaluate_shared_buffers,
        evaluate_pg_stat_statements_max,
        evaluate_log_min_duration_statement
    ]

    # Ejecutar cada detector y agregar hallazgos encontrados
    for check in checks:
        findings.extend(check(conn))

    return findings   


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