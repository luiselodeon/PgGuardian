import DataTable from '../components/DataTable'
import SqlRecommendation from '../components/SqlRecommendation'
import SeverityBadge from '../components/SeverityBadge'
import './PageCommon.css'

/**
 * Renderiza una lista de hallazgos tipo "finding" con evidencia y SQL.
 */
function FindingBlock({ data, emptyMessage }) {
  if (!data || data.length === 0) {
    return <p className="finding-empty">{emptyMessage || 'Sin hallazgos detectados'}</p>
  }
  return (
    <div className="finding-list">
      {data.map((item, i) => (
        <div key={i} className="finding-card">
          <div className="finding-card-header">
            <span className="finding-card-title">{item.title || 'Hallazgo'}</span>
            {item.severity && <SeverityBadge severity={item.severity} />}
          </div>
          {item.evidence && (
            <p className="finding-card-evidence">
              <span className="rec-evidence-icon">◈</span> {item.evidence}
            </p>
          )}
          <SqlRecommendation sql={item.sql_recommendation || item.sql_fix} />
        </div>
      ))}
    </div>
  )
}

function QuerySection({ title, data, columns, emptyMessage }) {
  // Inyectamos la columna dinámicamente para que el SQL quede en la tabla
  const enhancedColumns = [...columns, { key: 'sql_combined', label: 'Recomendación SQL' }]
  return (
    <DataTable
      title={title}
      data={data || []}
      columns={enhancedColumns}
      emptyMessage={emptyMessage}
    />
  )
}

export default function QueriesPage({ scanData, isLoading }) {
  const queries = scanData?.categories?.queries

  if (isLoading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Queries Problemáticas</h1>
        </div>
        <div className="skeleton" style={{ height: 200, borderRadius: 14 }}></div>
        <div className="skeleton" style={{ height: 200, borderRadius: 14 }}></div>
      </div>
    )
  }

  const pgStatEnabled = queries?.detectors?.pg_stat_statements?.data?.[0]?.enabled

  const tempSpillsData  = queries?.detectors?.temp_spills?.data    || []
  const seqScansData    = queries?.detectors?.seq_scans?.data      || []
  const topTimeData     = queries?.detectors?.top_time_queries?.data || []
  const dbTempData      = queries?.detectors?.db_temp_usage?.data  || []
  const explainData     = queries?.detectors?.explain_spills?.data  || []

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1 className="page-title">Queries Problemáticas</h1>
        <p className="page-subtitle">Detección de temp spills, seq scans, queries lentas y anti-patrones</p>
      </div>

      <div className={`status-banner ${pgStatEnabled ? 'status-banner--ok' : 'status-banner--warn'}`}>
        <span className="status-banner-icon">{pgStatEnabled ? 'OK' : 'Advertencia'}</span>
        <span>
          pg_stat_statements: <strong>{pgStatEnabled ? 'Habilitado' : 'No habilitado'}</strong>
          {!pgStatEnabled && ' — Algunos detectores no funcionarán sin esta extensión'}
        </span>
      </div>

      <div className="page-content">
        <section className="detector-section">
          <h3 className="detector-section-title">Temp Spills (Escritura a Disco)</h3>
          <FindingBlock
            data={tempSpillsData}
            emptyMessage="No se detectaron queries con escritura a disco"
          />
        </section>

        <QuerySection
          title="Sequential Scans"
          data={seqScansData}
          columns={[
            { key: 'title', label: 'Hallazgo' },
            { key: 'calls', label: 'Ejecuciones' },
            { key: 'evidence', label: 'Evidencia' },
          ]}
          emptyMessage="No se detectaron queries con Seq Scan"
        />

        <section className="detector-section">
          <h3 className="detector-section-title">Queries con Mayor Tiempo Acumulado</h3>
          <FindingBlock
            data={topTimeData}
            emptyMessage="No se detectaron queries con tiempo acumulado alto"
          />
        </section>

        <section className="detector-section">
          <h3 className="detector-section-title">Uso de Archivos Temporales en BD</h3>
          <FindingBlock
            data={dbTempData}
            emptyMessage="No se detectó uso de archivos temporales a nivel base de datos"
          />
        </section>

        <section className="detector-section">
          <h3 className="detector-section-title">Spills Detectados por EXPLAIN</h3>
          <FindingBlock
            data={explainData}
            emptyMessage="No se detectaron spills en los planes de ejecución"
          />
        </section>
      </div>
    </div>
  )
}
