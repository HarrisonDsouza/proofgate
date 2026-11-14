import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, Pause, Stamp } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError, refusalReason, secs, store, TENANT, type Policy, type QueueItem, type RunOnce, type Session } from '../api'
import { useHeartbeat } from '../useHeartbeat'
import { Notice, Spin, Title, type Tone } from '../ui'
import { SpeakAttestation } from '../voice/SpeakAttestation'

const REVIEWERS = ['dr-demo', 'dr-stamper', 'dr-skim', 'dr-cardio', 'dr-expired', 'vol-1', 'vol-2', 'vol-3']

type Result = { tone: Tone; head: string; lines: string[]; caseId?: string; denied?: boolean }

function reasons(r: Record<string, number>) {
  return Object.entries(r)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `Refused ${v}: ${refusalReason(k)}`)
}

export function errText(e: unknown) {
  if (e instanceof ApiError) {
    if (e.status === 401) return 'Console key missing or wrong. Paste it in the top right.'
    const b = e.body as { detail?: unknown; error?: unknown } | null
    const d = b?.detail ?? b?.error ?? b
    return `${e.status}: ${typeof d === 'string' ? d : JSON.stringify(d)}`
  }
  return e instanceof Error ? e.message : String(e)
}

export default function Review() {
  const qc = useQueryClient()
  const [session, setSession] = useState<Session | null>(store.session())
  const [who, setWho] = useState(session?.reviewer_id ?? 'dr-demo')
  const [picked, setPicked] = useState<QueueItem | null>(null)
  const [open, setOpen] = useState<{ eid: string; token: string; content: string } | null>(null)
  const [credited, setCredited] = useState<Record<string, number>>({})
  const [attest, setAttest] = useState('')
  const [attId, setAttId] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [opening, setOpening] = useState<string | null>(null)
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

  const { live, flush } = useHeartbeat(open?.token ?? null)
  const liveServer = live?.serverMs
  useEffect(() => {
    // Only apply a heartbeat to the document it belongs to (the token check), never to the next one opened.
    if (open && live && live.token === open.token) setCredited((c) => (c[open.eid] === live.serverMs ? c : { ...c, [open.eid]: live.serverMs }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveServer, open?.token])
  const shown = (eid: string) => {
    const base = credited[eid]
    if (!opening && open?.eid === eid && live && live.token === open.token) return Math.max(base ?? 0, live.shownMs)
    return base
  }

  const total = Object.keys(credited).reduce((a, k) => a + (shown(k) ?? 0), 0)
  const cited = picked?.cited_evidence ?? []
  const ready = cited.length > 0 && total >= floor && cited.every((e) => (shown(e.evidence_id) ?? 0) >= itemFloor)

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
      setResult({ tone: 'bad', head: 'Could not start a session', lines: [errText(e)] })
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
    if (!picked || opening || open?.eid === eid) return
    setOpening(eid)
    try {
      if (open) {
        const ms = await flush() // credit the time since the last heartbeat before the server closes this view
        if (ms != null) setCredited((c) => ({ ...c, [open.eid]: Math.max(c[open.eid] ?? 0, ms) }))
      }
      const r = await api<{ view_token: string; content: string }>(`/api/cases/${picked.case_id}/evidence/${eid}`)
      setCredited((c) => ({ ...c, [eid]: c[eid] ?? 0 }))
      setOpen({ eid, token: r.view_token, content: r.content })
    } catch (e) {
      setResult({ tone: 'bad', head: 'Could not open that document', lines: [errText(e)] })
    } finally {
      setOpening(null)
    }
  }

  async function runAgent(title: string, submitted?: number, caseId?: string) {
    const r = await api<RunOnce>('/api/agent/run-once', {})
    const n = submitted ?? r.submitted
    const dash = await api<{ suspended_reviewers: string[] }>('/api/dashboard')
    const suspended = dash.suspended_reviewers.includes(session?.reviewer_id ?? '')
    const head = `Executed ${r.executed} of ${n}` + (suspended ? ` · ${session?.reviewer_id} suspended` : '')
    const sentBack = Math.max(0, n - r.submitted)
    const lines = [
      `${title}: the gate refused ${r.submitted - r.executed}` + (sentBack ? `; ${sentBack} sent back to review by the suspension before reaching it.` : '.'),
      ...reasons(r.top_reasons),
    ]
    if (suspended) lines.push('Grants revoked, pending approvals sent back to review, executed denials queued to reopen.')
    if (r.executed > 0 && !suspended) lines.push('Denial executed and read back from the claims system.')
    const ok = r.executed > 0 && !suspended
    setResult({ tone: ok ? 'good' : 'bad', head, lines, caseId, denied: ok })
    qc.invalidateQueries()
  }

  async function approve() {
    if (!picked) return
    setBusy('approve')
    try {
      if (open) {
        await flush()
        await api(`/api/views/${open.token}/close`, {})
      }
      setOpen(null)
      await api('/api/approvals', { proposal_id: picked.proposal_id, attestation_text: attest, attestation_id: attId ?? undefined })
      setAttId(null)
      await runAgent(`Case ${picked.case_id}`, 1, picked.case_id)
    } catch (e) {
      setResult({ tone: 'bad', head: 'Approval refused', lines: [errText(e)], caseId: picked.case_id })
    } finally {
      setBusy(null)
    }
  }

  async function bulk() {
    setBusy('bulk')
    setResult({ tone: 'info', head: 'Approving 50 in one click…', lines: ['Each one goes through the gate transaction in Atlas.'] })
    try {
      const ids = (await api<QueueItem[]>('/api/queue?limit=50')).map((p) => p.proposal_id)
      await api('/api/approvals/bulk', { proposal_ids: ids, attestation_text: 'Reviewed in batch.' })
      await runAgent(`Select all, approve ${ids.length}`, ids.length)
    } catch (e) {
      setResult({ tone: 'bad', head: 'Bulk approval refused', lines: [errText(e)] })
    } finally {
      setBusy(null)
    }
  }

  return (
    <>
      <Title
        title="Review"
        sub="The agent proposes claim denials. None can execute until a credentialed reviewer has opened every document it cited, timed by the server."
      />

      {result && (
        <Notice
          tone={result.tone}
          head={result.head}
          lines={result.lines}
          stamp={result.denied ? { text: 'DENIED', sub: `GATE ALLOWED · v${active?.version ?? ''}`, ink: 'red' } : result.tone === 'bad' && result.head.startsWith('Executed 0') ? { text: 'REFUSED', sub: 'NO GRANT ISSUED', ink: 'red' } : undefined}
          action={result.caseId && result.tone !== 'info' ? <Link className="btn" to={`/examiner/${result.caseId}`}>Examiner <ArrowRight aria-hidden /></Link> : undefined}
        />
      )}

      <div className="deskbar">
        <label className="field">
          Reviewer
          <select value={who} onChange={(e) => setWho(e.target.value)}>
            {REVIEWERS.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
        </label>
        <button className="btn ink" onClick={start} disabled={busy === 'session'}>
          {busy === 'session' && <Spin />}
          {session ? 'New session' : 'Start session'}
        </button>
        {session && (
          <span className="who">
            Signed in as <b className="mono">{session.reviewer_id}</b>
            {session.specialty && <> · {session.specialty}</>}
          </span>
        )}
        <span className="spacer" />
        <button className="btn redline" onClick={bulk} disabled={!session || !!busy} title="The rubber-stamp button. The gate refuses it.">
          {busy === 'bulk' && <Spin />}
          Select all · approve 50
        </button>
      </div>

      <div className="desk">
        <div className="queue">
          <h2 className="section">Queue{queue.data ? <span className="subtle" style={{ font: '400 14px var(--sans)', marginLeft: 8 }}>{queue.data.length} cases</span> : null}</h2>
          {!session && <p className="empty">Start a session to see the cases routed to your specialty.</p>}
          {queue.isLoading && <p className="empty"><Spin /> Loading cases from Atlas…</p>}
          {queue.isError && <p className="empty red">{errText(queue.error)}</p>}
          {queue.data?.length === 0 && <p className="empty">Nothing awaiting review.</p>}
          {!!queue.data?.length && (
            <ul className="qlist">
              {queue.data.map((p) => (
                <li key={p.proposal_id}>
                  <button className={`qrow ${picked?.proposal_id === p.proposal_id ? 'on' : ''}`} onClick={() => pick(p)} aria-current={picked?.proposal_id === p.proposal_id}>
                    <span className="id">{p.case_id}</span>
                    <span className="sum">{p.summary}</span>
                    <span className="amt">${p.billed_amount?.toLocaleString()}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {!picked ? (
          <div className="file">
            <p className="empty">Pick a case. The agent has proposed a denial; it cannot run until you have read the documents it cited.</p>
          </div>
        ) : (
          <article className="file">
            <div className="filehead">
              <h2>{picked.case_id}</h2>
              <div className="amount">
                <div className="k">Billed</div>
                <div className="v">${picked.billed_amount?.toLocaleString()}</div>
              </div>
              <p className="proposal">
                The agent proposes to <b>deny</b>. {picked.rationale}
              </p>
            </div>

            <div>
              <h2 className="section">
                Documents <span className="subtle" style={{ font: '400 14px var(--sans)', marginLeft: 6 }}>{cited.filter((e) => (shown(e.evidence_id) ?? 0) >= itemFloor).length} of {cited.length} required documents read ({secs(itemFloor)} each)</span>
              </h2>
              <div className="docs">
                {picked.all_evidence.map((e) => {
                  const isCited = cited.some((c) => c.evidence_id === e.evidence_id)
                  const ms = shown(e.evidence_id)
                  const met = ms !== undefined && ms >= itemFloor
                  const isOpen = open?.eid === e.evidence_id
                  const isOpening = opening === e.evidence_id
                  return (
                    <button key={e.evidence_id} className={`doc ${isOpen ? 'open' : ''} ${met ? 'met' : ''}`} onClick={() => openEvidence(e.evidence_id)} disabled={!!opening && !isOpening} aria-busy={isOpening}>
                      <span className="top">
                        <span className="eid">{e.evidence_id}</span>
                        {isCited && <span className="tag red" title="The agent based its denial on this document. You must read it.">required</span>}
                      </span>
                      <span className="label">{e.label}</span>
                      <span className="ticks" aria-hidden>
                        <i style={{ width: `${Math.min(100, ((ms ?? 0) / itemFloor) * 100)}%` }} />
                      </span>
                      <span className="time">
                        <span>
                          {isOpening ? <><Spin /> opening…</> : ms === undefined ? 'not opened' : isOpen ? (!live || live.counting ? 'reading' : <span className="paused"><Pause aria-hidden /> paused</span>) : met ? 'done' : 'opened'}
                        </span>
                        <b>{ms === undefined ? '' : secs(ms)}</b>
                      </span>
                    </button>
                  )
                })}
              </div>
              {open && !opening && live && !live.counting && (
                <p className="pausenote" role="status">
                  <Pause aria-hidden /> Timer paused. Scroll, click or type to keep counting: the server only credits time while you are using this tab.
                </p>
              )}
              {open && <div className="reader" style={{ marginTop: 14 }}>{open.content}</div>}
            </div>

            <div className="tallyline" aria-label="Server-credited review time">
              <span className={`big ${total >= floor ? 'met' : ''}`}>{secs(total)}</span>
              <span className="of">
                review time · policy floor {secs(floor)}
                {live?.pending && <> · <Spin /> saving to Atlas</>}
              </span>
              <span className={`ticks ${total >= floor ? 'met' : ''}`} aria-hidden>
                <i style={{ width: `${Math.min(100, (total / floor) * 100)}%` }} />
              </span>
              <small>Counts only while this tab is visible and you have scrolled, clicked or typed in the last 15 s. The server confirms the time every 2 s; the browser cannot add time.</small>
            </div>

            <SpeakAttestation
              caseId={picked.case_id}
              typedText={attest}
              onAttested={(a) => {
                setAttId(a.attestation_id)
                setAttest(a.transcript)
              }}
            />
            <div className="sign">
              <label>
                Attestation
                <textarea
                  value={attest}
                  onChange={(e) => setAttest(e.target.value)}
                  placeholder="What did you check?"
                />
              </label>
              <button className="btn ink lg" onClick={approve} disabled={!!busy}>
                {busy === 'approve' ? <><Spin /> Checking in Atlas…</> : <><Stamp aria-hidden /> Approve denial</>}
              </button>
            </div>
            <p className={`hint ${ready ? 'met' : ''}`} style={{ margin: '-12px 0 0' }}>
              {ready ? 'Review requirements met. The gate still checks everything again in one transaction.' : 'You can approve early: the gate will refuse and say which rule failed.'}
            </p>
          </article>
        )}
      </div>
    </>
  )
}
