import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Pause, Play, UserX } from 'lucide-react'
import { useState } from 'react'
import { api, ruleName, secs, type Policy } from '../api'
import { Notice, Title, useDashboard, type Tone } from '../ui'
import { errText } from './Review'

const REVIEWERS = ['dr-demo', 'dr-stamper', 'dr-skim', 'dr-cardio', 'dr-expired', 'vol-1', 'vol-2', 'vol-3']
const when = (t?: string) => (t ? new Date(t).toLocaleTimeString() : '–')
const LABELS: Record<string, string> = {
  min_active_dwell_ms: 'Server-timed review per case, at least',
  min_item_active_ms: 'Time on each cited document, at least',
  rate_max_approvals: 'Approvals allowed per window',
  rate_window_ms: 'Rate window',
  median_n: 'Approvals in the median-dwell check',
  max_proposal_age_ms: 'Proposal expires after',
  compensation_lookback_ms: 'Reopen denials executed in the last',
}
const label = (k: string) => LABELS[k] ?? k.replace(/_ms$/, '').replaceAll('_', ' ').replace(/^./, (c) => c.toUpperCase())
const dur = (ms: number) => (ms >= 3600000 ? `${+(ms / 3600000).toFixed(1)} h` : ms >= 60000 && ms % 60000 === 0 ? `${ms / 60000} min` : secs(ms))
const value = (k: string, v: unknown) => (k.endsWith('_ms') ? dur(Number(v)) : typeof v === 'boolean' ? (v ? 'required' : 'off') : String(v))

