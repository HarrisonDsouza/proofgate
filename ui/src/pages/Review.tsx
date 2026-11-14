import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError, ruleName, secs, store, TENANT, type Policy, type QueueItem, type RunOnce, type Session } from '../api'
import { useHeartbeat } from '../useHeartbeat'

const REVIEWERS = ['dr-demo', 'dr-stamper', 'dr-skim', 'dr-cardio', 'dr-expired', 'vol-1', 'vol-2', 'vol-3']

type Result = { tone: 'good' | 'bad' | 'info'; title: string; lines: string[] }

function reasons(r: Record<string, number>) {
  return Object.entries(r)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `${ruleName(k)}: refused ${v}`)
}

function errText(e: unknown) {
  if (e instanceof ApiError) {
    if (e.status === 401) return 'Console key missing or wrong (top right).'
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
  const allOpened = cited.every((e) => (credited[e.evidence_id] ?? -1) >= 0)
  const ready = cited.length > 0 && allOpened && total >= floor && cited.every((e) => (credited[e.evidence_id] ?? 0) >= itemFloor)

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
    const r = await api<{ view_token: string; content: string }>(`/api/cases/${picked.case_id}/evidence/${eid}`)
    setCredited((c) => ({ ...c, [eid]: c[eid] ?? 0 }))
    setOpen({ eid, token: r.view_token, content: r.content })
  }

  async function runAgent(title: string, submitted?: number) {
    const r = await api<RunOnce>('/api/agent/run-once', {})
    const n = submitted ?? r.submitted
    const dash = await api<{ suspended_reviewers: string[] }>('/api/dashboard')
    const suspended = dash.suspended_reviewers.includes(session?.reviewer_id ?? '')
    const lines = [`Executed ${r.executed} of ${n}. Refused ${n - r.executed}.`, ...reasons(r.top_reasons)]
    if (suspended) lines.push(`${session?.reviewer_id} is SUSPENDED: grants revoked, pending approvals sent back to review.`)
    setResult({ tone: r.executed > 0 && !suspended ? 'good' : 'bad', title, lines })
    qc.invalidateQueries()
  }

  async function approve() {
    if (!picked) return
    setBusy('approve')
    try {
      if (open) await api(`/api/views/${open.token}/close`, {})
      setOpen(null)
      await api('/api/approvals', { proposal_id: picked.proposal_id, attestation_text: attest })
      await runAgent(`Case ${picked.case_id}`, 1)
    } catch (e) {
      setResult({ tone: 'bad', title: 'Approval refused', lines: [errText(e)] })
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
    <div className="review">
      <section className="panel sessionbar">
        <label>
          Reviewer
          <select value={who} onChange={(e) => setWho(e.target.value)}>
            {REVIEWERS.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
        </label>
        <button className="primary" onClick={start} disabled={busy === 'session'}>
          {session ? 'New session' : 'Start session'}
        </button>
        {session && (
          <span className="muted mono">
            {session.reviewer_id} · {session.specialty ?? '—'} · session {session.session_id}
          </span>
        )}
        <span className="spacer" />
        <button className="danger" onClick={bulk} disabled={!session || !!busy} title="The rubber-stamp button. Try it.">
          Select all, approve 50
        </button>
      </section>

      {result && (
        <section className={`result ${result.tone}`} role="status">
          <strong>{result.title}</strong>
          {result.lines.map((l) => (
            <div key={l}>{l}</div>
          ))}
          {picked && result.tone !== 'info' && <Link to={`/examiner/${picked.case_id}`}>Open the examiner for {picked.case_id} →</Link>}
        </section>
      )}

      <div className="cols">
        <section className="panel queue">
          <h2>Queue</h2>
          {!session && <p className="muted">Start a session to see the cases routed to your specialty.</p>}
          {queue.isError && <p className="bad-text">{errText(queue.error)}</p>}
          {queue.data?.length === 0 && <p className="muted">Nothing awaiting review.</p>}
          <ul>
            {queue.data?.map((p) => (
              <li key={p.proposal_id}>
                <button className={`qitem ${picked?.proposal_id === p.proposal_id ? 'on' : ''}`} onClick={() => pick(p)}>
                  <span className="mono">{p.case_id}</span>
                  <span>{p.summary}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel case">
          {!picked ? (
            <p className="muted">Pick a case. The agent has proposed a denial; it cannot run until you review the evidence it cited.</p>
          ) : (
            <>
              <header className="casehead">
                <div>
                  <h2 className="mono">{picked.case_id}</h2>
                  <p>{picked.summary}</p>
                </div>
                <div className="amount mono">${picked.billed_amount?.toLocaleString()}</div>
              </header>
              <div className="agent">
                <span className="label">Agent proposes</span> <strong>DENY</strong>
                <p>{picked.rationale}</p>
              </div>

              <h3>Evidence the agent cited</h3>
              <ol className="evidence">
                {picked.all_evidence.map((e) => {
                  const isCited = cited.some((c) => c.evidence_id === e.evidence_id)
                  const ms = credited[e.evidence_id]
                  return (
                    <li key={e.evidence_id} className={open?.eid === e.evidence_id ? 'open' : ''}>
                      <button onClick={() => openEvidence(e.evidence_id)}>
                        <span className="mono">{e.evidence_id}</span> {e.label}
                        {isCited && <span className="tag">cited</span>}
                      </button>
                      <span className={`mono ${ms !== undefined && ms >= itemFloor ? 'good-text' : 'muted'}`}>
                        {ms === undefined ? 'not opened' : secs(ms)}
                      </span>
                    </li>
                  )
                })}
              </ol>
              {open && <pre className="doc">{open.content}</pre>}

              <div className="meter" aria-label="server-credited review time">
                <div className="bar">
                  <i style={{ width: `${Math.min(100, (total / floor) * 100)}%` }} />
                </div>
                <div className="mono">
                  {secs(total)} credited by the server · floor {secs(floor)} (policy v{active?.version ?? '?'})
                </div>
                <small className="muted">
                  Counted only while this tab is visible and you have used it in the last 15 s. The browser cannot add time.
                </small>
              </div>

              <label className="attest">
                Attestation
                <textarea
                  value={attest}
                  onChange={(e) => setAttest(e.target.value)}
                  placeholder="What did you check? e.g. Prior-auth letter covers a different code than the one billed."
                />
              </label>
              <div className="actions">
                <button className="primary" onClick={approve} disabled={!!busy}>
                  Approve denial
                </button>
                <span className="muted">
                  {ready ? 'Review requirements met. The gate will still check.' : 'You can press it early: the gate will refuse and say why.'}
                </span>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  )
}
