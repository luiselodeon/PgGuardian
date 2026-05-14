"""
PgGuardian API — Punto de Entrada

Aplicación FastAPI que expone todos los detectores de salud de PostgreSQL
a través de endpoints REST agrupados por categoría.

Incluye:
- CORS configurado para el frontend
- Routers para cada módulo detector
- Endpoint /api/full-scan que ejecuta todos los detectores
- Endpoint /api/health-check para verificar conectividad
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from api.database import get_connection
from api.schemas import DetectorResponse, FullScanResponse

# Importar routers
from api.routers import bloat as bloat_router
from api.routers import config as config_router
from api.routers import health as health_router
from api.routers import indexes as indexes_router
from api.routers import queries as queries_router

# Importar detectores 
from detectors.bloat import check_table_bloat, check_disabled_autovacuum, check_dead_tuples
from detectors.config import (get_work_mem, evaluate_work_mem, get_shared_buffers, evaluate_shared_buffers, evaluate_pg_stat_statements_max,check_pg_stat_statements_limit,check_slow_query_logging,)
from detectors.health import check_partitioning_candidates, check_idle_in_transaction
from detectors.indexes import (check_missing_partial_indexes, check_missing_indexes, check_duplicate_indexes, check_unused_indexes, check_covering_index_candidates, check_obsolete_stats, check_leading_wildcard_searches)
from detectors.queries import (evaluate_temp_spills,detect_seq_scan_queries,check_pg_stat_statements,evaluate_top_time_queries,evaluate_database_temp_usage,evaluate_explain_spills)


app = FastAPI(
    title="PgGuardian API",
    description="API de diagnóstico de salud para PostgreSQL",
    version="1.0.0",
)

origins = [
    "http://localhost:5173",    # Para seguir probando localmente
    "https://pgguardian-frontend.onrender.com" 
]

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(bloat_router.router)
app.include_router(config_router.router)
app.include_router(health_router.router)
app.include_router(indexes_router.router)
app.include_router(queries_router.router)


def _serialize(rows: list) -> list[dict[str, Any]]:
    """Convierte RealDictRow a dict estándar para serialización JSON."""
    result = []
    for row in rows:
        item = {}
        for key, value in dict(row).items():
            if hasattr(value, 'as_tuple'):
                item[key] = float(value)
            else:
                item[key] = value
        result.append(item)
    return result


def _safe_run(func, conn, serialize=True):
    """Ejecuta un detector de forma segura, capturando excepciones."""
    try:
        result = func(conn)
        if result is None:
            return []
        if serialize and isinstance(result, list) and len(result) > 0:
            # Si el primer elemento tiene items() es un dict-like (RealDictRow)
            if hasattr(result[0], 'items'):
                return _serialize(result)
        return result if isinstance(result, list) else [result]
    except Exception as e:
        return [{"error": str(e)}]


@app.get("/api/health-check")
def health_check(conn=Depends(get_connection)):
    """Verifica que la API puede conectarse a PostgreSQL."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
        return {
            "status": "ok",
            "database": "connected",
            "pg_version": version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@app.get("/api/full-scan", response_model=FullScanResponse)
def full_scan(conn=Depends(get_connection)):
    """
    Ejecuta TODOS los detectores y devuelve un reporte consolidado
    con health score calculado.
    """
    now = datetime.now(timezone.utc)

    # --- Ejecutar cada detector ---
    # Bloat
    table_bloat = _safe_run(check_table_bloat, conn)
    disabled_autovacuum = _safe_run(check_disabled_autovacuum, conn)
    dead_tuples = _safe_run(check_dead_tuples, conn)

    # Config
    work_mem_result = get_work_mem(conn)
    work_mem_data = []
    if work_mem_result:
        name, setting, unit = work_mem_result
        work_mem_data = [{"name": name, "setting": setting, "unit": unit}]
    work_mem_eval = evaluate_work_mem(conn) or []

    shared_buffers_result = get_shared_buffers(conn)
    shared_buffers_data = []
    if shared_buffers_result:
        name, setting, unit = shared_buffers_result
        shared_buffers_data = [{"name": name, "setting": setting, "unit": unit}]
    shared_buffers_eval = evaluate_shared_buffers(conn) or []

    pg_stat_max_eval = evaluate_pg_stat_statements_max(conn) or []
    pg_stat_limit = _safe_run(check_pg_stat_statements_limit, conn)
    slow_query_logging = _safe_run(check_slow_query_logging, conn)

    # Health
    partition_candidates = _safe_run(check_partitioning_candidates, conn)
    idle_in_transaction = _safe_run(check_idle_in_transaction, conn)

    # Indexes
    missing_partial = _safe_run(check_missing_partial_indexes, conn)
    missing_indexes = _safe_run(check_missing_indexes, conn)
    duplicate_indexes = _safe_run(check_duplicate_indexes, conn)
    unused_indexes = _safe_run(check_unused_indexes, conn)
    covering_candidates = _safe_run(check_covering_index_candidates, conn)
    obsolete_stats = _safe_run(check_obsolete_stats, conn)
    wildcard_searches = _safe_run(check_leading_wildcard_searches, conn)

    # Queries
    pg_stat_enabled = check_pg_stat_statements(conn)
    temp_spills = _safe_run(evaluate_temp_spills, conn, serialize=False)
    seq_scans = _safe_run(detect_seq_scan_queries, conn, serialize=False)
    top_time_queries = _safe_run(evaluate_top_time_queries, conn, serialize=False)
    db_temp_usage = _safe_run(evaluate_database_temp_usage, conn, serialize=False)
    explain_spills = _safe_run(evaluate_explain_spills, conn, serialize=False)

    # --- Agrupar por categoría ---
    categories = {
        "bloat": {
            "label": "Bloat y Mantenimiento",
            "detectors": {
                "table_bloat": {
                    "label": "Bloat en Tablas",
                    "count": len(table_bloat),
                    "data": table_bloat,
                },
                "disabled_autovacuum": {
                    "label": "Autovacuum Desactivado",
                    "count": len(disabled_autovacuum),
                    "data": disabled_autovacuum,
                },
                "dead_tuples": {
                    "label": "Dead Tuples",
                    "count": len(dead_tuples),
                    "data": dead_tuples,
                },
            },
        },
        "config": {
            "label": "Configuración",
            "detectors": {
                "work_mem": {
                    "label": "Work Mem Actual",
                    "count": len(work_mem_data),
                    "data": work_mem_data,
                },
                "work_mem_evaluation": {
                    "label": "Evaluación Work Mem",
                    "count": len(work_mem_eval),
                    "data": work_mem_eval,
                },
                "shared_buffers": {
                    "label": "Shared Buffers Actual",
                    "count": len(shared_buffers_data),
                    "data": shared_buffers_data,
                },
                "shared_buffers_evaluation": {
                    "label": "Evaluación Shared Buffers",
                    "count": len(shared_buffers_eval),
                    "data": shared_buffers_eval,
                },
                "pg_stat_max_evaluation": {
                    "label": "Evaluación pg_stat_statements.max",
                    "count": len(pg_stat_max_eval),
                    "data": pg_stat_max_eval,
                },
                "pg_stat_limit": {
                    "label": "Límite de Tracking de Queries",
                    "count": len(pg_stat_limit),
                    "data": pg_stat_limit,
                },
                "slow_query_logging": {
                    "label": "Logging de Queries Lentas",
                    "count": len(slow_query_logging),
                    "data": slow_query_logging,
                },
            },
        },
        "health": {
            "label": "Salud General",
            "detectors": {
                "partitioning_candidates": {
                    "label": "Candidatos a Particionamiento",
                    "count": len(partition_candidates),
                    "data": partition_candidates,
                },
                "idle_in_transaction": {
                    "label": "Idle In Transaction",
                    "count": len(idle_in_transaction),
                    "data": idle_in_transaction,
                },
            },
        },
        "indexes": {
            "label": "Auditoría de Índices",
            "detectors": {
                "missing_partial": {
                    "label": "Índices Parciales Faltantes",
                    "count": len(missing_partial),
                    "data": missing_partial,
                },
                "missing_indexes": {
                    "label": "FK Sin Índice",
                    "count": len(missing_indexes),
                    "data": missing_indexes,
                },
                "duplicate_indexes": {
                    "label": "Índices Duplicados",
                    "count": len(duplicate_indexes),
                    "data": duplicate_indexes,
                },
                "unused_indexes": {
                    "label": "Índices No Usados",
                    "count": len(unused_indexes),
                    "data": unused_indexes,
                },
                "covering_candidates": {
                    "label": "Candidatos a Covering Index",
                    "count": len(covering_candidates),
                    "data": covering_candidates,
                },
                "obsolete_stats": {
                    "label": "Estadísticas Obsoletas",
                    "count": len(obsolete_stats),
                    "data": obsolete_stats,
                },
                "wildcard_searches": {
                    "label": "Búsquedas con Wildcard",
                    "count": len(wildcard_searches),
                    "data": wildcard_searches,
                },
            },
        },
        "queries": {
            "label": "Queries Problemáticas",
            "detectors": {
                "pg_stat_statements": {
                    "label": "pg_stat_statements",
                    "count": 1,
                    "data": [{"enabled": pg_stat_enabled}],
                },
                "temp_spills": {
                    "label": "Temp Spills",
                    "count": len(temp_spills),
                    "data": temp_spills,
                },
                "seq_scans": {
                    "label": "Sequential Scans",
                    "count": len(seq_scans),
                    "data": seq_scans,
                },
                "top_time_queries": {
                    "label": "Queries Más Lentas",
                    "count": len(top_time_queries),
                    "data": top_time_queries,
                },
                "db_temp_usage": {
                    "label": "Uso Temporal en BD",
                    "count": len(db_temp_usage),
                    "data": db_temp_usage,
                },
                "explain_spills": {
                    "label": "Spills por EXPLAIN",
                    "count": len(explain_spills),
                    "data": explain_spills,
                },
            },
        },
    }

    # --- Calcular Health Score ---
    # Cada problema encontrado resta puntos, máximo 100
    penalty = 0

    # Bloat
    bloat_warnings = [r for r in table_bloat if not isinstance(r, dict) or r.get("bloat_pct", 0) > 20]
    penalty += len(bloat_warnings) * 5
    penalty += len(disabled_autovacuum) * 10
    dead_warnings = [r for r in dead_tuples if isinstance(r, dict) and r.get("dead_tuple_pct", 0) > 10]
    penalty += len(dead_warnings) * 5

    # Config
    penalty += len(work_mem_eval) * 8
    penalty += len(shared_buffers_eval) * 8
    penalty += len(pg_stat_max_eval) * 5
    penalty += len(pg_stat_limit) * 3
    penalty += len(slow_query_logging) * 5

    # Health
    penalty += len(partition_candidates) * 2
    penalty += len(idle_in_transaction) * 10

    # Indexes
    penalty += len(missing_indexes) * 6
    penalty += len(duplicate_indexes) * 4
    penalty += len(unused_indexes) * 3
    penalty += len(missing_partial) * 3
    penalty += len(obsolete_stats) * 5
    penalty += len(wildcard_searches) * 3
    penalty += len(covering_candidates) * 2

    # Queries
    penalty += len([s for s in temp_spills if isinstance(s, dict) and s.get("severity") == "HIGH"]) * 8
    penalty += len([s for s in temp_spills if isinstance(s, dict) and s.get("severity") == "MEDIUM"]) * 5
    penalty += len(seq_scans) * 4
    penalty += len(top_time_queries) * 4
    penalty += len(db_temp_usage) * 5
    penalty += len(explain_spills) * 6

    # Nunca puede ser menor a cero
    health_score = max(0, 100 - penalty)

    # Total findings (excluyendo info/ok)
    total_findings = (
        len(bloat_warnings) + len(disabled_autovacuum) + len(dead_warnings)
        + len(work_mem_eval)
        + len(shared_buffers_eval) + len(pg_stat_max_eval)
        + len(pg_stat_limit) + len(slow_query_logging)
        + len(partition_candidates) + len(idle_in_transaction)
        + len(missing_partial) + len(missing_indexes) + len(duplicate_indexes)
        + len(unused_indexes) + len(covering_candidates) + len(obsolete_stats)
        + len(wildcard_searches)
        + len(temp_spills) + len(seq_scans)
        + len(top_time_queries) + len(db_temp_usage) + len(explain_spills)
    )

    return FullScanResponse(
        health_score=health_score,
        total_findings=total_findings,
        categories=categories,
        executed_at=now,
    )
