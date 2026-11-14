import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { api, ruleName, secs, type Policy } from '../api'
import { Banner, Card, PageHead, Stats, useDashboard, type Tone } from '../ui'
import { errText } from './Review'

const REVIEWERS = ['dr-demo', 'dr-stamper', 'dr-skim', 'dr-cardio', 'dr-expired', 'vol-1', 'vol-2', 'vol-3']
const when = (t?: string) => (t ? new Date(t).toLocaleTimeString() : '—')

export default function Supervisor() {
  const qc = useQueryClient()
  const dash = useDashboard()
  const policies = useQuery({ queryKey: ['policy'], queryFn: () => api<Policy[]>('/api/policies') })
  const active = policies.data?.find((p) => p.status === 'active')
  const [floorS, setFloorS] = useState('')
  const [who, setWho] = useState('dr-stamper')
  const [paused, setPaused] = useState<boolean | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [msg, setMsg] = useState<{ tone: Tone; title: string; lines?: string[] } | null>(null)

  async function act(name: string, fn: () => Promise<{ tone: Tone; title: string; lines?: string[] }>) {
    setBusy(name)
    try {
      setMsg(await fn())
      qc.invalidateQueries()
    } catch (e) {
      setMsg({ tone: 'bad', title: 'Refused', lines: [errText(e)] })
    } finally {
      setBusy(null)
    }
  }

  const setFloor = () =>
    act('floor', async () => {
      const ms = Math.round(Number(floorS) * 1000)
      if (!Number.isFinite(ms) || ms < 1000 || ms > 600000) throw new Error('Enter a floor between 1 and 600 seconds.')
      const r = await api<{ version: number; superseded_version: number }>('/api/policies', {
        rules: { min_active_dwell_ms: ms },
        rationale: `Supervisor set dwell floor to ${secs(ms)}`,
      })
      setFloorS('')
      return { tone: 'good', title: `Policy v${r.version} is now active`, lines: [`v${r.superseded_version} superseded in the same transaction. New floor ${secs(ms)}; gate decisions cite the version they used.`] }
    })

  const halt = () =>
    act('halt', async () => {
      await api('/api/suspensions', { reviewer_id: who, reason: 'SUPERVISOR_HALT' })
      return { tone: 'bad', title: `${who} suspended`, lines: ['Grants revoked, pending approvals sent back to review, executed denials queued to reopen with read-back.'] }
    })

  const togglePause = () =>
    act('pause', async () => {
      const r = await api<{ paused: boolean }>('/api/agent/pause', { paused: !paused })
      setPaused(r.paused)
      return { tone: 'info', title: r.paused ? 'Agent paused' : 'Agent resumed', lines: [r.paused ? 'The executor will not request any grant until resumed.' : 'The executor will pick up approved proposals again.'] }
    })

  const d = dash.data
  const burst = d?.last_burst

  return (
    <>
      <PageHead title="Supervisor" sub="Change the review policy, halt a reviewer, or stop the agent. Every control writes to Atlas inside a transaction." />
      <Stats />
      {msg && <Banner tone={msg.tone} title={msg.title} lines={msg.lines} />}

      <div className="sup-grid">
        <Card title="Review policy" hint={active ? <span className="badge mono">v{active.version} active</span> : undefined}>
          <div className="card-body section-gap">
            <dl className="kv">
              <dt>Minimum server-timed dwell per case</dt>
              <dd>{secs(Number(active?.rules.min_active_dwell_ms))}</dd>
              <dt>Minimum time on each cited item</dt>
              <dd>{secs(Number(active?.rules.min_item_active_ms))}</dd>
              {Object.entries(active?.rules ?? {})
                .filter(([k]) => !['min_active_dwell_ms', 'min_item_active_ms'].includes(k))
                .map(([k, v]) => (
                  <div key={k} style={{ display: 'contents' }}>
                    <dt>{k.replace(/_ms$/, '').replaceAll('_', ' ').replace(/^./, (c) => c.toUpperCase())}</dt>
                    <dd>{k.endsWith('_ms') ? secs(Number(v)) : typeof v === 'boolean' ? (v ? 'Required' : 'Off') : String(v)}</dd>
                  </div>
                ))}
            </dl>
            <form
              className="row"
              style={{ alignItems: 'flex-end' }}
              onSubmit={(e) => {
                e.preventDefault()
                setFloor()
              }}
            >
              <label className="field" style={{ flex: 1 }}>
                New dwell floor (seconds)
                <input type="number" min={1} max={600} step={1} inputMode="numeric" value={floorS} onChange={(e) => setFloorS(e.target.value)} placeholder="e.g. 45" />
              </label>
              <button className="btn primary" disabled={!floorS || !!busy}>
                Publish v{(active?.version ?? 0) + 1}
              </button>
            </form>
          </div>
        </Card>

        <Card title="Controls">
          <div className="card-body section-gap">
            <div className="row" style={{ alignItems: 'flex-end' }}>
              <label className="field" style={{ flex: 1 }}>
                Halt a reviewer
                <select value={who} onChange={(e) => setWho(e.target.value)}>
                  {REVIEWERS.map((r) => (
                    <option key={r}>{r}</option>
                  ))}
                </select>
              </label>
              <button className="btn danger" onClick={halt} disabled={!!busy}>
                Suspend
              </button>
            </div>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--ink-2)' }}>Agent executor</div>
                <div className="subtle" style={{ fontSize: 13 }}>
                  {paused === null ? 'State shown after the first change' : paused ? 'Paused: no grants requested' : 'Running'}
                </div>
              </div>
              <button className="btn" onClick={togglePause} disabled={!!busy}>
                {paused ? 'Resume agent' : 'Pause agent'}
              </button>
            </div>
          </div>
        </Card>

        <Card title="Last agent run" hint={burst ? `${burst.submitted} submitted` : undefined}>
          <div className="card-body">
            {!burst ? (
              <div className="empty">No run recorded yet.</div>
            ) : (
              <>
                <div className="facts" style={{ marginBottom: 12 }}>
                  <div className="f"><span className="k">Executed</span><span className={`v ${burst.executed ? 'good-text' : ''}`}>{burst.executed}</span></div>
                  <div className="f"><span className="k">Refused</span><span className={`v ${burst.submitted - burst.executed ? 'bad-text' : ''}`}>{burst.submitted - burst.executed}</span></div>
                </div>
                {Object.keys(burst.top_reasons).length > 0 && (
                  <table>
                    <thead><tr><th>Gate rule that refused</th><th style={{ textAlign: 'right' }}>Count</th></tr></thead>
                    <tbody>
                      {Object.entries(burst.top_reasons)
                        .sort((a, b) => b[1] - a[1])
                        .map(([k, v]) => (
                          <tr key={k}><td>{ruleName(k)}</td><td className="mono" style={{ textAlign: 'right' }}>{v}</td></tr>
                        ))}
                    </tbody>
                  </table>
                )}
              </>
            )}
          </div>
        </Card>

        <Card title="Suspensions" hint={d ? `${d.suspended_reviewers.length} active` : undefined}>
          <div className="card-body">
            {!d?.suspensions?.length ? (
              <div className="empty">No reviewer has been suspended.</div>
            ) : (
              <table>
                <thead><tr><th>Reviewer</th><th>Rule</th><th>By</th><th>When</th></tr></thead>
                <tbody>
                  {d.suspensions.map((s) => (
                    <tr key={s.suspension_id}>
                      <td className="mono">{s.reviewer_id} {s.active && <span className="badge bad">Active</span>}</td>
                      <td><span className="badge mono">{s.rule}</span></td>
                      <td>{s.source}</td>
                      <td className="mono subtle">{when(s.ts)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Card>
      </div>
    </>
  )
}
