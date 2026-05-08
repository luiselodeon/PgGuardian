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