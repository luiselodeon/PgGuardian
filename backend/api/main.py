"""
PgGuardian — Backend FastAPI

API REST que expone los detectores de problemas de PostgreSQL como endpoints HTTP.

Por aquí definimos la lógica de la API 

- Importamos todas las funciones de detección del archivo detectors/
- Centralizamos los detectores en diccionario (DETECTORS_MENU), nuestros endpoint los toman de ahí

FLUJO DE INFO:
1. El cliente (frontend o curl) hace una petición HTTP a un endpoint de FastAPI (aquí).
2. FastAPI usa "get_connection()" para abrir una conexión a PostgreSQL.
3. Con esa conexión, se llama a "run_detector()" que ejecuta cada detector de forma aislada.
4. El resultado del detector pasa por "normalize_findings()", que lo
   convierte a un formato estandarizado list[dict].
5. Si es un escaneo completo, "calculate_health_score()" toma todos los
   hallazgos y asigna un puntaje de 0 a 100.
6. FastAPI empaqueta todo en un JSON (DetectorResponse o FullScanResponse)
   y lo devuelve al cliente. La conexión a Postgres se cierra automáticamente.


PROBAR
- cd backend/api
- pip install -r requirements.txt
- python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
Swagger UI: http://localhost:8001/docs

NOTA: Al agregar 2 endpoints nuevos, Swagger no los mostró,
se cambió el puerto a 8001 y se ejecutó de nuevo el comando de uvicorn.
"""

import sys, os
"""
main.py importa módulos de dos niveles:
- database, schemas de backend/api/
- detectors.* de backend/
Agregamos ambos al path para que Python los encuentre
"""
_API_DIR = os.path.dirname(os.path.abspath(__file__)) # apunta a este archivo (main.py)
_BACKEND_DIR = os.path.dirname(_API_DIR) # apunta a directorio /backend/
sys.path.insert(0, _API_DIR) # busca módulos en backend/api/
sys.path.insert(0, _BACKEND_DIR) # busca módulos en backend/

from datetime import datetime
from typing import Callable
 
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
 
# provee la conexión a Postgres como dependencia
from database import get_connection

# definen la estructura de las respuestas JSON
from schemas import DetectorResponse, FullScanResponse

"""
# IMPORTACIÓN DE DETECTORES
Cada detector es una función que recibe una conexión (conn) a Postgres,
ejecuta queries de diagnóstico y retorna los hallazgos.
"""
# Detectores de ÍNDICES
from detectors.indexes import (
    check_missing_indexes,              
    check_duplicate_indexes,            
    check_unused_indexes,               
    check_missing_partial_indexes,      
    check_covering_index_candidates,    
    check_obsolete_stats,               
    check_leading_wildcard_searches,    
)

# Detectores de CONFIG
from detectors.config import (
    evaluate_work_mem,    
    evaluate_shared_buffers, 
    evaluate_pg_stat_statements_max,
    evaluate_log_min_duration_statement,
    check_pg_stat_statements_limit,
    check_slow_query_logging,
)

# Detectores de BLOAT
from detectors.bloat import (
    check_table_bloat,                  
    check_disabled_autovacuum,          
    check_dead_tuples,                  
)



# Detectores de SALUD general
from detectors.health import (
    check_partitioning_candidates,
    check_idle_in_transaction,
)

# Detectores para QUERIES
from detectors.queries import (
    evaluate_temp_spills,
    evaluate_top_time_queries,
    evaluate_database_temp_usage,
    detect_seq_scan_queries,            
)
 
 
load_dotenv()

