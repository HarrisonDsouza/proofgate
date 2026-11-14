import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { api, type Dashboard } from './api'

export function PageHead({ title, sub, children }: { title: string; sub: string; children?: ReactNode }) {
  return (
    <header className="page-head">
      <div>
        <h1>{title}</h1>
        <p>{sub}</p>
      </div>
      <span className="spacer" />
      {children}
    </header>
  )
}

export function Card({ title, hint, right, children, className = '' }: {
  title?: string; hint?: ReactNode; right?: ReactNode; children: ReactNode; className?: string
}) {
  return (
    <section className={`card ${className}`}>
      {title && (
        <div className="card-head">
          <h2>{title}</h2>
          {hint && <span className="hint">{hint}</span>}
          <span className="spacer" />
          {right}
        </div>
      )}
      {children}
    </section>
  )
}

export type Tone = 'good' | 'bad' | 'info'
export function Banner({ tone, title, lines = [], action }: { tone: Tone; title: string; lines?: string[]; action?: ReactNode }) {
  return (
    <div className={`banner ${tone}`} role={tone === 'bad' ? 'alert' : 'status'}>
      <div className="icon" aria-hidden>{tone === 'good' ? '✓' : tone === 'bad' ? '✕' : 'i'}</div>
      <div className="title">{title}</div>
      {action ? <div className="action">{action}</div> : <span />}
      <div className="lines">
        {lines.map((l) => (
          <div key={l}>{l}</div>
        ))}
      </div>
    </div>
  )
}

export function useDashboard() {
  return useQuery({ queryKey: ['dashboard'], queryFn: () => api<Dashboard>('/api/dashboard'), refetchInterval: 2000 })
}

export function Stats() {
  const { data } = useDashboard()
  const s = (k: string, v: number | undefined, tone = '') => (
    <div className={`stat ${tone}`}>
      <div className="k">{k}</div>
      <div className="v">{v ?? '—'}</div>
    </div>
  )
  return (
    <div className="stats" aria-live="polite">
      {s('Denials executed', data?.executed, data?.executed ? 'good' : '')}
      {s('Refused by the gate', data?.refused, data?.refused ? 'bad' : '')}
      {s('Reopened after suspension', data?.reversed, data?.reversed ? 'bad' : '')}
      {s('Awaiting human review', data?.pending)}
    </div>
  )
}
