import DataTable from '../components/DataTable'
import SqlRecommendation from '../components/SqlRecommendation'
import SeverityBadge from '../components/SeverityBadge'
import './PageCommon.css'

/**
 * Bloque de hallazgo con evidencia + SQL para detectores de tipo "finding"
 * (los que devuelven category, title, severity, evidence, sql_fix).
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
            <span className="finding-card-title">{item.title || item.finding_id || 'Hallazgo'}</span>
            {item.severity && <SeverityBadge severity={item.severity} />}
          </div>
          {item.evidence && (
            <p className="finding-card-evidence">
              <span className="rec-evidence-icon">◈</span> {item.evidence}
            </p>
          )}
          <SqlRecommendation sql={item.sql_recommendation || item.sql_fix || item.suggested_action} />
        </div>
      ))}
    </div>
  )
}

export default function ConfigPage({ scanData, isLoading }) {
  const config = scanData?.categories?.config

  if (isLoading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Configuración</h1>
        </div>
        <div className="skeleton" style={{ height: 200, borderRadius: 14 }}></div>
        <div className="skeleton" style={{ height: 200, borderRadius: 14 }}></div>
      </div>
    )
  }

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1 className="page-title">Configuración</h1>
        <p className="page-subtitle">Parámetros críticos del servidor PostgreSQL y sus evaluaciones</p>
      </div>

      <div className="page-content">
        {/* work_mem — valor actual */}
        <DataTable
          title="Valor Actual de work_mem"
          data={config?.detectors?.work_mem?.data || []}
          columns={[
            { key: 'name', label: 'Parámetro' },
            { key: 'setting', label: 'Valor' },
            { key: 'unit', label: 'Unidad' },
          ]}
          emptyMessage="No se pudo obtener el valor de work_mem"
        />

        {/* work_mem — evaluación */}
        <section className="detector-section">
          <h3 className="detector-section-title">Evaluación de work_mem</h3>
          <FindingBlock
            data={config?.detectors?.work_mem_evaluation?.data}
            emptyMessage="work_mem tiene un valor aceptable"
          />
        </section>

        {/* shared_buffers — valor actual */}
        <DataTable
          title="Valor Actual de shared_buffers"
          data={config?.detectors?.shared_buffers?.data || []}
          columns={[
            { key: 'name', label: 'Parámetro' },
            { key: 'setting', label: 'Valor' },
            { key: 'unit', label: 'Unidad' },
          ]}
          emptyMessage="No se pudo obtener el valor de shared_buffers"
        />

        {/* shared_buffers — evaluación */}
        <section className="detector-section">
          <h3 className="detector-section-title">Evaluación de shared_buffers</h3>
          <FindingBlock
            data={config?.detectors?.shared_buffers_evaluation?.data}
            emptyMessage="shared_buffers tiene un valor aceptable"
          />
        </section>

        {/* pg_stat_statements.max — evaluación */}
        <section className="detector-section">
          <h3 className="detector-section-title">Evaluación de pg_stat_statements.max</h3>
          <FindingBlock
            data={config?.detectors?.pg_stat_max_evaluation?.data}
            emptyMessage="pg_stat_statements.max tiene un valor aceptable"
          />
        </section>

        {/* pg_stat_statements límite de tracking */}
        <section className="detector-section">
          <h3 className="detector-section-title">Límite de Tracking de Queries</h3>
          <FindingBlock
            data={config?.detectors?.pg_stat_limit?.data}
            emptyMessage="El tracking de queries es suficiente (sin eviction detectada)"
          />
        </section>

        {/* Logging de queries lentas */}
        <section className="detector-section">
          <h3 className="detector-section-title">Logging de Queries Lentas</h3>
          <FindingBlock
            data={config?.detectors?.slow_query_logging?.data}
            emptyMessage="El registro de queries lentas está habilitado"
          />
        </section>
      </div>
    </div>
  )
}