"""
Catálogo de detectores
este diccionario sirve para centralizar la información de los detectores, si se crean nuevos detectores, 
se implementan aqui y para que los endpoint los usen 
TODO: implementar los que faltan 
"""
DETECTORS_MENU: dict[str, dict] = {

#-------------------------------------------------------------------------
                            # DETECTORES EN ÍNDICES 
#-------------------------------------------------------------------------
    # check_missing_indexes
    "I1": {
        "nombre": "Llaves foráneas sin índice",
        "descripcion": "Detecta llaves foráneas que no tienen un índice asociado.",
        "category": "Índices",
        "function": check_missing_indexes,
        "severidad": "HIGH"
    },

    # check_missing_partial_indexes
    "I2":{
        "nombre": "Oportunidades de índices parciales",
        "descripcion": "Identifica columnas con un valor dominante (>85%%) en tablas grandes donde un índice parcial optimizaría las consultas.",
        "category": "Índices",
        "function": check_missing_partial_indexes,
        "severidad": "MEDIUM"
    },

    # check_duplicate_indexes
    "I3": {
        "nombre": "Índices duplicados",
        "descripcion": "Detecta índices duplicados ignorando los esquemas de sistema de PostgreSQL.",
        "category": "Índices",
        "function": check_duplicate_indexes,
        "severidad": "HIGH"
    },

    # check_unused_indexes
    "I4": {
        "nombre": "Índices sin usar",
        "descripcion": "Detecta índices que consumen recursos pero no se utilizan.",
        "category": "Índices",
        "function": check_unused_indexes,
        "severidad": "MEDIUM"
    },

    # check_covering_index_candidates
    "I5": {
        "nombre": "Candidatos a índices de cobertura",
        "descripcion": "Identifica SELECTs frecuentes que podrían convertirse en Index-Only Scans usando la cláusula INCLUDE.",
        "category": "Índices",
        "function": check_covering_index_candidates,
        "severidad": "LOW"
    },

    # check_obsolete_stats
    "I6": {
        "nombre": "Estadísticas obsoletas",
        "descripcion": "Detecta tablas donde la estimación del planificador difiere significativamente del conteo real, causando planes de ejecución subóptimos.",
        "category": "Índices",
        "function": check_obsolete_stats,
        "severidad": "MEDIUM"
    },

    # check_leading_wildcard_searches
    "I7": {
        "nombre": "Búsquedas LIKE/ILIKE con wildcard inicial",
        "descripcion": "Detecta consultas con patrones LIKE '%%texto%%' que invalidan índices B-Tree y fuerzan Sequential Scans.",
        "category": "Índices",
        "function": check_leading_wildcard_searches,
        "severidad": "HIGH"
    },

#-------------------------------------------------------------------------
                # DETECTORES EN CONFIGURACIÓN 
#-------------------------------------------------------------------------

    # evaluate_work_mem
    "C1": {
        "nombre": "work_mem insuficiente",
        "descripcion": "Evalúa si work_mem es demasiado bajo para operaciones de sort y hash, lo cual provoca escritura de archivos temporales en disco.",
        "category": "Configuración",
        "function": evaluate_work_mem,
        "severidad": "MEDIUM"
    },

    # evaluate_shared_buffers
    "C2": {
        "nombre": "shared_buffers insuficiente",
        "descripcion": "Evalúa si shared_buffers es demasiado bajo, lo cual provoca más lecturas directas desde disco.",
        "category": "Configuración",
        "function": evaluate_shared_buffers,
        "severidad": "MEDIUM"
    },

    # evaluate_pg_stat_statements_max
    "C3": {
        "nombre": "Detector de pg_stat_statements.max",
        "descripcion": "Evalúa si pg_stat_statements.max podría ser insuficiente.",
        "category": "Configuración",
        "function": evaluate_pg_stat_statements_max,
        "severidad": "MEDIUM"
    },

    # evaluate_log_min_duration_statement
    "C4": {
        "nombre": "Detector de log_min_duration_statement",
        "descripcion": "Evalúa si log_min_duration_statement está habilitado.",
        "category": "Configuración",
        "function": evaluate_log_min_duration_statement,
        "severidad": "MEDIUM"
    },

    # check_pg_stat_statements_limit
    "C5": {
        "nombre": "Tracking de queries insuficiente",
        "descripcion": "Verifica si pg_stat_statements_max es muy bajo (<1000), lo cual causa pérdida de métricas por eviction.",
        "category": "Configuración",
        "function": check_pg_stat_statements_limit,
        "severidad": "LOW"
    },

    # check_slow_query_logging
    "C6": {
        "nombre": "Registro de queries lentas desactivado",
        "descripcion": "Verifica si log_min_duration_statement está desactivado (-1), lo cual impide diagnosticar consultas problemáticas.",
        "category": "Configuración",
        "function": check_slow_query_logging,
        "severidad": "MEDIUM"
    },


#-------------------------------------------------------------------------
                        # DETECTORES DE BLOAT 
#-------------------------------------------------------------------------
    
    # check_table_bloat
    "B1":{
        "nombre": "Bloat en tablas",
        "descripcion": "Analiza el almacenamiento físico de tablas cuantificando el bloat y la fragmentación de datos.",
        "category": "Bloat",
        "function": check_table_bloat,
        "severidad": "HIGH"
    },

    # check_disabled_autovacuum
    "B2": {
        "nombre": "Autovacuum deshabilitado en tablas",
        "descripcion": "Detecta tablas donde autovacuum está deshabilitado.",
        "category": "Bloat",
        "function": check_disabled_autovacuum,
        "severidad": "HIGH"
    },

    # check_dead_tuples
    "B3": {
        "nombre": "Tuplas muertas en tablas",
        "descripcion": "Detecta tuplas muertas que podrían requerir vacuum o autovacuum.",
        "category": "Bloat",
        "function": check_dead_tuples,
        "severidad": "MEDIUM"
    },

#-------------------------------------------------------------------------
                        # DETECTORES DE SALUD 
#-------------------------------------------------------------------------

    # check_partitioning_candidates
    "H1":{
        "nombre": "Candidatos a particionamiento",
        "descripcion": "Detecta tablas grandes que podrían beneficiarse del particionamiento.",
        "category": "Salud",
        "function": check_partitioning_candidates,
        "severidad": "MEDIUM"
    },
    
    # check_idle_in_transaction
    "H2": {
        "nombre": "Transacciones inactivas (idle-in-transaction)",
        "descripcion": "Detecta transacciones que están abiertas sin hacer nada por mucho tiempo.",
        "category": "Salud",
        "function": check_idle_in_transaction,
        "severidad": "HIGH"
    },

#-------------------------------------------------------------------------
                        # DETECTORES DE QUERIES 
#-------------------------------------------------------------------------
    # evaluate_temp_spills
    "Q1":{
        "nombre": "Spill de archivos temporales por query",
        "descripcion": "Detecta queries que escribieron bloques temporales en disco, indicando que work_mem fue insuficiente para la operación.",
        "category": "Queries",
        "function": evaluate_temp_spills,
        "severidad": "MEDIUM"
    },
    # evaluate_top_time_queries
    "Q2":{
        "nombre": "Queries con alto tiempo de ejecución",
        "descripcion": "Identifica las queries con mayor tiempo total acumulado en pg_stat_statements, candidatas a optimización.",
        "category": "Queries",
        "function": evaluate_top_time_queries,
        "severidad": "MEDIUM"
    },
    # evaluate_database_temp_usage
    "Q3":{
        "nombre": "Uso de archivos temporales (nivel BD)",
        "descripcion": "Evalúa el uso acumulado de archivos temporales desde pg_stat_database para la base de datos actual.",
        "category": "Queries",
        "function": evaluate_database_temp_usage,
        "severidad": "MEDIUM"
    },
    # detect_seq_scan_queries
    "Q4":{
        "nombre": "Sequential Scans en queries",
        "descripcion": "Analiza las queries más costosas y reporta las que realizan escaneos secuenciales completos de tabla (Seq Scan).",
        "category": "Queries",
        "function": detect_seq_scan_queries,
        "severidad": "MEDIUM"
    }
}


# FUNCIONES AUXILIARES
def normalize_findings(raw_result)-> list[dict]:
    """
    Recibe el resultado de un detector y normaliza los tres casos a list[dict]
    
    Los posibles formatos que puede recibir:
    - None (sin hallazgos)
    - dict (un solo hallazgo)
    - list[dict] o list[RealDictRow] (hallazgos de RealDictCursor)
    - list[tuple] (varios hallazgos como namedtuples)
    """
    # Caso 1: sin hallazgos
    if raw_result is None:
        return []

    # Caso 2: un solo hallazgo como dict
    if isinstance(raw_result, dict):
        return [raw_result]

    # Caso 3: lista (puede ser de dicts, RealDictRow, o tuplas)
    if isinstance(raw_result, list):
        if len(raw_result) == 0:
            return []

        # Si el primer elemento es dict-like, convertir a dict puro
        if isinstance(raw_result[0], dict):
            return [dict(r) for r in raw_result]
        
        # Si es una lista de tuplas
        if isinstance(raw_result[0], tuple):
            return [dict(r) for r in raw_result]

    # Caso por defecto: tipo no reconocido
    return []


def run_detector(conn, detector_func: Callable)-> list[dict]:
    """
    Ejecuta un detector con manejo de errores aislado.
    Si falla, retorna [] y loguea
    Sin este aislamiento de errores, un detector fallido tira todo el scan
    """
    try:
        # Ejecutar el detector pasándole la conexión a PostgreSQL
        raw_result = detector_func(conn)
        # Normalizar el resultado a list[dict]
        return normalize_findings(raw_result)
    except Exception as e:
        print(f"Error al ejecutar {detector_func}: {e}")
        return []


