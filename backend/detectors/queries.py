import re
"""
PgGuardian — Detectores de Queries Problemáticas

Módulo encargado de analizar consultas con impacto negativo en rendimiento mediante métricas de pg_stat_statements y uso de archivos temporales.

Incluye:
- Detección de queries con temp_blks_written
- Identificación de posibles sort spills
- Evaluación de operaciones de sort/hash con uso de disco
- Clasificación básica de severidad

"""

import psycopg2.extras

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
                "Habilitar pg_stat_statements para revisar queries "
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

        # Evitar reportar spills demasiado pequeños
        if temp_mb < 1:
            continue

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
                "Revisar EXPLAIN (ANALYZE, BUFFERS) antes de ajustar work_mem."
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

# Obtener queries con mayor tiempo total de ejecución
def get_top_time_queries(conn):
    """
    Consulta queries con alto total_exec_time desde pg_stat_statements.
    """

    sql = """
    SELECT query,
           calls,
           total_exec_time,
           mean_exec_time,
           rows
    FROM pg_stat_statements
    WHERE total_exec_time >= %s
    ORDER BY total_exec_time DESC
    LIMIT 5;
    """

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (MIN_TOTAL_EXEC_TIME_MS,))
            return cur.fetchall()

    except Exception as error:
        print(f"No se pudieron consultar queries por tiempo total: {error}")
        return []


# Evaluar queries con tiempo acumulado alto
def evaluate_top_time_queries(conn):
    """
    Evalúa queries que consumen mucho tiempo total de ejecución.
    """

    findings = []

    # Esta revisión depende de pg_stat_statements
    if not check_pg_stat_statements(conn):
        return findings

    rows = get_top_time_queries(conn)

    for query, calls, total_exec_time, mean_exec_time, rows_returned in rows:

        findings.append({
            "category": "Queries problemáticas",
            "title": "Query con alto tiempo total",
            "severity": "MEDIUM",
            "evidence": (
                f"total_exec_time: {round(total_exec_time, 2)} ms, "
                f"calls: {calls}, mean_exec_time: {round(mean_exec_time, 2)} ms."
            ),
            "recommendation": (
                "Revisar el plan de ejecución de esta consulta. "
                "Puede ser una query frecuente, pesada o con oportunidad de optimización."
            ),
            "sql_fix": (
                "EXPLAIN (ANALYZE, BUFFERS) <query>;"
            ),
            "query_sample": query[:300],
            "rows": rows_returned
        })

    return findings

# Obtener uso de archivos temporales a nivel base de datos
def get_database_temp_usage(conn):
    """
    Consulta temp_files y temp_bytes desde pg_stat_database.
    """
    # temp_files y temp_bytes son contadores acumulados desde el último reset de estadísticas
    sql = """
    SELECT datname,
           temp_files,
           temp_bytes
    FROM pg_stat_database
    WHERE datname = current_database()
      AND temp_files > 0
    ORDER BY temp_bytes DESC;
    """

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

    except Exception as error:
        print(f"No se pudo consultar pg_stat_database: {error}")
        return []


# Evaluar uso de archivos temporales a nivel base de datos
def evaluate_database_temp_usage(conn):
    """
    Evalúa si la base de datos ha generado archivos temporales.
    """

    findings = []

    rows = get_database_temp_usage(conn)

    for datname, temp_files, temp_bytes in rows:

        # Convertir bytes temporales a MB
        temp_mb = round(temp_bytes / 1024 / 1024, 2)

        findings.append({
            "category": "Queries problemáticas",
            "title": "Uso de archivos temporales en la base de datos",
            "severity": get_spill_severity(temp_mb),
            "evidence": (
                f"La base {datname} generó {temp_files} archivos temporales "
                f"con un tamaño aproximado de {temp_mb} MB."
            ),
            "recommendation": (
                "Revisar queries con ORDER BY, GROUP BY, DISTINCT, joins pesados "
                "o configuraciones de memoria como work_mem."
            ),
            "sql_fix": (
                "Revisar pg_stat_statements y logs temporales para ubicar "
                "las queries específicas."
            )
        })

    return findings

# Ejecutar todos los detectores de queries problemáticas
def run_query_checks(conn):
    """
    Ejecuta las revisiones de queries problemáticas y regresa
    los hallazgos encontrados.
    """

    findings = []

    # Lista de validaciones configuradas actualmente
    checks = [
        evaluate_temp_spills,
        evaluate_top_time_queries,
        evaluate_database_temp_usage
    ]

    # Ejecutar cada detector y agregar hallazgos encontrados
    for check in checks:
        findings.extend(check(conn))

    return findings

# Obtener el valor máximo de Batches dentro del plan
def get_max_batches(plan_text):
    """
    Busca valores de Batches en el plan y regresa el mayor.
    Si no encuentra batches, regresa 0.
    """

    matches = re.findall(r"Batches:\s*(\d+)", plan_text)

    if not matches:
        return 0

    return max(int(value) for value in matches)

# Revisar EXPLAIN de una query específica
def evaluate_single_explain(conn, query):
    """
    Revisa el plan de una query buscando señales de sort/hash spill.
    Solo se recomienda para queries SELECT identificadas como lentas.
    """

    findings = []

    # Evitar ejecutar INSERT, UPDATE, DELETE u otras porque EXPLAIN ANALYZE sí ejecuta la query real
    if not query.strip().upper().startswith("SELECT"):
        return findings

    #Se configura statement_timeout antes de correr el plan, para evitar que una consulta pesada se quede ejecutando demasiado tiempo durante las pruebas
    try:
       with conn.cursor() as cur:

        # Limitar tiempo para evitar que EXPLAIN ANALYZE se quede ejecutando demasiado
        cur.execute("SET statement_timeout = '5s';")

        cur.execute(f"""
        EXPLAIN (ANALYZE, BUFFERS)
        {query}
        """)

        rows = cur.fetchall()

        # Regresar el timeout a su valor normal después de la prueba, con esto no deja afectada la conexión       
        cur.execute("RESET statement_timeout;")

    except Exception as error:
        print(f"No se pudo ejecutar EXPLAIN ANALYZE: {error}")
        conn.rollback() # Si hay error hace rollback y limpia el estado de la transaccion
        return findings

    # Convertir el plan a texto para buscar señales de spill
    plan_text = "\n".join(row[0] for row in rows)

    # Sort en disco: normalmente aparece como external merge y Disk
    if "Sort Method: external merge" in plan_text or "Disk:" in plan_text:

        findings.append({
            "category": "Queries problemáticas",
            "title": "Sort en disco detectado por EXPLAIN",
            "severity": "HIGH",
            "evidence": (
                "El plan de ejecución muestra uso de disco en una operación de sort."
            ),
            "recommendation": (
                "Revisar si la query usa ORDER BY, GROUP BY o DISTINCT. "
                "También validar si work_mem es suficiente antes de ajustarlo."
            ),
            "sql_fix": (
                "Revisar EXPLAIN (ANALYZE, BUFFERS) y evaluar work_mem."
            ),
            "query_sample": query[:300]
        })

    # Hash Join / Hash Aggregate con batches
    max_batches = get_max_batches(plan_text)

    # Batches: 1 puede ser normal
    # Solo se genera hallazgo cuando Batches es mayor a 1.
    if max_batches > 1:

        findings.append({
            "category": "Queries problemáticas",
            "title": "Hash con batches detectado por EXPLAIN",
            "severity": "HIGH",
            "evidence": (
                f"El plan contiene Batches: {max_batches}, lo que puede indicar "
                "que una operación Hash Join o Hash Aggregate fue dividida en lotes."
            ),
            "recommendation": (
                "Revisar operaciones Hash Join o Hash Aggregate. "
                "Si Batches es mayor a 1, puede indicar que la operación "
                "no cupo completamente en memoria."
            ),
            "sql_fix": (
                "Validar plan de ejecución y considerar ajuste controlado de work_mem."
            ),
            "query_sample": query[:300]
        })

    return findings


