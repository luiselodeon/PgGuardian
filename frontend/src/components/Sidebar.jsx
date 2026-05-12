import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import './Sidebar.css'

const navItems = [
  {
    path: '/',
    label: 'Overview',
    icon: '📊',
    description: 'Resumen general',
  },
  {
    path: '/bloat',
    label: 'Bloat',
    icon: '💾',
    description: 'Bloat y mantenimiento',
  },
  {
    path: '/config',
    label: 'Configuración',
    icon: '⚙️',
    description: 'Parámetros del servidor',
  },
  {
    path: '/health',
    label: 'Salud General',
    icon: '🏥',
    description: 'Particionamiento y retención',
  },
  {
    path: '/indexes',
    label: 'Índices',
    icon: '🔍',
    description: 'Auditoría de índices',
  },
  {
    path: '/queries',
    label: 'Queries',
    icon: '⚡',
    description: 'Queries problemáticas',
  },
]

export default function Sidebar({ scanData }) {
  const getCategoryCount = (category) => {
    if (!scanData?.categories?.[category]) return null
    const cat = scanData.categories[category]
    let total = 0
    Object.values(cat.detectors).forEach(d => {
      total += d.count || 0
    })
    return total
  }

  const categoryMap = {
    '/bloat': 'bloat',
    '/config': 'config',
    '/health': 'health',
    '/indexes': 'indexes',
    '/queries': 'queries',
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <span className="logo-icon">🛡️</span>
          <div>
            <h1 className="logo-text">PgGuardian</h1>
            <span className="logo-subtitle">Health Monitor</span>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const count = categoryMap[item.path]
            ? getCategoryCount(categoryMap[item.path])
            : null

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `nav-item ${isActive ? 'nav-item--active' : ''}`
              }
            >
              <span className="nav-icon">{item.icon}</span>
              <div className="nav-content">
                <span className="nav-label">{item.label}</span>
                <span className="nav-desc">{item.description}</span>
              </div>
              {count !== null && count > 0 && (
                <span className="nav-badge">{count}</span>
              )}
            </NavLink>
          )
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className={`status-dot ${scanData ? 'status-dot--connected' : 'status-dot--disconnected'}`}></span>
          <span className="status-text">
            {scanData ? 'Conectado' : 'Sin datos'}
          </span>
        </div>
      </div>
    </aside>
  )
}
