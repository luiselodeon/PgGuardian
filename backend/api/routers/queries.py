"""
PgGuardian API — Router de Queries Problemáticas

Endpoints para los detectores de:
- Estado de pg_stat_statements (check_pg_stat_statements)
- Spills a disco (evaluate_temp_spills)
- Seq Scans en queries (detect_seq_scan_queries)
- Queries con mayor tiempo acumulado (evaluate_top_time_queries)
- Uso de archivos temporales en BD (evaluate_database_temp_usage)
- Spills detectados con EXPLAIN (evaluate_explain_spills)
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from api.database import get_connection
from api.schemas import DetectorResponse
from detectors.queries import (check_pg_stat_statements, evaluate_temp_spills, detect_seq_scan_queries, evaluate_top_time_queries, evaluate_database_temp_usage, evaluate_explain_spills)

router = APIRouter(prefix="/api/queries", tags=["Queries"])


@router.get("/pg-stat-status", response_model=DetectorResponse)
def get_pg_stat_status(conn=Depends(get_connection)):
    """Verifica si pg_stat_statements está habilitado."""
    try:
        enabled = check_pg_stat_statements(conn)
        data = [{"pg_stat_statements_enabled": enabled}]
        return DetectorResponse(
            status="ok" if enabled else "warning",
            detector="check_pg_stat_statements",
            count=1,
            data=data,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_pg_stat_statements",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/temp-spills", response_model=DetectorResponse)
def get_temp_spills(conn=Depends(get_connection)):
    """Detecta queries con posible uso de archivos temporales."""
    try:
        findings = evaluate_temp_spills(conn)
        return DetectorResponse(
            status="warning" if len(findings) > 0 else "ok",
            detector="evaluate_temp_spills",
            count=len(findings),
            data=findings,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="evaluate_temp_spills",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/seq-scans", response_model=DetectorResponse)
def get_seq_scans(conn=Depends(get_connection)):
    """Detecta queries que realizan Sequential Scans."""
    try:
        data = detect_seq_scan_queries(conn)
        return DetectorResponse(
            status="warning" if len(data) > 0 else "ok",
            detector="detect_seq_scan_queries",
            count=len(data),
            data=data,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="detect_seq_scan_queries",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/top-time", response_model=DetectorResponse)
def get_top_time_queries(conn=Depends(get_connection)):
    """Queries con mayor tiempo acumulado de ejecución."""
    try:
        findings = evaluate_top_time_queries(conn)
        return DetectorResponse(
            status="warning" if len(findings) > 0 else "ok",
            detector="evaluate_top_time_queries",
            count=len(findings),
            data=findings,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="evaluate_top_time_queries",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/db-temp-usage", response_model=DetectorResponse)
def get_database_temp_usage(conn=Depends(get_connection)):
    """Uso de archivos temporales a nivel base de datos."""
    try:
        findings = evaluate_database_temp_usage(conn)
        return DetectorResponse(
            status="warning" if len(findings) > 0 else "ok",
            detector="evaluate_database_temp_usage",
            count=len(findings),
            data=findings,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="evaluate_database_temp_usage",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/explain-spills", response_model=DetectorResponse)
def get_explain_spills(conn=Depends(get_connection)):
    """Detecta spills a disco analizando EXPLAIN de queries lentas."""
    try:
        findings = evaluate_explain_spills(conn)
        return DetectorResponse(
            status="warning" if len(findings) > 0 else "ok",
            detector="evaluate_explain_spills",
            count=len(findings),
            data=findings,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="evaluate_explain_spills",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )
