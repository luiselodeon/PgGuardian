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

# Detectores de BLOAT
from detectors.bloat import (
    check_table_bloat,                  
    check_disabled_autovacuum,          
    check_dead_tuples,                  
)

# Detectores de CONFIG
from detectors.config import (
    evaluate_work_mem,                  
)

# Detectores de SALUD general
from detectors.health import (
    check_partitioning_candidates,
)

# Detectores para QUERIES
from detectors.queries import (
    detect_temp_spills,                 
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
    "D1": {
        "nombre": "Llaves foráneas sin índice",
        "descripcion": "Detecta llaves foráneas que no tienen un índice asociado.",
        "category": "Índices",
        "function": check_missing_indexes,
        "severidad": "HIGH"
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