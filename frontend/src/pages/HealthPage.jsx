import DataTable from '../components/DataTable'
import SqlRecommendation from '../components/SqlRecommendation'
import SeverityBadge from '../components/SeverityBadge'
import './PageCommon.css'

function FindingBlock({ data, emptyMessage }) {
  if (!data || data.length === 0) {
    return <p className="finding-empty">{emptyMessage || 'Sin hallazgos detectados'}</p>
  }
  return (
    <div className="finding-list">
      {data.map((item, i) => (
        <div key={i} className="finding-card">
          <div className="finding-card-header">
            <span className="finding-card-title">{item.finding_id || item.title || 'Hallazgo'}</span>
            {item.severity && <SeverityBadge severity={item.severity} />}
          </div>
          {(item.evidence || item.description) && (
            <p className="finding-card-evidence">
              <span className="rec-evidence-icon">◈</span>
              {item.evidence || item.description}
            </p>
          )}
          {(item.recommendation) && (
            <p className="finding-card-recommendation">
              {item.recommendation}
            </p>
          )}
          <SqlRecommendation sql={item.sql_recommendation || item.sql_fix} />
        </div>
      ))}
    </div>
  )
}

export default function HealthPage({ scanData, isLoading }) {
  const health = scanData?.categories?.health

  if (isLoading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Salud General</h1>
        </div>
        <div className="skeleton" style={{ height: 200, borderRadius: 14 }}></div>
        <div className="skeleton" style={{ height: 200, borderRadius: 14 }}></div>
      </div>
    )
  }

  const partitionData = health?.detectors?.partitioning_candidates?.data || []
  const idleData = health?.detectors?.idle_in_transaction?.data || []

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1 className="page-title">Salud General</h1>
        <p className="page-subtitle">Candidatos a particionamiento, sesiones bloqueadas y políticas de retención</p>
      </div>

      <div className="page-content">
        {/* Las recomendaciones ahora van integradas directo a las columnas */}
        <DataTable
          title="Candidatos a Particionamiento"
          data={partitionData}
          columns={[
            { key: 'table_name', label: 'Tabla' },
            { key: 'schemaname', label: 'Schema' },
            { key: 'total_table_size', label: 'Tamaño' },
            { key: 'size_mb', label: 'MB' },
            { key: 'total_inserts_history', label: 'Inserts Totales' },
            { key: 'total_deletes_history', label: 'Deletes Totales' },
            { key: 'delete_ratio_pct', label: 'Ratio Delete %' },
            { key: 'evidence', label: 'Evidencia' },
            { key: 'sql_combined', label: 'Recomendación SQL' },
          ]}
          emptyMessage="No se encontraron candidatos a particionamiento"
        />

        <section className="detector-section">
          <h3 className="detector-section-title">
            Sesiones Idle In Transaction
            {idleData.length > 0 && (
              <span className="detector-section-badge detector-section-badge--warn">
                {idleData.length} sesión{idleData.length !== 1 ? 'es' : ''} activa{idleData.length !== 1 ? 's' : ''}
              </span>
            )}
          </h3>
          {idleData.length === 0 ? (
            <p className="finding-empty">No se detectaron sesiones idle in transaction</p>
          ) : (
            <FindingBlock data={idleData} />
          )}
        </section>
      </div>
    </div>
  )
}
