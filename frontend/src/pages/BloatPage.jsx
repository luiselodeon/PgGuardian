import DataTable from '../components/DataTable'
import './PageCommon.css'

export default function BloatPage({ scanData, isLoading }) {
  const bloat = scanData?.categories?.bloat

  if (isLoading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Bloat y Mantenimiento</h1>
        </div>
        <div className="skeleton" style={{ height: 200, borderRadius: 14 }}></div>
        <div className="skeleton" style={{ height: 200, borderRadius: 14 }}></div>
      </div>
    )
  }

  const tableBloatData = bloat?.detectors?.table_bloat?.data || []
  const autovacuumData = bloat?.detectors?.disabled_autovacuum?.data || []
  const deadTuplesData = bloat?.detectors?.dead_tuples?.data || []

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1 className="page-title">Bloat y Mantenimiento</h1>
        <p className="page-subtitle">Bloat en tablas, autovacuum desactivado y dead tuples</p>
      </div>

      <div className="page-content">
        <DataTable
          title="Bloat en Tablas"
          data={tableBloatData}
          columns={[
            { key: 'tblname', label: 'Tabla' },
            { key: 'schemaname', label: 'Schema' },
            { key: 'real_size', label: 'Tamaño Real' },
            { key: 'bloat_size', label: 'Tamaño Bloat' },
            { key: 'bloat_pct', label: 'Bloat %' },
            { key: 'extra_pct', label: 'Extra %' },
            { key: 'evidence', label: 'Evidencia' },
            { key: 'sql_combined', label: 'Recomendación SQL' },
          ]}
          emptyMessage="No se detectó bloat significativo en las tablas"
        />

        <DataTable
          title="Autovacuum Desactivado"
          data={autovacuumData}
          columns={[
            { key: 'relname', label: 'Tabla' },
            { key: 'reloptions', label: 'Opciones' },
            { key: 'evidence', label: 'Evidencia' },
            { key: 'sql_combined', label: 'Recomendación SQL' },
          ]}
          emptyMessage="Todas las tablas tienen autovacuum habilitado"
        />

        <DataTable
          title="Dead Tuples"
          data={deadTuplesData}
          columns={[
            { key: 'table_name', label: 'Tabla' },
            { key: 'schemaname', label: 'Schema' },
            { key: 'n_live_tup', label: 'Filas Vivas' },
            { key: 'n_dead_tup', label: 'Filas Muertas' },
            { key: 'dead_tuple_pct', label: 'Dead %' },
            { key: 'evidence', label: 'Evidencia' },
            { key: 'sql_combined', label: 'Recomendación SQL' },
          ]}
          emptyMessage="No se encontraron tablas con dead tuples"
        />
      </div>
    </div>
  )
}
