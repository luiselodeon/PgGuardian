import './SeverityBadge.css'

export default function SeverityBadge({ severity }) {
  const s = (severity || 'ok').toUpperCase()

  const map = {
    HIGH: { label: 'Alta', className: 'severity--high' },
    CRITICAL: { label: 'Crítico', className: 'severity--high' },
    MEDIUM: { label: 'Media', className: 'severity--medium' },
    LOW: { label: 'Baja', className: 'severity--low' },
    OK: { label: 'OK', className: 'severity--ok' },
    WARNING: { label: 'Warning', className: 'severity--medium' },
  }

  const info = map[s] || map['OK']

  return (
    <span className={`severity-badge ${info.className}`}>
      {info.label}
    </span>
  )
}
