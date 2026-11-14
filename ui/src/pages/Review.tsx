import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError, ruleName, secs, store, TENANT, type Policy, type QueueItem, type RunOnce, type Session } from '../api'
import { useHeartbeat } from '../useHeartbeat'
import { Banner, Card, PageHead, Stats, type Tone } from '../ui'

const REVIEWERS = ['dr-demo', 'dr-stamper', 'dr-skim', 'dr-cardio', 'dr-expired', 'vol-1', 'vol-2', 'vol-3']

type Result = { tone: Tone; title: string; lines: string[]; caseId?: string }

function reasons(r: Record<string, number>) {
  return Object.entries(r)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `${ruleName(k)}: refused ${v}`)
}

export function errText(e: unknown) {
  if (e instanceof ApiError) {
    if (e.status === 401) return 'Console key missing or wrong. Paste it in the sidebar.'
    const b = e.body as { detail?: unknown; error?: unknown } | null
    return `${e.status}: ${JSON.stringify(b?.detail ?? b?.error ?? b)}`
  }
  return String(e)
}

export default function Review() {
  const qc = useQueryClient()
  const [session, setSession] = useState<Session | null>(store.session())
  const [who, setWho] = useState(session?.reviewer_id ?? 'dr-demo')
  const [picked, setPicked] = useState<QueueItem | null>(null)
  const [open, setOpen] = useState<{ eid: string; token: string; content: string } | null>(null)
  const [credited, setCredited] = useState<Record<string, number>>({})
  const [attest, setAttest] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [result, setResult] = useState<Result | null>(null)

  const policy = useQuery({ queryKey: ['policy'], queryFn: () => api<Policy[]>('/api/policies') })
  const active = policy.data?.find((p) => p.status === 'active')
  const floor = Number(active?.rules.min_active_dwell_ms ?? 30000)
  const itemFloor = Number(active?.rules.min_item_active_ms ?? 5000)

  const queue = useQuery({
    queryKey: ['queue', session?.session_id],
    queryFn: () => api<QueueItem[]>('/api/queue?limit=12'),
    enabled: !!session,
  })

  const beat = useHeartbeat(open?.token ?? null)
  useEffect(() => {
    if (open && beat) setCredited((c) => ({ ...c, [open.eid]: beat.active_ms }))
  }, [beat, open])

  const total = Object.values(credited).reduce((a, b) => a + b, 0)
  const cited = picked?.cited_evidence ?? []
  const openedCited = cited.filter((e) => credited[e.evidence_id] !== undefined).length
  const ready = cited.length > 0 && total >= floor && cited.every((e) => (credited[e.evidence_id] ?? 0) >= itemFloor)

  async function start() {
    setBusy('session')
    setResult(null)
    try {
      const r = await api<{ session_id: string; reviewer: { specialty: string } }>('/api/sessions', { tenant_id: TENANT, reviewer_id: who })
      const s = { session_id: r.session_id, reviewer_id: who, specialty: r.reviewer?.specialty }
      store.setSession(s)
      setSession(s)
      setPicked(null)
      setOpen(null)
      setCredited({})
    } catch (e) {
      setResult({ tone: 'bad', title: 'Could not start a session', lines: [errText(e)] })
    } finally {
      setBusy(null)
    }
  }

  function pick(p: QueueItem) {
    setPicked(p)
    setOpen(null)
    setCredited({})
    setAttest('')
    setResult(null)
  }

  async function openEvidence(eid: string) {
    if (!picked) return
    try {
      const r = await api<{ view_token: string; content: string }>(`/api/cases/${picked.case_id}/evidence/${eid}`)
      setCredited((c) => ({ ...c, [eid]: c[eid] ?? 0 }))
      setOpen({ eid, token: r.view_token, content: r.content })
    } catch (e) {
      setResult({ tone: 'bad', title: 'Could not open evidence', lines: [errText(e)] })
    }
  }

  async function runAgent(title: string, submitted?: number, caseId?: string) {
    const r = await api<RunOnce>('/api/agent/run-once', {})
    const n = submitted ?? r.submitted
    const dash = await api<{ suspended_reviewers: string[] }>('/api/dashboard')
    const suspended = dash.suspended_reviewers.includes(session?.reviewer_id ?? '')
    const head = `Executed ${r.executed} of ${n}` + (suspended ? ` · ${session?.reviewer_id} suspended` : '')
    const lines = [`${title}: refused ${n - r.executed}.`, ...reasons(r.top_reasons)]
    if (suspended) lines.push('Grants revoked, pending approvals sent back to review, executed denials queued to reopen.')
    if (r.executed > 0 && !suspended) lines.push('Denial executed and read back from the claims system.')
    setResult({ tone: r.executed > 0 && !suspended ? 'good' : 'bad', title: head, lines, caseId })
    qc.invalidateQueries()
  }

  async function approve() {
    if (!picked) return
    setBusy('approve')
    try {
      if (open) await api(`/api/views/${open.token}/close`, {})
      setOpen(null)
      await api('/api/approvals', { proposal_id: picked.proposal_id, attestation_text: attest })
      await runAgent(`Case ${picked.case_id}`, 1, picked.case_id)
    } catch (e) {
      setResult({ tone: 'bad', title: 'Approval refused', lines: [errText(e)], caseId: picked.case_id })
    } finally {
      setBusy(null)
    }
  }

  async function bulk() {
    setBusy('bulk')
    setResult({ tone: 'info', title: 'Approving 50 in one click…', lines: ['Each one goes through the gate transaction in Atlas.'] })
    try {
      const ids = (await api<QueueItem[]>('/api/queue?limit=50')).map((p) => p.proposal_id)
      await api('/api/approvals/bulk', { proposal_ids: ids, attestation_text: 'Reviewed in batch.' })
      await runAgent(`Select all, approve ${ids.length}`, ids.length)
    } catch (e) {
      setResult({ tone: 'bad', title: 'Bulk approval refused', lines: [errText(e)] })
    } finally {
      setBusy(null)
    }
  }

  return (
    <>
      <PageHead
        title="Review queue"
        sub="The agent proposes claim denials. None can execute until a credentialed reviewer has opened every cited item, timed by the server."
      />
      <Stats />

      {result && (
        <Banner
          tone={result.tone}
          title={result.title}
          lines={result.lines}
          action={result.caseId && result.tone !== 'info' ? <Link className="btn" to={`/examiner/${result.caseId}`}>Open in examiner →</Link> : undefined}
        />
      )}

      <Card>
        <div className="toolbar">
          <label className="field">
            Reviewer
            <select value={who} onChange={(e) => setWho(e.target.value)}>
              {REVIEWERS.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
          </label>
          <button className="btn primary" onClick={start} disabled={busy === 'session'}>
            {session ? 'New session' : 'Start session'}
          </button>
          {session && (
            <div className="who">
              Signed in as <b className="mono">{session.reviewer_id}</b>
              {session.specialty && <> · <span className="badge">{session.specialty}</span></>}
            </div>
          )}
          <span className="spacer" />
          <button className="btn danger" onClick={bulk} disabled={!session || !!busy} title="The rubber-stamp button. The gate will refuse it.">
            Select all · approve 50
          </button>
        </div>
      </Card>

      <div className="review-grid">
        <Card title="Queue" hint={queue.data ? `${queue.data.length} shown` : undefined}>
          {!session && <div className="empty">Start a session to see the cases routed to your specialty.</div>}
          {queue.isError && <div className="empty bad-text">{errText(queue.error)}</div>}
          {queue.data?.length === 0 && <div className="empty">Nothing awaiting review.</div>}
          {!!queue.data?.length && (
            <ul className="queue-list">
              {queue.data.map((p) => (
                <li key={p.proposal_id}>
                  <button className={`qitem ${picked?.proposal_id === p.proposal_id ? 'on' : ''}`} onClick={() => pick(p)}>
                    <span className="id">{p.case_id}</span>
                    <span className="amt">${p.billed_amount?.toLocaleString()}</span>
                    <span className="sum">{p.summary}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          {!picked ? (
            <div className="empty" style={{ padding: '64px 24px' }}>
              Pick a case from the queue. The agent has proposed a denial; it cannot run until you review the evidence it cited.
            </div>
          ) : (
            <div className="card-body section-gap">
              <div>
                <div className="case-top">
                  <div>
                    <h2>{picked.case_id}</h2>
                    <div className="muted">{picked.summary}</div>
                  </div>
                  <div className="amount">
                    <div className="subtle" style={{ fontSize: 12 }}>Billed</div>
                    <div className="v">${picked.billed_amount?.toLocaleString()}</div>
                  </div>
                </div>
                <div className="proposal">
                  <div className="row">
                    <span className="eyebrow" style={{ margin: 0 }}>Agent proposal</span>
                    <span className="badge bad">Deny</span>
                  </div>
                  <p>{picked.rationale}</p>
                </div>
              </div>

              <div>
                <div className="row" style={{ marginBottom: 8 }}>
                  <p className="eyebrow" style={{ margin: 0 }}>Evidence</p>
                  <span className="subtle" style={{ fontSize: 13 }}>
                    {openedCited} of {cited.length} cited items opened
                  </span>
                </div>
                <div className="ev-list">
                  {picked.all_evidence.map((e) => {
                    const isCited = cited.some((c) => c.evidence_id === e.evidence_id)
                    const ms = credited[e.evidence_id]
                    const met = ms !== undefined && ms >= itemFloor
                    return (
                      <button key={e.evidence_id} className={`ev ${open?.eid === e.evidence_id ? 'open' : ''}`} onClick={() => openEvidence(e.evidence_id)}>
                        <span className="eid">{e.evidence_id}</span>
                        <span className="t">
                          <span>
                            {e.label} {isCited && <span className="badge accent">Cited</span>}
                          </span>
                          {ms !== undefined && (
                            <span className="mini" aria-hidden>
                              <i style={{ width: `${Math.min(100, (ms / itemFloor) * 100)}%` }} />
                            </span>
                          )}
                        </span>
                        <span className={`time ${met ? 'good-text' : 'subtle'}`}>{ms === undefined ? 'Not opened' : secs(ms)}</span>
                      </button>
                    )
                  })}
                </div>
                {open && <pre className="doc" style={{ marginTop: 12 }}>{open.content}</pre>}
              </div>

              <div className="meter" aria-label="Server-credited review time">
                <div className="top">
                  <span className="big">{secs(total)}</span>
                  <span className="of">credited by the server · floor {secs(floor)}</span>
                  <span className="spacer" />
                  <span className="badge mono">policy v{active?.version ?? '?'}</span>
                </div>
                <div className={`bar ${total >= floor ? 'done' : ''}`}>
                  <i style={{ width: `${Math.min(100, (total / floor) * 100)}%` }} />
                </div>
                <small className="muted">
                  Counted only while this tab is visible and you have used it in the last 15 s. The browser cannot add time.
                </small>
              </div>

              <label className="field">
                Attestation
                <textarea
                  value={attest}
                  onChange={(e) => setAttest(e.target.value)}
                  placeholder="What did you check? e.g. The prior-auth letter covers a different code than the one billed."
                />
              </label>
              <div className="approve-row">
                <button className="btn primary lg" onClick={approve} disabled={!!busy}>
                  {busy === 'approve' ? 'Checking in Atlas…' : 'Approve denial'}
                </button>
                <span className={ready ? 'good-text' : 'muted'} style={{ fontSize: 14 }}>
                  {ready ? '✓ Review requirements met. The gate will still check.' : 'You can press it early: the gate will refuse and say why.'}
                </span>
              </div>
            </div>
          )}
        </Card>
      </div>
    </>
  )
}