def calculate_health_score(categories: dict) -> int:
    """
    Calcula un puntaje de salud de la base de datos en escala de 0 a 100.

    - Se empieza con 100 puntos (base de datos perfecta).
    - Por cada hallazgo encontrado se restan puntos según su severidad:
      - HIGH:   -3 puntos por hallazgo
      - MEDIUM: -1 punto por hallazgo
      - LOW:    -0.5 puntos por hallazgo
    - El puntaje mínimo es 0
    """
    score = 100.0
    # Recorrer cada categoría (índices, bloat, queries, etc.)
    for cat_data in categories.values():

        # Dentro de cada categoría, recorrer cada detector
        for det_data in cat_data.get("detectors", {}).values():
            count = det_data["count"]         # cantidad de hallazgos
            severity = det_data["severity"]   # severidad del detector
        
            # restar puntos según severidad × cantidad de hallazgos
            if severity == "HIGH":
                score -= count * 3
        
            elif severity == "MEDIUM":
                score -= count * 1
        
            elif severity == "LOW":
                score -= count * 0.5
    
    # Asegurar que el puntaje no sea negativo
    return max(0, int(score))


# INICIALIZACIÓN DE FASTAPI
# Crear la instancia principal de la app FastAPI
app = FastAPI(
    title="PgGuardian API",
    description="Auditoría y optimización de PostgreSQL",
    version="1.0.0"
)

"""
Configura CORS (Cross-Origin Resource Sharing) para que el frontend 
haga peticiones a esta API sin ser bloqueado por el navegador.
"""
app.add_middleware(
    CORSMiddleware,
    # permite cualquier origen, en prod se debe restringir a dominios específicos
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ENDPOINTS
@app.get("/", tags=["meta"])
def root():
    
    # metadata de la API y cuantos etectores hay disponibles.
    return {
        "name": "PgGuardian API",
        "version": "0.1.0",
        "docs": "/docs",                           # Ruta a Swagger UI auto-generada
        "detectors_loaded": len(DETECTORS_MENU)     # Cuántos detectores hay registrados
    }



@app.get("/health", tags=["meta"])
def health(conn=Depends(get_connection)):
    """
    Verifica que la API funcione y que pueda 
    conectarse a la base de dato
    """
    try:
        # query simple para confirmar que la conexión jala
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
        return {
            "status": "ok",
            "db_connected": True,
            "db_version": version,
            "detectors_available": len(DETECTORS_MENU),
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


# Primer endpoint (prueba)
@app.get("/api/detectors/{detector_id}", response_model=DetectorResponse, tags=["detectors"])
def run_single_detector(detector_id: str, conn=Depends(get_connection)):

    detector_id = detector_id.upper()
    meta = DETECTORS_MENU.get(detector_id)

    # Ejecutar el detector y formatea el resultado a list[dict]
    hallazgos = run_detector(conn, meta["function"])

    # Construir respuesta según el schema DetectorResponse
    return DetectorResponse(
        status="warning" if hallazgos else "ok",
        detector=meta["nombre"],
        count=len(hallazgos),
        data=hallazgos,
        executed_at=datetime.utcnow(),
    )

# ENDPOINT PRINCIPAL: Escaneo completo de la base de datos
"""
Recorre y ejecuta todos los detectores de DETECTORS_MENU, luego 
agrupa los resultados por categoría (Índices, Bloat, etc.)
y calcula un puntaje de salud (health_score) de 0 a 100.
"""
@app.get("/api/v1/scan/full", response_model=FullScanResponse, tags=["scan"])
def run_full_scan(conn=Depends(get_connection)):
    """
    Ejecuta todos los detectores registrados y retorna un reporte
    """

    categories: dict[str, dict] = {}
    total_findings = 0

    # Recorrer cada detector del menú de detectores
    for detector_id, meta in DETECTORS_MENU.items():
        hallazgos = run_detector(conn, meta["function"])
        category = meta["category"]

        # Inicializar la categoría si es la primera vez que aparece
        if category not in categories:
            categories[category] = {"total": 0, "detectors": {}}

        # Registrar los resultados del detector dentro de su categoría
        categories[category]["detectors"][detector_id] = {
            "name": meta["nombre"],
            "status": "warning" if hallazgos else "ok",
            "count": len(hallazgos),
            "severity": meta["severidad"],
        }
        categories[category]["total"] += len(hallazgos)
        total_findings += len(hallazgos)
    
    # Construir respuesta según el schema FullScanResponse
    return FullScanResponse(
        health_score=calculate_health_score(categories),
        total_findings=total_findings,
        categories=categories,
        executed_at=datetime.utcnow(),
    )



# ENDPOINT: Listar detectores del menú
"""
Retorna la lista de detectores registrados en DETECTORS_MENU,
regresa: id, nombre, categoría y severidad por defecto
"""
@app.get("/api/v1/detectors", tags=["menu"])
def list_detectors():

    # Construir un dict limpio sin el campo "function"
    return {
        "total": len(DETECTORS_MENU),
        "detectors": [
            {
                "hallazgo_id": hid,
                "title": meta["nombre"],
                "category": meta["category"],
                "default_severity": meta["severidad"],
            }
            for hid, meta in DETECTORS_MENU.items()
        ],
    }