"""
PgGuardian API — Router de Auditoría de Índices

Endpoints para los detectores de:
- Índices parciales faltantes (check_missing_partial_indexes)
- Llaves foráneas sin índice (check_missing_indexes)
- Índices duplicados (check_duplicate_indexes)
- Índices no usados (check_unused_indexes)
- Candidatos a índice cubriente (check_covering_index_candidates)
- Estadísticas obsoletas (check_obsolete_stats)
- Búsquedas con wildcard inicial (check_leading_wildcard_searches)
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from api.database import get_connection
from api.schemas import DetectorResponse
from detectors.indexes import (
    check_missing_partial_indexes,
    check_missing_indexes,
    check_duplicate_indexes,
    check_unused_indexes,
    check_covering_index_candidates,
    check_obsolete_stats,
    check_leading_wildcard_searches,
)

router = APIRouter(prefix="/api/indexes", tags=["Índices"])


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


@router.get("/missing-partial", response_model=DetectorResponse)
def get_missing_partial_indexes(conn=Depends(get_connection)):
    """Detecta oportunidades de índices parciales."""
    try:
        data = check_missing_partial_indexes(conn)
        serialized = _serialize(data)
        return DetectorResponse(
            status="warning" if len(serialized) > 0 else "ok",
            detector="check_missing_partial_indexes",
            count=len(serialized),
            data=serialized,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_missing_partial_indexes",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/missing", response_model=DetectorResponse)
def get_missing_indexes(conn=Depends(get_connection)):
    """Detecta llaves foráneas sin índice."""
    try:
        data = check_missing_indexes(conn)
        serialized = _serialize(data)
        return DetectorResponse(
            status="warning" if len(serialized) > 0 else "ok",
            detector="check_missing_indexes",
            count=len(serialized),
            data=serialized,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_missing_indexes",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/duplicate", response_model=DetectorResponse)
def get_duplicate_indexes(conn=Depends(get_connection)):
    """Identifica índices duplicados."""
    try:
        data = check_duplicate_indexes(conn)
        serialized = _serialize(data)
        return DetectorResponse(
            status="warning" if len(serialized) > 0 else "ok",
            detector="check_duplicate_indexes",
            count=len(serialized),
            data=serialized,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_duplicate_indexes",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/unused", response_model=DetectorResponse)
def get_unused_indexes(conn=Depends(get_connection)):
    """Identifica índices que no se utilizan."""
    try:
        data = check_unused_indexes(conn)
        serialized = _serialize(data)
        return DetectorResponse(
            status="warning" if len(serialized) > 0 else "ok",
            detector="check_unused_indexes",
            count=len(serialized),
            data=serialized,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_unused_indexes",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/covering-candidates", response_model=DetectorResponse)
def get_covering_index_candidates(conn=Depends(get_connection)):
    """Detecta queries que se beneficiarían de índices cubrientes (INCLUDE)."""
    try:
        data = check_covering_index_candidates(conn)
        serialized = _serialize(data)
        return DetectorResponse(
            status="warning" if len(serialized) > 0 else "ok",
            detector="check_covering_index_candidates",
            count=len(serialized),
            data=serialized,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_covering_index_candidates",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/obsolete-stats", response_model=DetectorResponse)
def get_obsolete_stats(conn=Depends(get_connection)):
    """Detecta estadísticas obsoletas que causan planes subóptimos."""
    try:
        data = check_obsolete_stats(conn)
        serialized = _serialize(data)
        return DetectorResponse(
            status="warning" if len(serialized) > 0 else "ok",
            detector="check_obsolete_stats",
            count=len(serialized),
            data=serialized,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_obsolete_stats",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/leading-wildcards", response_model=DetectorResponse)
def get_leading_wildcard_searches(conn=Depends(get_connection)):
    """Detecta uso de LIKE/ILIKE con wildcard al inicio."""
    try:
        data = check_leading_wildcard_searches(conn)
        serialized = _serialize(data)
        return DetectorResponse(
            status="warning" if len(serialized) > 0 else "ok",
            detector="check_leading_wildcard_searches",
            count=len(serialized),
            data=serialized,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_leading_wildcard_searches",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )
