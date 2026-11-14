import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { api, store, type Dashboard } from './api'
import Examiner from './pages/Examiner'
import Review from './pages/Review'

function ConsoleKey() {
  const [key, setKey] = useState(store.key())
  return (
    <label className="key">
      <span>Console key</span>
      <input
        type="password"
        autoComplete="off"
        value={key}
        placeholder="paste once"
        onChange={(e) => {
          setKey(e.target.value)
          store.setKey(e.target.value)
        }}
      />
    </label>
  )
}

function Ledger() {
  const { data } = useQuery({ queryKey: ['dashboard'], queryFn: () => api<Dashboard>('/api/dashboard'), refetchInterval: 2000 })
  if (!data) return <div className="ledger muted">connecting to Atlas…</div>
  return (
    <div className="ledger" aria-live="polite">
      <span><b className="num good">{data.executed}</b> executed</span>
      <span><b className={`num ${data.refused ? 'bad' : ''}`}>{data.refused}</b> refused by the gate</span>
      <span><b className={`num ${data.reversed ? 'bad' : ''}`}>{data.reversed}</b> reopened</span>
      <span><b className="num">{data.pending}</b> awaiting review</span>
      {data.suspended_reviewers.length > 0 && (
        <span className="tag bad">suspended: {data.suspended_reviewers.join(', ')}</span>
      )}
    </div>
  )
}

export default function App() {
  return (
    <div className="shell">
      <header className="top">
        <div className="brand">
          <span className="mark" aria-hidden>◆</span>
          <div>
            <strong>ProofGate</strong>
            <small>No proof of review, no denial.</small>
          </div>
        </div>
        <nav>
          <NavLink to="/review">Review</NavLink>
          <NavLink to="/examiner">Examiner</NavLink>
          <a href="http://localhost:8080/" target="_blank" rel="noreferrer">Supervisor ↗</a>
        </nav>
        <ConsoleKey />
      </header>
      <Ledger />
      <main>
        <Routes>
          <Route path="/" element={<Navigate to="/review" replace />} />
          <Route path="/review" element={<Review />} />
          <Route path="/examiner" element={<Examiner />} />
          <Route path="/examiner/:caseId" element={<Examiner />} />
        </Routes>
      </main>
      <footer>Synthetic data only. Every decision is made by one MongoDB Atlas transaction; this page only shows it.</footer>
    </div>
  )
}
