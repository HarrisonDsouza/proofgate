import { useQuery } from '@tanstack/react-query'
import { LoaderCircle } from 'lucide-react'
import type { ReactNode } from 'react'
import { api, type Dashboard } from './api'

export function Title({ title, sub, children }: { title: string; sub: string; children?: ReactNode }) {
  return (
    <header className="title">
      <div>
        <h1>{title}</h1>
        <p>{sub}</p>
      </div>
      <span className="spacer" />
      {children}
    </header>
  )
}

export function Spin({ label }: { label?: string }) {
  return <LoaderCircle className="spin" aria-hidden={!label} aria-label={label} />
}

export type Tone = 'good' | 'bad' | 'info'

export function Notice({ tone, head, lines = [], stamp, action }: {
  tone: Tone; head: string; lines?: string[]; stamp?: { text: string; sub: string; ink: 'red' | 'proof' }; action?: ReactNode
}) {
  return (
    <div className={`notice ${tone}`} role={tone === 'bad' ? 'alert' : 'status'}>
      <div className="head">{head}</div>
      {(stamp || action) && (
        <div className="side">
          {action}
          {stamp && (
            <span className={`stamp ${stamp.ink}`} aria-hidden>
              {stamp.text}
              <small>{stamp.sub}</small>
            </span>
          )}
        </div>
      )}
      {lines.length > 0 && (
        <div className="lines">
          {lines.map((l) => (
            <div key={l}>{l}</div>
          ))}
        </div>
      )}
    </div>
  )
}

export function useDashboard() {
  return useQuery({ queryKey: ['dashboard'], queryFn: () => api<Dashboard>('/api/dashboard'), refetchInterval: 3000, refetchOnWindowFocus: false })
}

export function Tally() {
  const { data } = useDashboard()
  const col = (k: string, v: number | undefined, ink = '') => (
    <div>
      <div className="k">{k}</div>
      <div className={`v ${ink}`}>{v ?? '–'}</div>
    </div>
  )
  return (
    <div className="tally" aria-live="polite">
      {col('Denials executed', data?.executed, data?.executed ? 'proof' : '')}
      {col('Refused by the gate', data?.refused, data?.refused ? 'red' : '')}
      {col('Reopened after suspension', data?.reversed, data?.reversed ? 'red' : '')}
      {col('Awaiting human review', data?.pending)}
    </div>
  )
}
