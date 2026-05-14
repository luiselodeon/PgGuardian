import { useState } from 'react'
import DataTable from '../components/DataTable'
import './PageCommon.css'

const tabs = [
  { key: 'missing_indexes', label: 'FK Sin Índice' },
  { key: 'duplicate_indexes', label: 'Duplicados' },
  { key: 'unused_indexes', label: 'No Usados' },
  { key: 'missing_partial', label: 'Parciales Faltantes' },
  { key: 'covering_candidates', label: 'Covering Index' },
  { key: 'obsolete_stats', label: 'Stats Obsoletas' },
  { key: 'wildcard_searches', label: 'Wildcards' },
]

const columnConfig = {
  missing_indexes: [
    { key: 'constraint_name', label: 'Constraint' },
    { key: 'table_name', label: 'Tabla' },
    { key: 'column_name', label: 'Columna' },
    { key: 'referenced_table', label: 'Tabla Referenciada' },
    { key: 'evidence', label: 'Evidencia' },
    { key: 'sql_combined', label: 'Recomendación SQL' },
  ],
  duplicate_indexes: [
    { key: 'table_name', label: 'Tabla' },
    { key: 'columns', label: 'Columnas' },
    { key: 'index_names', label: 'Índices' },
    { key: 'count', label: 'Cantidad' },
    { key: 'evidence', label: 'Evidencia' },
    { key: 'sql_combined', label: 'Recomendación SQL' },
  ],
  unused_indexes: [
    { key: 'table_name', label: 'Tabla' },
    { key: 'index_name', label: 'Índice' },
    { key: 'idx_scan', label: 'Scans' },
    { key: 'size', label: 'Tamaño' },
    { key: 'evidence', label: 'Evidencia' },
    { key: 'sql_combined', label: 'Recomendación SQL' },
  ],
  missing_partial: [
    { key: 'table_name', label: 'Tabla' },
    { key: 'column_name', label: 'Columna' },
    { key: 'estimated_rows', label: 'Filas Estimadas' },
    { key: 'dominant_value', label: 'Valor Dominante' },
    { key: 'percent_occurrence', label: 'Ocurrencia %' },
    { key: 'evidence', label: 'Evidencia' },
    { key: 'sql_combined', label: 'Recomendación SQL', width: '400px'},
  ],
  covering_candidates: [
    { key: 'query_sample', label: 'Query' },
    { key: 'total_executions', label: 'Ejecuciones' },
    { key: 'total_time_ms', label: 'Tiempo Total (ms)' },
    { key: 'avg_time_ms', label: 'Tiempo Promedio (ms)' },
    { key: 'cache_hit_pct', label: 'Cache Hit %' },
    { key: 'evidence', label: 'Evidencia' },
    { key: 'sql_combined', label: 'Recomendación SQL', width: '500px'},
  ],
  obsolete_stats: [
    { key: 'table_name', label: 'Tabla' },
    { key: 'schema_name', label: 'Schema' },
    { key: 'planner_estimate', label: 'Estimación Planner' },
    { key: 'stats_live_tuples', label: 'Tuples Vivos' },
    { key: 'divergence_ratio', label: 'Ratio Divergencia' },
    { key: 'stats_severity', label: 'Severidad' },
    { key: 'evidence', label: 'Evidencia' },
    { key: 'sql_combined', label: 'Recomendación SQL' },
  ],
  wildcard_searches: [
    { key: 'query_sample', label: 'Query' },
    { key: 'total_executions', label: 'Ejecuciones' },
    { key: 'total_time_ms', label: 'Tiempo Total (ms)' },
    { key: 'anti_pattern_type', label: 'Anti-Patrón' },
    { key: 'severity', label: 'Severidad' },
    { key: 'evidence', label: 'Evidencia' },
    { key: 'sql_combined', label: 'Recomendación SQL' },
  ],
}

export default function IndexesPage({ scanData, isLoading }) {
  const [activeTab, setActiveTab] = useState('missing_indexes')
  const indexes = scanData?.categories?.indexes

  if (isLoading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Auditoría de Índices</h1>
        </div>
        <div className="skeleton" style={{ height: 300, borderRadius: 14 }}></div>
      </div>
    )
  }

  const activeDetector = indexes?.detectors?.[activeTab]
  const activeData = activeDetector?.data || []  

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1 className="page-title">Auditoría de Índices</h1>
        <p className="page-subtitle">7 detectores analizando la salud de tus índices</p>
      </div>

      {/* Tabs */}
      <div className="tab-bar">
        {tabs.map(tab => {
          const count = indexes?.detectors?.[tab.key]?.count || 0
          return (
            <button
              key={tab.key}
              className={`tab-btn ${activeTab === tab.key ? 'tab-btn--active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
              {count > 0 && <span className="tab-count">{count}</span>}
            </button>
          )
        })}
      </div>

      <div className="page-content">
        <DataTable
          title={activeDetector?.label || ''}
          data={activeData}
          columns={columnConfig[activeTab]}
          emptyMessage="No se encontraron hallazgos para este detector"
        />
      </div>
    </div>
  )
}
