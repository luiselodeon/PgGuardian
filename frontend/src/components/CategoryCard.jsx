import './CategoryCard.css'



export default function CategoryCard({ categoryKey, category, onClick }) {
  if (!category) return null

  const detectors = category.detectors || {}
  let totalFindings = 0
  let hasWarnings = false

  Object.values(detectors).forEach(d => {
    totalFindings += d.count || 0
    if (d.count > 0) hasWarnings = true
  })

  const detectorCount = Object.keys(detectors).length
  const statusClass = hasWarnings ? 'card--warning' : 'card--ok'

  return (
    <div className={`category-card ${statusClass}`} onClick={onClick} role="button" tabIndex={0}>
      <div className="card-header">
        <div className="card-title-group">
          <h3 className="card-title">{category.label}</h3>
          <span className="card-detector-count">{detectorCount} detectores</span>
        </div>
      </div>

      <div className="card-metric">
        <span className="metric-value">{totalFindings}</span>
        <span className="metric-label">hallazgos</span>
      </div>

      <div className="card-footer">
        {Object.entries(detectors).map(([key, det]) => (
          <div key={key} className="detector-pill">
            <span className={`pill-dot ${det.count > 0 ? 'pill-dot--warn' : 'pill-dot--ok'}`}></span>
            <span className="pill-label">{det.label}</span>
            <span className="pill-count">{det.count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
