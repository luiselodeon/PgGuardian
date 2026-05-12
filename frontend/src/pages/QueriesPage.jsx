import DataTable from '../components/DataTable'
import './PageCommon.css'

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

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1 className="page-title">Queries Problemáticas</h1>
        <p className="page-subtitle">Detección de temp spills, seq scans y anti-patrones</p>
      </div>

      {/* pg_stat_statements status */}
      <div className={`status-banner ${pgStatEnabled ? 'status-banner--ok' : 'status-banner--warn'}`}>
        <span className="status-banner-icon">{pgStatEnabled ? 'OK' : 'Advertencia'}</span>
        <span>
          pg_stat_statements: <strong>{pgStatEnabled ? 'Habilitado' : 'No habilitado'}</strong>
          {!pgStatEnabled && ' — Algunos detectores no funcionarán sin esta extensión'}
        </span>
      </div>

      <div className="page-content">
        <DataTable
          title="Temp Spills (Escritura a Disco)"
          data={queries?.detectors?.temp_spills?.data || []}
          columns={[
            { key: 'title', label: 'Hallazgo' },
            { key: 'severity', label: 'Severidad' },
            { key: 'evidence', label: 'Evidencia' },
          ]}
          emptyMessage="No se detectaron queries con escritura a disco"
        />

        <DataTable
          title="Sequential Scans"
          data={queries?.detectors?.seq_scans?.data || []}
          columns={[
            { key: 'title', label: 'Hallazgo' },
            { key: 'calls', label: 'Ejecuciones' },
            { key: 'recommendation', label: 'Recomendación' },
          ]}
          emptyMessage="No se detectaron queries con Seq Scan"
        />
      </div>
    </div>
  )
}