export default function Supervisor() {
  const qc = useQueryClient()
  const dash = useDashboard()
  const policies = useQuery({ queryKey: ['policy'], queryFn: () => api<Policy[]>('/api/policies') })
  const active = policies.data?.find((p) => p.status === 'active')
  const curFloorS = Math.round(Number(active?.rules.min_active_dwell_ms ?? 30000) / 1000)
  const [floorS, setFloorS] = useState('')
  const [who, setWho] = useState('dr-stamper')
  const [paused, setPaused] = useState<boolean | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [msg, setMsg] = useState<{ tone: Tone; head: string; lines?: string[] } | null>(null)

  async function act(name: string, fn: () => Promise<{ tone: Tone; head: string; lines?: string[] }>) {
    setBusy(name)
    try {
      setMsg(await fn())
      qc.invalidateQueries()
    } catch (e) {
      setMsg({ tone: 'bad', head: 'Refused', lines: [errText(e)] })
    } finally {
      setBusy(null)
    }
  }

  const setFloor = () =>
    act('floor', async () => {
      const ms = Math.round(Number(floorS) * 1000)
      if (!Number.isFinite(ms) || ms <= curFloorS * 1000 || ms > 600000) throw new Error(`Enter a floor above the current ${curFloorS} s (at most 600 s). Policies can only be tightened.`)
      const r = await api<{ version: number; superseded_version: number }>('/api/policies', {
        rules: { min_active_dwell_ms: ms },
        rationale: `Supervisor raised the dwell floor to ${secs(ms)}`,
      })
      setFloorS('')
      return { tone: 'good', head: `Policy v${r.version} is in force`, lines: [`v${r.superseded_version} superseded in the same Atlas transaction. Floor is now ${secs(ms)}; every gate decision records the version it used.`] }
    })

  const halt = () =>
    act('halt', async () => {
      await api('/api/suspensions', { reviewer_id: who, reason: 'SUPERVISOR_HALT' })
      return { tone: 'bad', head: `${who} suspended`, lines: ['Grants revoked, pending approvals sent back to review, executed denials queued to reopen with read-back.'] }
    })

  const togglePause = () =>
    act('pause', async () => {
      const r = await api<{ paused: boolean }>('/api/agent/pause', { paused: !paused })
      setPaused(r.paused)
      return { tone: 'info', head: r.paused ? 'Agent paused' : 'Agent running', lines: [r.paused ? 'The executor requests no grants until resumed.' : 'The executor picks up approved proposals again.'] }
    })

  const d = dash.data
  const burst = d?.last_burst

  return (
    <>
      <Title title="Supervisor" sub="Tighten the review policy, halt a reviewer, or stop the agent. Every control is written to Atlas inside a transaction." />
      {msg && <Notice tone={msg.tone} head={msg.head} lines={msg.lines} />}

      <div className="ledger-grid">
        <section>
          <h2 className="section">Review policy {active && <span className="tag proof" style={{ marginLeft: 6 }}>v{active.version} in force</span>}</h2>
          <dl className="kv">
            {Object.entries(active?.rules ?? {}).map(([k, v]) => (
              <div key={k} style={{ display: 'contents' }}>
                <dt>{label(k)}</dt>
                <dd>{value(k, v)}</dd>
              </div>
            ))}
          </dl>
          <form
            className="inline-form"
            onSubmit={(e) => {
              e.preventDefault()
              setFloor()
            }}
          >
            <label className="field">
              Raise the dwell floor to (seconds)
              <input type="number" min={curFloorS + 1} max={600} step={1} inputMode="numeric" value={floorS} onChange={(e) => setFloorS(e.target.value)} placeholder={`more than ${curFloorS}`} />
            </label>
            <button className="btn ink" disabled={!floorS || !!busy}>
              Publish v{(active?.version ?? 0) + 1}
            </button>
          </form>
        </section>

        <section>
          <h2 className="section">Controls</h2>
          <div className="ctl">
            <label className="field what">
              Halt a reviewer
              <select value={who} onChange={(e) => setWho(e.target.value)}>
                {REVIEWERS.map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
            </label>
            <button className="btn redline" onClick={halt} disabled={!!busy} style={{ alignSelf: 'flex-end' }}>
              <UserX aria-hidden />
              Suspend
            </button>
          </div>
          <div className="ctl">
            <div className="what">
              <b>Agent executor</b>
              <span>{paused === null ? 'Running unless paused here' : paused ? 'Paused: no grants requested' : 'Running'}</span>
            </div>
            <button className="btn" onClick={togglePause} disabled={!!busy}>
              {paused ? <Play aria-hidden /> : <Pause aria-hidden />}
              {paused ? 'Resume agent' : 'Pause agent'}
            </button>
          </div>
        </section>

        <section>
          <h2 className="section">Last agent run</h2>
          {!burst ? (
            <p className="empty">No run recorded yet.</p>
          ) : (
            <>
              <div className="figures">
                <div><span className="k">Submitted</span><span className="v">{burst.submitted}</span></div>
                <div><span className="k">Executed</span><span className={`v ${burst.executed ? 'proof' : ''}`}>{burst.executed}</span></div>
                <div><span className="k">Refused</span><span className={`v ${burst.submitted - burst.executed ? 'red' : ''}`}>{burst.submitted - burst.executed}</span></div>
              </div>
              {Object.keys(burst.top_reasons).length > 0 && (
                <table>
                  <thead><tr><th>Gate rule that refused</th><th className="r">Count</th></tr></thead>
                  <tbody>
                    {Object.entries(burst.top_reasons)
                      .sort((a, b) => b[1] - a[1])
                      .map(([k, v]) => (
                        <tr key={k}><td>{ruleName(k)}</td><td className="r mono">{v}</td></tr>
                      ))}
                  </tbody>
                </table>
              )}
            </>
          )}
        </section>

        <section>
          <h2 className="section">Suspensions <span className="subtle" style={{ font: '400 14px var(--sans)', marginLeft: 6 }}>{d ? `${d.suspended_reviewers.length} active` : ''}</span></h2>
          {!d?.suspensions?.length ? (
            <p className="empty">No reviewer has been suspended.</p>
          ) : (
            <table>
              <thead><tr><th>Reviewer</th><th>Rule</th><th>By</th><th className="r">When</th></tr></thead>
              <tbody>
                {d.suspensions.map((s) => (
                  <tr key={s.suspension_id}>
                    <td className="mono">{s.reviewer_id} {s.active && <span className="tag red">active</span>}</td>
                    <td className="mono">{s.rule}</td>
                    <td>{s.source.replaceAll('_', ' ')}</td>
                    <td className="r mono subtle">{when(s.ts)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>
    </>
  )
}
