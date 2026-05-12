import DataTable from '../components/DataTable'
import './PageCommon.css'

export default function ConfigPage({ scanData, isLoading }) {
  const config = scanData?.categories?.config

  if (isLoading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Configuración</h1>
        </div>
        <div className="skeleton" style={{ height: 200, borderRadius: 14 }}></div>
      </div>
    )
  }

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1 className="page-title">Configuración</h1>
        <p className="page-subtitle">Parámetros del servidor y evaluación de work_mem</p>
      </div>

      <div className="page-content">
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

        <DataTable
          title="Evaluación de work_mem"
          data={config?.detectors?.work_mem_evaluation?.data || []}
          columns={[
            { key: 'category', label: 'Categoría' },
            { key: 'title', label: 'Hallazgo' },
            { key: 'severity', label: 'Severidad' },
            { key: 'evidence', label: 'Evidencia' },
          ]}
          emptyMessage="work_mem tiene un valor aceptable"
        />
      </div>
    </div>
  )
}
