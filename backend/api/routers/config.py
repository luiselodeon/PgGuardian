"""
PgGuardian API — Router de Configuración

Endpoints para los detectores de:
- Valor de work_mem (get_work_mem)
- Evaluación de work_mem (evaluate_work_mem)
- Valor de shared_buffers (get_shared_buffers)
- Evaluación de shared_buffers (evaluate_shared_buffers)
- Evaluación de pg_stat_statements.max (evaluate_pg_stat_statements_max)
- Límite de tracking de queries (check_pg_stat_statements_limit)
- Logging de queries lentas (check_slow_query_logging)
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from api.database import get_connection
from api.schemas import DetectorResponse
from detectors.config import (get_work_mem, evaluate_work_mem, get_shared_buffers, evaluate_shared_buffers, evaluate_pg_stat_statements_max,check_pg_stat_statements_limit,check_slow_query_logging,)

router = APIRouter(prefix="/api/config", tags=["Configuración"])


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


@router.get("/work-mem", response_model=DetectorResponse)
def get_work_mem_endpoint(conn=Depends(get_connection)):
    """Consulta el valor actual de work_mem."""
    try:
        result = get_work_mem(conn)
        if result:
            name, setting, unit = result
            data = [{"name": name, "setting": setting, "unit": unit}]
        else:
            data = []
        return DetectorResponse(
            status="ok",
            detector="get_work_mem",
            count=len(data),
            data=data,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="get_work_mem",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/evaluate-work-mem", response_model=DetectorResponse)
def evaluate_work_mem_endpoint(conn=Depends(get_connection)):
    """Evalúa si work_mem es insuficiente para el workload."""
    try:
        finding = evaluate_work_mem(conn)
        if finding:
            data = [finding]
            status = "warning"
        else:
            data = []
            status = "ok"
        return DetectorResponse(
            status=status,
            detector="evaluate_work_mem",
            count=len(data),
            data=data,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="evaluate_work_mem",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/shared-buffers", response_model=DetectorResponse)
def get_shared_buffers_endpoint(conn=Depends(get_connection)):
    """Consulta el valor actual de shared_buffers."""
    try:
        result = get_shared_buffers(conn)
        if result:
            name, setting, unit = result
            data = [{"name": name, "setting": setting, "unit": unit}]
        else:
            data = []
        return DetectorResponse(
            status="ok",
            detector="get_shared_buffers",
            count=len(data),
            data=data,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="get_shared_buffers",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/evaluate-shared-buffers", response_model=DetectorResponse)
def evaluate_shared_buffers_endpoint(conn=Depends(get_connection)):
    """Evalúa si shared_buffers tiene un valor bajo."""
    try:
        finding = evaluate_shared_buffers(conn)
        if finding:
            data = [finding]
            status = "warning"
        else:
            data = []
            status = "ok"
        return DetectorResponse(
            status=status,
            detector="evaluate_shared_buffers",
            count=len(data),
            data=data,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="evaluate_shared_buffers",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/evaluate-pg-stat-max", response_model=DetectorResponse)
def evaluate_pg_stat_max_endpoint(conn=Depends(get_connection)):
    """Evalúa si pg_stat_statements.max es insuficiente."""
    try:
        finding = evaluate_pg_stat_statements_max(conn)
        if finding:
            data = finding
            status = "warning"
        else:
            data = []
            status = "ok"
        return DetectorResponse(
            status=status,
            detector="evaluate_pg_stat_statements_max",
            count=len(data),
            data=data,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="evaluate_pg_stat_statements_max",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/pg-stat-limit", response_model=DetectorResponse)
def get_pg_stat_limit_endpoint(conn=Depends(get_connection)):
    """Verifica si el límite de tracking de queries causa eviction."""
    try:
        rows = check_pg_stat_statements_limit(conn)
        serialized = _serialize(rows)
        return DetectorResponse(
            status="warning" if len(serialized) > 0 else "ok",
            detector="check_pg_stat_statements_limit",
            count=len(serialized),
            data=serialized,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_pg_stat_statements_limit",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/slow-query-logging", response_model=DetectorResponse)
def get_slow_query_logging_endpoint(conn=Depends(get_connection)):
    """Verifica si el registro de queries lentas está habilitado."""
    try:
        rows = check_slow_query_logging(conn)
        serialized = _serialize(rows)
        return DetectorResponse(
            status="warning" if len(serialized) > 0 else "ok",
            detector="check_slow_query_logging",
            count=len(serialized),
            data=serialized,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_slow_query_logging",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )
