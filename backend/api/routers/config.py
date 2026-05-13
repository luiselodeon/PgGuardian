"""
PgGuardian API — Router de Configuración

Endpoints para los detectores de:
- Valor de work_mem (get_work_mem)
- Evaluación de work_mem (evaluate_work_mem)
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from api.database import get_connection
from api.schemas import DetectorResponse
from detectors.config import get_work_mem, evaluate_work_mem

router = APIRouter(prefix="/api/config", tags=["Configuración"])


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
