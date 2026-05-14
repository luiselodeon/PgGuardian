import { useState } from 'react'
import './SqlRecommendation.css'

/**
 * SqlRecommendation
 * Muestra un bloque de código SQL con estilo de terminal,
 * con botón de copiar al clipboard.
 */
export default function SqlRecommendation({ sql, title = 'Recomendación SQL' }) {
  const [copied, setCopied] = useState(false)

  if (!sql) return null

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sql)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback silencioso
    }
  }

  return (
    <div className="sql-rec">
      <div className="sql-rec-header">
        <span className="sql-rec-title">
          <span className="sql-rec-icon">⌘</span>
          {title}
        </span>
        <button
          className={`sql-rec-copy ${copied ? 'sql-rec-copy--done' : ''}`}
          onClick={handleCopy}
          title="Copiar SQL"
        >
          {copied ? '✓ Copiado' : 'Copiar'}
        </button>
      </div>
      <pre className="sql-rec-body">
        <code>{sql}</code>
      </pre>
    </div>
  )
}
