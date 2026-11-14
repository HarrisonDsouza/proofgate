import { useState } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { store, TENANT } from './api'
import Examiner from './pages/Examiner'
import Review from './pages/Review'
import Supervisor from './pages/Supervisor'
import { useDashboard } from './ui'

function ConsoleKey() {
  const [key, setKey] = useState(store.key())
  return (
    <label>
      Console key
      <input
        type="password"
        autoComplete="off"
        value={key}
        placeholder="Paste once per tab"
        onChange={(e) => {
          setKey(e.target.value)
          store.setKey(e.target.value)
        }}
      />
    </label>
  )
}

function Connection() {
  const { isSuccess, isError } = useDashboard()
  return (
    <div className="meta">
      <span>
        <span className={`status-dot ${isSuccess ? 'on' : ''}`} aria-hidden />
        {isSuccess ? 'Atlas connected' : isError ? 'API unreachable' : 'Connecting…'}
      </span>
    </div>
  )
}

export default function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo" aria-hidden>PG</div>
          <div>
            <strong>ProofGate</strong>
            <small>No proof of review, no denial.</small>
          </div>
        </div>
        <nav className="nav" aria-label="Main">
          <div className="nav-label">Workspace</div>
          <NavLink to="/review"><span className="ico" aria-hidden>▤</span>Review queue</NavLink>
          <NavLink to="/supervisor"><span className="ico" aria-hidden>◎</span>Supervisor</NavLink>
          <NavLink to="/examiner"><span className="ico" aria-hidden>⌕</span>Examiner</NavLink>
        </nav>
        <div className="sidebar-foot">
          <div className="meta">
            <span>Tenant</span>
            <span className="mono">{TENANT}</span>
          </div>
          <ConsoleKey />
          <Connection />
        </div>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/review" replace />} />
          <Route path="/review" element={<Review />} />
          <Route path="/supervisor" element={<Supervisor />} />
          <Route path="/examiner" element={<Examiner />} />
          <Route path="/examiner/:caseId" element={<Examiner />} />
        </Routes>
        <p className="footnote">
          Synthetic data only. Every decision is made by one MongoDB Atlas transaction; this console only displays it.
        </p>
      </main>
    </div>
  )
}
