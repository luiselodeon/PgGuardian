import './HealthScore.css'

export default function HealthScore({ score, isLoading }) {
  if (isLoading) {
    return (
      <div className="health-score-container">
        <div className="health-ring skeleton" style={{ width: 180, height: 180, borderRadius: '50%' }}></div>
      </div>
    )
  }

  const s = score ?? 0
  const circumference = 2 * Math.PI * 72 // radius=72
  const offset = circumference - (s / 100) * circumference

  const getColor = () => {
    if (s >= 80) return 'var(--severity-ok)'
    if (s >= 60) return 'var(--severity-medium)'
    if (s >= 40) return '#f97316'
    return 'var(--severity-high)'
  }

  const getLabel = () => {
    if (s >= 80) return 'Saludable'
    if (s >= 60) return 'Aceptable'
    if (s >= 40) return 'Necesita Atención'
    return 'Crítico'
  }

  const color = getColor()

  return (
    <div className="health-score-container fade-in">
      <svg className="health-ring" viewBox="0 0 160 160" width="180" height="180">
        {/* Glow filter */}
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background ring */}
        <circle
          cx="80" cy="80" r="72"
          fill="none"
          stroke="var(--border-subtle)"
          strokeWidth="8"
        />

        {/* Score arc */}
        <circle
          cx="80" cy="80" r="72"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 80 80)"
          filter="url(#glow)"
          style={{ transition: 'stroke-dashoffset 1s ease-out, stroke 0.5s ease' }}
        />

        {/* Score text */}
        <text x="80" y="72" textAnchor="middle" fill={color} fontSize="36" fontWeight="700" fontFamily="var(--font-sans)">
          {s}
        </text>
        <text x="80" y="100" textAnchor="middle" fill="var(--text-secondary)" fontSize="12" fontWeight="400">
          {getLabel()}
        </text>
      </svg>
    </div>
  )
}
