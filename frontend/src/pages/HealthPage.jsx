import DataTable from '../components/DataTable'
import './PageCommon.css'

export default function HealthPage({ scanData, isLoading }) {
  const health = scanData?.categories?.health

  if (isLoading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Salud General</h1>
        </div>
        <div className="skeleton" style={{ height: 200, borderRadius: 14 }}></div>
      </div>
    )
  }

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1 className="page-title">Salud General</h1>
        <p className="page-subtitle">Candidatos a particionamiento y políticas de retención</p>
      </div>

      <div className="page-content">
        <DataTable
          title="Candidatos a Particionamiento"
          data={health?.detectors?.partitioning_candidates?.data || []}
          columns={[
            { key: 'table_name', label: 'Tabla' },
            { key: 'schemaname', label: 'Schema' },
            { key: 'total_table_size', label: 'Tamaño' },
            { key: 'size_mb', label: 'MB' },
            { key: 'total_inserts_history', label: 'Inserts Totales' },
            { key: 'total_deletes_history', label: 'Deletes Totales' },
            { key: 'delete_ratio_pct', label: 'Ratio Delete %' },
          ]}
          emptyMessage="No se encontraron candidatos a particionamiento"
        />
      </div>
    </div>
  )
}
