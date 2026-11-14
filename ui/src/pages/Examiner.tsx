import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, ruleName, secs } from '../api'

/* eslint-disable @typescript-eslint/no-explicit-any */
type Ex = Record<string, any>

const when = (t?: string) => (t ? new Date(t).toLocaleTimeString() : '—')

function Step({ n, title, ok, children }: { n: number; title: string; ok?: boolean | null; children: React.ReactNode }) {
  return (
    <li className="step">
      <div className={`dot ${ok === true ? 'good' : ok === false ? 'bad' : ''}`} aria-label={`Step ${n}${ok === true ? ', passed' : ok === false ? ', failed' : ''}`}>
        {ok === true ? '✓' : ok === false ? '✗' : n}
      </div>
      <div className="body">
        <h3>{title}</h3>
        {children}
      </div>
    </li>
  )
}

function Verdict({ d }: { d: Ex }) {
  const g = d.gate_decisions?.at(-1)
  if (!g) return <div className="result info verdict"><strong>{d.case.case_id}: no gate decision yet</strong></div>
  const failed = (g.checks ?? []).filter((c: any) => !c.pass)
  const nChecks = (g.checks ?? []).length
  if (g.decision === 'ALLOW') {
    const reopened = d.compensation?.status === 'confirmed'
    return (
      <div className={`result ${reopened ? 'bad' : 'good'} verdict`}>
        <strong>
          {reopened ? 'ALLOWED, then REOPENED' : 'ALLOWED'} · server dwell {secs(d.approval?.active_dwell_ms)} · {nChecks - failed.length}/{nChecks} checks
          {d.denial ? ` · denial ${d.denial.status}` : ''}
          {d.denial?.readback ? `, read back ${d.denial.readback.status}` : ''}
        </strong>
      </div>
    )
  }
  return (
    <div className="result bad verdict">
      <strong>REFUSED · {failed.length ? ruleName(failed[0].rule) : 'see checks'}</strong>
      {failed.length > 1 && <div>Also failed: {failed.slice(1).map((c: any) => ruleName(c.rule)).join(' · ')}</div>}
    </div>
  )
}

