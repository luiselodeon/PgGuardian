"""
PgGuardian API — Router de Bloat y Mantenimiento

Endpoints para los detectores de:
- Bloat en tablas (check_table_bloat)
- Autovacuum desactivado (check_disabled_autovacuum)
- Dead tuples (check_dead_tuples)
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from api.database import get_connection
from api.schemas import DetectorResponse
from detectors.bloat import (
    check_table_bloat,
    check_disabled_autovacuum,
    check_dead_tuples,
)

router = APIRouter(prefix="/api/bloat", tags=["Bloat"])


def _serialize(rows: list) -> list[dict[str, Any]]:
    """Convierte RealDictRow a dict estándar para serialización JSON."""
    result = []
    for row in rows:
        item = {}
        for key, value in dict(row).items():
            # Convertir Decimal a float para JSON
            if hasattr(value, 'as_tuple'):
                item[key] = float(value)
            else:
                item[key] = value
        result.append(item)
    return result


@router.get("/table-bloat", response_model=DetectorResponse)
def get_table_bloat(conn=Depends(get_connection)):
    """Analiza el bloat y fragmentación de tablas."""
    try:
        data = check_table_bloat(conn)
        serialized = _serialize(data)
        return DetectorResponse(
            status="warning" if len(serialized) > 0 else "ok",
            detector="check_table_bloat",
            count=len(serialized),
            data=serialized,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_table_bloat",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/disabled-autovacuum", response_model=DetectorResponse)
def get_disabled_autovacuum(conn=Depends(get_connection)):
    """Detecta tablas con autovacuum desactivado."""
    try:
        data = check_disabled_autovacuum(conn)
        serialized = _serialize(data)
        return DetectorResponse(
            status="warning" if len(serialized) > 0 else "ok",
            detector="check_disabled_autovacuum",
            count=len(serialized),
            data=serialized,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_disabled_autovacuum",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )


@router.get("/dead-tuples", response_model=DetectorResponse)
def get_dead_tuples(conn=Depends(get_connection)):
    """Muestra tablas con filas muertas (dead tuples)."""
    try:
        data = check_dead_tuples(conn)
        serialized = _serialize(data)
        # Filtrar las que tienen dead tuples > 0 para el conteo de warnings
        warnings = [r for r in serialized if r.get("dead_tuple_pct", 0) > 0]
        return DetectorResponse(
            status="warning" if len(warnings) > 0 else "ok",
            detector="check_dead_tuples",
            count=len(serialized),
            data=serialized,
            executed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        return DetectorResponse(
            status="error",
            detector="check_dead_tuples",
            count=0,
            data=[{"error": str(e)}],
            executed_at=datetime.now(timezone.utc),
        )
