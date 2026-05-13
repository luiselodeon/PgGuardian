"""
PgGuardian API — Router de Salud General

Endpoints para los detectores de:
- Candidatos a particionamiento (check_partitioning_candidates)
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from api.database import get_connection
from api.schemas import DetectorResponse
from detectors.health import check_partitioning_candidates

router = APIRouter(prefix="/api/health", tags=["Salud General"])


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


@router.get("/partitioning-candidates", response_model=DetectorResponse)
def get_partitioning_candidates(conn=Depends(get_connection)):
    """Identifica tablas candidatas a ser particionadas."""
    try:
        data = check_partitioning_candidates(conn)
        serialized = _serialize(data)
        return DetectorResponse(
            status="warning" if len(serialized) > 0 else "ok",
            detector="check_partitioning_candidates",
            count=len(serialized),
            data=serialized,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_partitioning_candidates",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )
