"""
PgGuardian — Detectores de Queries Problemáticas

Módulo encargado de analizar consultas con impacto negativo
en rendimiento mediante métricas de pg_stat_statements y
uso de archivos temporales.

Incluye:
- Detección de queries con temp_blks_written
- Identificación de posibles sort spills
- Evaluación de operaciones de sort/hash con uso de disco
- Clasificación básica de severidad

"""

import psycopg2.extras

# Tamaño normal de bloque temporal en PostgreSQL (8 KB)
BLOCK_SIZE = 8192


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
            return cur.fetchone()[0]

    except Exception as error:
        print(f"Error al verificar pg_stat_statements: {error}")
        return False


# Obtener queries que escribieron datos temporales en disco
def get_temp_queries(conn):
    """
    Consulta las queries que tienen temp_blks_written mayor a cero.
    """

    sql = """
    SELECT query,
           calls,
           total_exec_time,
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
            return cur.fetchall()

    except Exception as error:
        print(f"No se pudieron consultar los bloques temporales: {error}")
        return []


# Clasificar el impacto según los MB escritos a disco (severidad aproximada del spill detectado)
def get_spill_severity(temp_mb):
    """
    Regresa una severidad simple según el tamaño del spill.
    """

    # Spill alto
    if temp_mb >= 100:
        return "HIGH"

    # Spill medio
    if temp_mb >= 10:
        return "MEDIUM"

    # Spill bajo
    return "LOW"


# Detectar queries que pudieron hacer spill a disco (posibles operaciones de sort/hash que usaron disco)
def detect_temp_spills(conn):
    """
    Detecta queries con posible uso de archivos temporales usando pg_stat_statements.
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

    for query, calls, total_exec_time, temp_blks_written in rows:

        # Conversión aproximada de bloques temporales a MB, 
        temp_mb = round(
            (temp_blks_written * BLOCK_SIZE) / 1024 / 1024, 2)

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
            "total_exec_time": total_exec_time
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
                                "calls": row['calls'] # Veces que se ha ejecutado el query
                            })
                            
                            break 
                except:
                    # En caso de que no hayan queries que no se permita explain se saltan 
                    continue
                    
    except Exception as e:
        print(f"Error al detectar Seq Scans en queries: {e}")
        
    return seq_scan_queries