# Función para detectar funciones que estén usando Seq Scan
def detect_seq_scan_queries(conn):
    """
    Analiza las queries de pg_stat_statements que más tiempo toman (top 20)
    y reporta las que realizan Seq Scans.
    """
    seq_scan_queries = []
        
    sql_top = """
        SELECT query, calls, queryid 
        FROM pg_stat_statements 
        WHERE query NOT LIKE 'SELECT pg_%' AND query NOT LIKE 'EXPLAIN %'
        ORDER BY total_exec_time DESC LIMIT 20;
    """

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql_top)
            top_queries = cur.fetchall()

            for row in top_queries:
                try:
                    # Se ejecuta el plan de ejecución para la query que se está analizando actualmente
                    cur.execute(f"EXPLAIN {row['query']}")
                    plan = cur.fetchall()
                    
                    # Se busca en el plan de ejecución si es que hay un query que use Seq Scan
                    for plan_line in plan:
                        line = plan_line[0]
                        
                        # Aquí es donde se detecta Seq Scan en el plan de ejecución
                        if "Seq Scan on" in line:                            
                            # Esto hace que se pueda extraer el nombre de la tabla del query que se está analizando
                            table_match = line.split("on ")[1].split("  ")[0].strip()
                            
                            seq_scan_queries.append({
                                "title": f"Seq Scan detectado en tabla: {table_match} por el query {row['queryid']}",
                                "recommendation": f"Verificar si la tabla '{table_match}' requiere índices",
                                "query": row['query'][:200], # Muestra el query
                                "calls": row['calls'], # Veces que se ha ejecutado el query
                                "evidence": (
                                    f"El query (ID {row['queryid']}) realiza un Seq Scan sobre '{table_match}' "
                                    f"y ha sido ejecutado {row['calls']:,} veces. "
                                    f"Un Seq Scan en tablas grandes implica leer todas las filas sin usar índice."
                                ),
                                "sql_recommendation": (
                                    f"-- Analizar el plan de ejecución:\n"
                                    f"EXPLAIN (ANALYZE, BUFFERS) <query>;\n\n"
                                    f"-- Si la tabla '{table_match}' es grande, considerar un índice:\n"
                                    f"-- Reemplaza 'columna_filtro' con la columna usada en el WHERE\n"
                                    f"CREATE INDEX CONCURRENTLY idx_{table_match}_columna_filtro\n"
                                    f"    ON {table_match} (columna_filtro);\n\n"
                                    f"-- Actualizar estadísticas:\n"
                                    f"ANALYZE {table_match};"
                                ),
                            })
                            
                            break 
                except:
                    # En caso de que no hayan queries que no se permita explain se saltan 
                    continue
                    
    except Exception as e:
        print(f"Error al detectar Seq Scans en queries: {e}")
        
    return seq_scan_queries
# Evaluar spills desde EXPLAIN usando queries sospechosas
# Esta como validacion manual y no se grega a run?query porque EXPLAIN ANALYZE ejecuta la query real
def evaluate_explain_spills(conn):
    """
    Obtiene queries con alto total_exec_time y revisa su plan con EXPLAIN.
    """

    findings = []

    # Esta revisión depende de pg_stat_statements
    if not check_pg_stat_statements(conn):
        return findings

    # Se reutilizan las queries con mayor tiempo total
    rows = get_top_time_queries(conn)

    for query, calls, total_exec_time, mean_exec_time, rows_returned in rows:

        explain_findings = evaluate_single_explain(conn, query)

        for finding in explain_findings:
            finding["calls"] = calls
            finding["total_exec_time"] = round(total_exec_time, 2)
            finding["mean_exec_time"] = round(mean_exec_time, 2)
            finding["rows"] = rows_returned

        findings.extend(explain_findings)

    return findings