export default function Examiner() {
  const { caseId } = useParams()
  const nav = useNavigate()
  const [input, setInput] = useState(caseId ?? 'CLM-A-0003')
  const q = useQuery({
    queryKey: ['examiner', caseId],
    queryFn: () => api<Ex>(`/api/examiner/cases/${caseId}`),
    enabled: !!caseId,
    refetchInterval: 2000,
  })
  const d = q.data

  return (
    <div className="examiner">
      <form
        className="panel sessionbar"
        onSubmit={(e) => {
          e.preventDefault()
          nav(`/examiner/${input.trim()}`)
        }}
      >
        <label>
          Case
          <input className="mono" value={input} onChange={(e) => setInput(e.target.value)} />
        </label>
        <button className="primary">Rebuild from Atlas</button>
        <span className="muted">Everything below is read from stored documents, not from logs or this browser.</span>
      </form>

      {q.isLoading && <p className="muted">Reading {caseId} from Atlas…</p>}
      {q.isError && <p className="result bad">Could not load {caseId}.</p>}
      {d && !d.case && <p className="result bad">No case {caseId} in this tenant.</p>}
      {d?.case && <Verdict d={d} />}
      {d?.case && (
        <ol className="timeline">
          <Step n={1} title="Agent proposal" ok={!!d.proposal}>
            {d.proposal ? (
              <>
                <p>
                  <span className="mono">{d.proposal.agent_id}</span> proposed <strong>{d.proposal.recommendation?.toUpperCase()}</strong> ·
                  operator <span className="mono">{d.proposal.operator_id}</span> · status <span className="tag">{d.proposal.status}</span>
                </p>
                <p className="muted">{d.proposal.rationale}</p>
                <p>
                  Cited:{' '}
                  {d.proposal.cited_evidence?.map((c: any) => (
                    <span key={c.evidence_id} className="tag mono">
                      {c.evidence_id}
                    </span>
                  ))}
                </p>
              </>
            ) : (
              <p className="muted">No proposal.</p>
            )}
          </Step>

          <Step n={2} title="What the reviewer opened, timed by the server" ok={d.views?.length ? true : null}>
            {d.views?.length ? (
              <table>
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>Active</th>
                    <th>Open</th>
                    <th>Evidence hash</th>
                  </tr>
                </thead>
                <tbody>
                  {d.views.map((v: any) => (
                    <tr key={v.evidence_id + v.opened_at}>
                      <td className="mono">{v.evidence_id}</td>
                      <td className="mono">{secs(v.active_ms)}</td>
                      <td className="mono">
                        {secs(v.open_ms)} {v.idle_flag && <span className="tag bad">mostly idle</span>}
                      </td>
                      <td className="mono muted">{String(v.evidence_hash ?? v.hash ?? '').slice(0, 12)}…</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="muted">No evidence views recorded for the latest approval.</p>
            )}
          </Step>

          <Step n={3} title="Approval" ok={d.approval ? d.approval.status !== 'invalidated' : null}>
            {d.approval ? (
              <>
                <p>
                  <span className="mono">{d.approval.reviewer_id}</span> · server dwell <b className="mono">{secs(d.approval.active_dwell_ms)}</b> ·
                  status <span className="tag">{d.approval.status}</span> · {when(d.approval.created_at)}
                </p>
                {d.approval.attestation_text && <blockquote>{d.approval.attestation_text}</blockquote>}
                {d.approval.client_supplied_ignored && Object.values(d.approval.client_supplied_ignored).some((v) => v != null) && (
                  <p className="muted">
                    The browser also sent: <code>{JSON.stringify(d.approval.client_supplied_ignored).slice(0, 120)}</code> — stored and ignored.
                  </p>
                )}
                <p className="muted">
                  Dwell recomputed from heartbeat events: <span className="mono">{secs(d.chain?.dwell_recomputed_ms)}</span>{' '}
                  {d.chain?.dwell_matches ? '✓ matches' : '✗ does not match'} · review-event hash chain{' '}
                  {d.chain?.review_events_ok ? '✓ intact' : '✗ broken'}
                </p>
              </>
            ) : (
              <p className="muted">Not approved.</p>
            )}
          </Step>

          <Step n={4} title="Gate decisions (one Atlas transaction each)" ok={d.gate_decisions?.length ? d.gate_decisions.at(-1).decision === 'ALLOW' : null}>
            {d.gate_decisions?.length ? (
              d.gate_decisions.map((g: any) => (
                <div key={g.decision_id ?? g.ts} className="gate">
                  <p>
                    <span className={`tag ${g.decision === 'ALLOW' ? 'good' : 'bad'}`}>{g.decision}</span> policy v{g.policy_version} ·
                    transaction attempts <b className="mono">{g.txn_attempts}</b> · {when(g.ts)}
                  </p>
                  <ul className="checks">
                    {g.checks?.map((c: any) => (
                      <li key={c.rule} className={c.pass ? 'good-text' : 'bad-text'}>
                        <span className="mono">{c.pass ? '✓' : '✗'}</span> {ruleName(c.rule)}
                        {!c.pass && c.detail && <span className="muted"> — {c.detail}</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              ))
            ) : (
              <p className="muted">The gate has not been called for this case.</p>
            )}
          </Step>

          <Step n={5} title="Claims system" ok={d.denial ? d.denial.status === 'CONFIRMED' : null}>
            {d.denial ? (
              <p>
                Denial <span className="mono">{d.denial.denial_id}</span> <span className="tag">{d.denial.status}</span>
                {d.denial.readback && (
                  <>
                    {' '}
                    · read back: <span className="mono">{d.denial.readback.status}</span>
                  </>
                )}
                {d.grant && (
                  <>
                    {' '}
                    · single-use grant <span className="tag">{d.grant.status}</span>
                  </>
                )}
              </p>
            ) : (
              <p className="muted">No denial executed.</p>
            )}
            {d.target_log?.length > 0 && (
              <ul className="log mono">
                {d.target_log.map((t: any, i: number) => (
                  <li key={i} className={/REFUSED/.test(t.outcome) ? 'bad-text' : ''}>
                    {when(t.ts)} {t.op} → {t.outcome} <span className="muted">by {t.caller}</span>
                  </li>
                ))}
              </ul>
            )}
          </Step>

          <Step n={6} title="Suspension and reopen" ok={d.suspension ? (d.compensation ? d.compensation.status === 'confirmed' : false) : d.approval ? true : null}>
            {d.suspension ? (
              <p>
                <span className="mono">{d.suspension.reviewer_id}</span> suspended by <b>{d.suspension.source}</b> · rule{' '}
                <span className="tag bad">{d.suspension.rule}</span> · {when(d.suspension.ts)}
              </p>
            ) : (
              <p className="muted">Reviewer not suspended.</p>
            )}
            {d.compensation && (
              <p>
                Denial reopened in the claims system: <span className="tag">{d.compensation.status}</span>
                {d.compensation.readback && <> · read back <span className="mono">{d.compensation.readback.status}</span></>}
              </p>
            )}
          </Step>
        </ol>
      )}
    </div>
  )
}
