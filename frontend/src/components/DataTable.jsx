import { useState } from 'react'
import SeverityBadge from './SeverityBadge'
import './DataTable.css'

export default function DataTable({ title, data, columns, emptyMessage }) {
  const [expandedRow, setExpandedRow] = useState(null)

  if (!data || data.length === 0) {
    return (
      <div className="data-table-container fade-in">
        {title && <h3 className="table-title">{title}</h3>}
        <div className="table-empty">
          <p>{emptyMessage || 'No se encontraron hallazgos'}</p>
        </div>
      </div>
    )
  }

  // Auto-detect columns if not provided
  const cols = columns || Object.keys(data[0]).map(key => ({
    key,
    label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
  }))

  const toggleRow = (index) => {
    setExpandedRow(expandedRow === index ? null : index)
  }

  const renderCellValue = (value, key) => {
    if (value === null || value === undefined) return '—'
    if (typeof value === 'boolean') return value ? 'Sí' : 'No'
    if (key === 'severity' || key === 'stats_severity') return <SeverityBadge severity={value} />

    // Format numbers
    if (typeof value === 'number') {
      if (key.includes('pct') || key.includes('percent') || key.includes('ratio')) {
        return `${value.toFixed(2)}%`
      }
      if (key.includes('size') && !key.includes('pretty')) {
        return value.toLocaleString()
      }
      if (key.includes('time') || key.includes('ms')) {
        return `${value.toFixed(2)} ms`
      }
      return value.toLocaleString()
    }

    // Truncate long strings
    if (typeof value === 'string' && value.length > 120) {
      return value.substring(0, 120) + '…'
    }

    return String(value)
  }

  // Get all keys for expanded view
  const allKeys = data.length > 0 ? Object.keys(data[0]) : []
  const displayedKeys = cols.map(c => c.key)
  const extraKeys = allKeys.filter(k => !displayedKeys.includes(k))

  return (
    <div className="data-table-container fade-in">
      {title && <h3 className="table-title">{title}</h3>}
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              {cols.map(col => (
                <th key={col.key}>{col.label}</th>
              ))}
              {extraKeys.length > 0 && <th className="th-expand"></th>}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <>
                <tr key={i} onClick={() => extraKeys.length > 0 && toggleRow(i)} className={extraKeys.length > 0 ? 'expandable' : ''}>
                  {cols.map(col => (
                    <td key={col.key} className={col.key === 'query' || col.key === 'query_sample' || col.key === 'sql_fix' ? 'mono' : ''}>
                      {renderCellValue(row[col.key], col.key)}
                    </td>
                  ))}
                  {extraKeys.length > 0 && (
                    <td className="td-expand">
                      <span className={`expand-icon ${expandedRow === i ? 'expand-icon--open' : ''}`}>▸</span>
                    </td>
                  )}
                </tr>
                {expandedRow === i && extraKeys.length > 0 && (
                  <tr key={`${i}-detail`} className="detail-row">
                    <td colSpan={cols.length + 1}>
                      <div className="detail-content">
                        {extraKeys.map(k => (
                          <div key={k} className="detail-item">
                            <span className="detail-label">{k.replace(/_/g, ' ')}</span>
                            <span className={`detail-value ${k.includes('sql') || k.includes('query') ? 'mono' : ''}`}>
                              {renderCellValue(row[k], k)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
      <div className="table-footer">
        <span className="result-count">{data.length} resultado{data.length !== 1 ? 's' : ''}</span>
      </div>
    </div>
  )
}
