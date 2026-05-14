"""
PgGuardian — Schemas de respuesta genéricos

Modelos Pydantic que envuelven la metadata de cada respuesta
sin acoplar la estructura interna de los datos.
Usa dict[str, Any] para ser compatible con cualquier base de datos PostgreSQL.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel


class DetectorResponse(BaseModel):
    """Respuesta estándar para cualquier detector individual."""
    status: str                     # "ok" | "warning" | "error"
    detector: str                   # Nombre del detector ejecutado
    count: int                      # Cantidad de resultados/hallazgos
    data: list[dict[str, Any]]      # Resultados crudos — estructura genérica
    executed_at: datetime


class FullScanResponse(BaseModel):
    """Respuesta del escaneo completo que agrupa todos los detectores."""
    health_score: int               # 0-100
    total_findings: int
    categories: dict[str, Any]      # Resultados agrupados por categoría
    executed_at: datetime
