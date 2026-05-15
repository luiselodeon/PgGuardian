/*
Este es el Cliente API para PgGuardian.

Aquí se va a centralizar todas las llamadas al backend de FastAPI.
Se usa un Base URL configurable, manejo de errores y función fullScan 
que ejecuta todos los detectores en una sola petición.

Este documento fue hecho con ayuda de Inteligencia Artificial. 
*/

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

async function fetchJSON(endpoint) {
  const res = await fetch(`${API_BASE}${endpoint}`);
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

// En esta parte van a estar todas las funciones que estén en el API del Backend

// Health Check
export const healthCheck = () => fetchJSON('/health-check');

// Full Scan
export const fullScan = () => fetchJSON('/full-scan');

// Bloat
export const getTableBloat = () => fetchJSON('/bloat/table-bloat');
export const getDisabledAutovacuum = () => fetchJSON('/bloat/disabled-autovacuum');
export const getDeadTuples = () => fetchJSON('/bloat/dead-tuples');

// Config
export const getWorkMem = () => fetchJSON('/config/work-mem');
export const evaluateWorkMem = () => fetchJSON('/config/evaluate-work-mem');
export const getSharedBuffers = () => fetchJSON('/config/shared-buffers');
export const evaluateSharedBuffers = () => fetchJSON('/config/evaluate-shared-buffers');
export const evaluatePgStatMax = () => fetchJSON('/config/evaluate-pg-stat-max');
export const getPgStatLimit = () => fetchJSON('/config/pg-stat-limit');
export const getSlowQueryLogging = () => fetchJSON('/config/slow-query-logging');

// Health
export const getPartitioningCandidates = () => fetchJSON('/health/partitioning-candidates');
export const getIdleInTransaction = () => fetchJSON('/health/idle-in-transaction');

// Indexes
export const getMissingPartialIndexes = () => fetchJSON('/indexes/missing-partial');
export const getMissingIndexes = () => fetchJSON('/indexes/missing');
export const getDuplicateIndexes = () => fetchJSON('/indexes/duplicate');
export const getUnusedIndexes = () => fetchJSON('/indexes/unused');
export const getCoveringCandidates = () => fetchJSON('/indexes/covering-candidates');
export const getObsoleteStats = () => fetchJSON('/indexes/obsolete-stats');
export const getLeadingWildcards = () => fetchJSON('/indexes/leading-wildcards');

// Queries
export const getPgStatStatus = () => fetchJSON('/queries/pg-stat-status');
export const getTempSpills = () => fetchJSON('/queries/temp-spills');
export const getSeqScans = () => fetchJSON('/queries/seq-scans');
export const getTopTimeQueries = () => fetchJSON('/queries/top-time');
export const getDatabaseTempUsage = () => fetchJSON('/queries/db-temp-usage');
export const getExplainSpills = () => fetchJSON('/queries/explain-spills');