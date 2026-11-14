import { FileSearch, Inbox, SlidersHorizontal } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { api, store, TENANT, type Policy } from './api'
import Examiner from './pages/Examiner'
import Review from './pages/Review'
import Supervisor from './pages/Supervisor'
import { Tally, useDashboard } from './ui'
import { useQuery } from '@tanstack/react-query'

function ConsoleKey() {
  const [key, setKey] = useState(store.key())
  return (
    <label className="keyfield">
      <span>Console key</span>
      <input
        type="password"
        autoComplete="off"
        value={key}
        placeholder="paste once"
        aria-label="Console key"
        onChange={(e) => {
          setKey(e.target.value)
          store.setKey(e.target.value)
        }}
      />
    </label>
  )
}

function Folio() {
  const { isSuccess, isError } = useDashboard()
  const pol = useQuery({ queryKey: ['policy'], queryFn: () => api<Policy[]>('/api/policies') })
  const v = pol.data?.find((p) => p.status === 'active')?.version
  return (
    <div className="folio">
      <span>
        <span className={`dot ${isSuccess ? 'on' : ''}`} aria-hidden />
        {isSuccess ? 'Atlas' : isError ? 'API unreachable' : 'connecting'}
      </span>
      <span>{TENANT.toUpperCase()}</span>
      <span>POLICY v{v ?? '–'}</span>
      <ConsoleKey />
    </div>
  )
}

export default function App() {
  return (
    <>
      <header className="masthead">
        <NavLink to="/review" className="wordmark" aria-label="ProofGate home">
          Proof<i>Gate</i>
        </NavLink>
        <nav className="nav" aria-label="Main">
          <NavLink to="/review"><Inbox aria-hidden />Review</NavLink>
          <NavLink to="/supervisor"><SlidersHorizontal aria-hidden />Supervisor</NavLink>
          <NavLink to="/examiner"><FileSearch aria-hidden />Examiner</NavLink>
        </nav>
        <Folio />
      </header>
      <Tally />
      <main className="page">
        <Routes>
          <Route path="/" element={<Navigate to="/review" replace />} />
          <Route path="/review" element={<Review />} />
          <Route path="/supervisor" element={<Supervisor />} />
          <Route path="/examiner" element={<Examiner />} />
          <Route path="/examiner/:caseId" element={<Examiner />} />
        </Routes>
      </main>
      <footer className="colophon">
        Synthetic data only. Every decision is one MongoDB Atlas transaction; this console only shows what Atlas recorded.
      </footer>
    </>
  )
}
