import { useNavigate } from 'react-router-dom'
import HealthScore from '../components/HealthScore'
import CategoryCard from '../components/CategoryCard'
import './Overview.css'

export default function Overview({ scanData, isLoading, lastScan }) {
  const navigate = useNavigate()

  const routeMap = {
    bloat: '/bloat',
    config: '/config',
    health: '/health',
    indexes: '/indexes',
    queries: '/queries',
  }

  return (
    <div className="overview-page">
      <div className="overview-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Resumen de salud de la base de datos</p>
        </div>
        {lastScan && (
          <div className="last-scan-info">
            <span className="last-scan-label">Último escaneo</span>
            <span className="last-scan-time">{new Date(lastScan).toLocaleString('es-MX')}</span>
          </div>
        )}
      </div>

      {/* Score + Summary */}
      <div className="overview-hero">
        <div className="hero-score-card fade-in">
          <h2 className="hero-card-title">Health Score</h2>
          <HealthScore score={scanData?.health_score} isLoading={isLoading} />
          <div className="hero-stats">
            <div className="hero-stat">
              <span className="hero-stat-value">
                {scanData?.categories
                  ? Object.values(scanData.categories).reduce((acc, cat) => {
                      return acc + Object.values(cat.detectors).reduce((sum, d) => sum + (d.count || 0), 0)
                    }, 0)
                  : '—'}
              </span>
              <span className="hero-stat-label">Hallazgos</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">{scanData?.categories ? Object.keys(scanData.categories).length : '—'}</span>
              <span className="hero-stat-label">Categorías</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">
                {scanData?.categories
                  ? Object.values(scanData.categories).reduce(
                      (acc, cat) => acc + Object.keys(cat.detectors).length, 0
                    )
                  : '—'}
              </span>
              <span className="hero-stat-label">Detectores</span>
            </div>
          </div>
        </div>
      </div>

      {/* Category Cards */}
      <div className="overview-section">
        <h2 className="section-title">Categorías</h2>
        <div className="category-grid">
          {isLoading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 240, borderRadius: 14 }}></div>
            ))
          ) : scanData?.categories ? (
            Object.entries(scanData.categories).map(([key, cat]) => (
              <CategoryCard
                key={key}
                categoryKey={key}
                category={cat}
                onClick={() => navigate(routeMap[key])}
              />
            ))
          ) : (
            <div className="no-data-message">
              <p>Haz clic en <strong>"Ejecutar Escaneo"</strong> para analizar la base de datos</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
