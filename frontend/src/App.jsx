import { useState, useEffect, useCallback } from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Overview from './pages/Overview'
import BloatPage from './pages/BloatPage'
import ConfigPage from './pages/ConfigPage'
import HealthPage from './pages/HealthPage'
import IndexesPage from './pages/IndexesPage'
import QueriesPage from './pages/QueriesPage'
import { fullScan } from './api/pgguardian'
import './App.css'

const POLL_INTERVAL = 30000 // 30 seconds

export default function App() {
  const [scanData, setScanData] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [lastScan, setLastScan] = useState(null)
  const [error, setError] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const runScan = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await fullScan()
      setScanData(data)
      setLastScan(new Date().toISOString())
    } catch (err) {
      setError(err.message)
      console.error('Scan failed:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Initial scan
  useEffect(() => {
    runScan()
  }, [runScan])

  // Auto-refresh polling
  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(runScan, POLL_INTERVAL)
    return () => clearInterval(interval)
  }, [autoRefresh, runScan])

  return (
    <div className="app-layout">
      <Sidebar scanData={scanData} />

      <main className="main-content">
        {/* Top bar */}
        <header className="top-bar">
          <div className="top-bar-left">
            {error && (
              <div className="error-toast">
                <span>{error}</span>
                <button onClick={() => setError(null)} className="toast-close">×</button>
              </div>
            )}
          </div>
          <div className="top-bar-actions">
            <label className="auto-refresh-toggle">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              <span className="toggle-label">Auto-refresh (30s)</span>
            </label>
            <button
              className={`scan-button ${isLoading ? 'scan-button--loading' : ''}`}
              onClick={runScan}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <span className="spinner"></span>
                  Escaneando…
                </>
              ) : (
                <>Ejecutar Escaneo</>
              )}
            </button>
          </div>
        </header>

        {/* Page content */}
        <div className="page-wrapper">
          <Routes>
            <Route path="/" element={<Overview scanData={scanData} isLoading={isLoading} lastScan={lastScan} />} />
            <Route path="/bloat" element={<BloatPage scanData={scanData} isLoading={isLoading} />} />
            <Route path="/config" element={<ConfigPage scanData={scanData} isLoading={isLoading} />} />
            <Route path="/health" element={<HealthPage scanData={scanData} isLoading={isLoading} />} />
            <Route path="/indexes" element={<IndexesPage scanData={scanData} isLoading={isLoading} />} />
            <Route path="/queries" element={<QueriesPage scanData={scanData} isLoading={isLoading} />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}
