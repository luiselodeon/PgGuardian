/*
Este es el Cliente API para PgGuardian.

Aquí se va a centralizar todas las llamadas al backend de FastAPI.
Se usa un Base URL configurable, manejo de errores y función fullScan 
que ejecuta todos los detectores en una sola petición.
*/

const API_BASE = 'http://localhost:8000/api';

async function fetchJSON(endpoint) {
  const res = await fetch(`${API_BASE}${endpoint}`);
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}


// En esta parte van a estar todas llas funciones que estén en el API del Backend
// Cuando estén las apis listas, se van a agregar sus exports aquí

// Esta función es únicamente temporal para poder observar y evaluar el front,
// posteriormente cuando estén las apis se cambiaran a sus fetchJSON correspondientes.
// return fetchJSON('/scan/full')
export async function fullScan() {
  // Devuelve datos de ejemplo para previsualizar el frontend
  await new Promise(r => setTimeout(r, 600)) // simula latencia de red
  return {
    health_score: 72,
    total_findings: 14,
    categories: {
      bloat: {
        label: 'Bloat',
        detectors: {
          table_bloat:         { label: 'Bloat en Tablas',           count: 3, data: [] },
          disabled_autovacuum: { label: 'Autovacuum Desactivado',    count: 0, data: [] },
          dead_tuples:         { label: 'Dead Tuples',               count: 2, data: [] },
        },
      },
      config: {
        label: 'Configuración',
        detectors: {
          work_mem:            { label: 'Valor de work_mem',         count: 1, data: [] },
          work_mem_evaluation: { label: 'Evaluación de work_mem',    count: 1, data: [] },
        },
      },
      health: {
        label: 'Salud General',
        detectors: {
          partitioning_candidates: { label: 'Candidatos a Particionamiento', count: 2, data: [] },
        },
      },
      indexes: {
        label: 'Índices',
        detectors: {
          missing_indexes:      { label: 'FK Sin Índice',            count: 3, data: [] },
          duplicate_indexes:    { label: 'Índices Duplicados',       count: 0, data: [] },
          unused_indexes:       { label: 'Índices No Usados',        count: 1, data: [] },
          missing_partial:      { label: 'Parciales Faltantes',      count: 0, data: [] },
          covering_candidates:  { label: 'Covering Index',           count: 0, data: [] },
          obsolete_stats:       { label: 'Stats Obsoletas',          count: 1, data: [] },
          wildcard_searches:    { label: 'Wildcards',                count: 0, data: [] },
        },
      },
      queries: {
        label: 'Queries',
        detectors: {
          pg_stat_statements: { label: 'pg_stat_statements', count: 0, data: [{ enabled: true }] },
          temp_spills:        { label: 'Temp Spills',         count: 0, data: [] },
          seq_scans:          { label: 'Sequential Scans',    count: 0, data: [] },
        },
      },
    },
  }
}