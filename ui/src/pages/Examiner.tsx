import { useQuery } from '@tanstack/react-query'
import { Check, X } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, ruleName, secs } from '../api'
import { AgentTrace } from '../AgentTrace'
import { Notice, Title } from '../ui'

/* eslint-disable @typescript-eslint/no-explicit-any */
type Ex = Record<string, any>

const when = (t?: string) => (t ? new Date(t).toLocaleTimeString() : '—')

function Step({ n, title, ok, children }: { n: number; title: string; ok?: boolean | null; children: React.ReactNode }) {
  const tone = ok === true ? 'good' : ok === false ? 'bad' : ''
  return (
    <li className="entry">
      <div className={`n ${tone}`}>{n}</div>
      <div>
        <h3>{title}</h3>
        <div className={`state ${tone}`}>{ok === true ? 'recorded · consistent' : ok === false ? 'failed or reversed' : 'nothing recorded'}</div>
      </div>
      <div className="body">{children}</div>
    </li>
  )
}

function Verdict({ d }: { d: Ex }) {
  const g = d.gate_decisions?.at(-1)
  if (!g) return <Notice tone="info" head={`${d.case.case_id}: no gate decision yet`} lines={['The agent has proposed; no approval has reached the gate.']} />
  const failed = (g.checks ?? []).filter((c: any) => !c.pass)
  const nChecks = (g.checks ?? []).length
  if (g.decision === 'ALLOW') {
    const reopened = d.compensation?.status === 'confirmed'
    const lines = [
      `Server-timed review ${secs(d.approval?.active_dwell_ms)} · ${nChecks - failed.length} of ${nChecks} gate checks passed under policy v${g.policy_version}`,
      d.denial ? `Denial ${d.denial.status}${d.denial.readback ? `, read back from the claims system as ${d.denial.readback.status}` : ''}` : '',
      reopened ? 'The reviewer was later suspended; the denial was reopened in the claims system and read back.' : '',
    ].filter(Boolean)
    return (
      <Notice
        tone={reopened ? 'bad' : 'good'}
        head={reopened ? `${d.case.case_id} was allowed, then reopened` : `${d.case.case_id} was allowed with proof of review`}
        lines={lines}
        stamp={reopened ? { text: 'REOPENED', sub: 'AFTER SUSPENSION', ink: 'red' } : { text: 'DENIED', sub: `GATE ALLOWED · v${g.policy_version}`, ink: 'red' }}
      />
    )
  }
  return (
    <Notice
      tone="bad"
      head={`${d.case.case_id} refused: ${failed.length ? ruleName(failed[0].rule) : 'see checks'}`}
      lines={failed.length > 1 ? [`Also failed: ${failed.slice(1).map((c: any) => ruleName(c.rule)).join(' · ')}`] : ['No grant was minted; the claims system was never changed.']}
      stamp={{ text: 'REFUSED', sub: 'NO GRANT ISSUED', ink: 'red' }}
    />
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
    <>
      <Title title="Examiner" sub="Rebuild any case from the documents stored in Atlas: what the agent proposed, what the reviewer opened, what the gate checked, and what the claims system did." />
      <form
        className="lookup"
        onSubmit={(e) => {
          e.preventDefault()
          nav(`/examiner/${input.trim()}`)
        }}
      >
        <label className="field">
          Case
          <input value={input} onChange={(e) => setInput(e.target.value)} />
        </label>
        <button className="btn ink">Rebuild from Atlas</button>
        <span className="subtle" style={{ fontSize: 13.5, paddingBottom: 9 }}>Read from stored documents, not from logs or this browser.</span>
      </form>

      {!caseId && <p className="empty">Enter a case to reconstruct its full decision trail.</p>}
      {q.isLoading && <p className="empty">Reading {caseId} from Atlas…</p>}
      {q.isError && <Notice tone="bad" head={`Could not load ${caseId}`} />}
      {d && !d.case && <Notice tone="bad" head={`No case ${caseId} in this tenant`} />}
      {d?.case && <Verdict d={d} />}
      {d?.case && <AgentTrace caseId={d.case.case_id} />}
      {d?.case && (
        <ol className="entries">
          <Step n={1} title="Agent proposal" ok={!!d.proposal}>
            {d.proposal ? (
              <>
                <p>
                  <span className="mono">{d.proposal.agent_id}</span> proposed <strong>{d.proposal.recommendation?.toUpperCase()}</strong> ·
                  operator <span className="mono">{d.proposal.operator_id}</span> · status <span className="tag">{d.proposal.status}</span>
                </p>
                <p className="subtle">{d.proposal.rationale}</p>
                <p>
                  Cited:{' '}
                  {d.proposal.cited_evidence?.map((c: any) => (
                    <span key={c.evidence_id} className="tag">
                      {c.evidence_id}
                    </span>
                  ))}
                </p>
              </>
            ) : (
              <p className="subtle">No proposal.</p>
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
                        {secs(v.open_ms)} {v.idle_flag && <span className="tag red">mostly idle</span>}
                      </td>
                      <td className="mono muted">{String(v.evidence_hash ?? v.hash ?? '').slice(0, 12)}…</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="subtle">No evidence views recorded for the latest approval.</p>
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
                  <p className="subtle">
                    The browser also sent: <code>{JSON.stringify(d.approval.client_supplied_ignored).slice(0, 120)}</code> — stored and ignored.
                  </p>
                )}
                <p className="subtle">
                  Dwell recomputed from heartbeat events: <span className="mono">{secs(d.chain?.dwell_recomputed_ms)}</span>{' '}
                  {d.chain?.dwell_matches ? '✓ matches' : '✗ does not match'} · review-event hash chain{' '}
                  {d.chain?.review_events_ok ? '✓ intact' : '✗ broken'}
                </p>
              </>
            ) : (
              <p className="subtle">Not approved.</p>
            )}
          </Step>

          <Step n={4} title="Gate decisions (one Atlas transaction each)" ok={d.gate_decisions?.length ? d.gate_decisions.at(-1).decision === 'ALLOW' : null}>
            {d.gate_decisions?.length ? (
              d.gate_decisions.map((g: any) => (
                <div key={g.decision_id ?? g.ts} className="gate">
                  <p>
                    <span className={`tag ${g.decision === 'ALLOW' ? 'proof' : 'red'}`}>{g.decision}</span> policy v{g.policy_version} ·
                    transaction attempts <b className="mono">{g.txn_attempts}</b> · {when(g.ts)}
                  </p>
                  <ul className="checks">
                    {g.checks?.map((c: any) => (
                      <li key={c.rule} className={c.pass ? 'ok' : 'no'}>
                        {c.pass ? <Check aria-label="passed" /> : <X aria-label="failed" />}
                        <span>{ruleName(c.rule)}{!c.pass && c.detail && <span className="detail"> · {String(c.detail)}</span>}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))
            ) : (
              <p className="subtle">The gate has not been called for this case.</p>
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
              <p className="subtle">No denial executed.</p>
            )}
            {d.target_log?.length > 0 && (
              <ul className="log">
                {d.target_log.map((t: any, i: number) => (
                  <li key={i} className={/REFUSED/.test(t.outcome) ? 'red' : ''}>
                    {when(t.ts)} {t.op} → {t.outcome} <span className="subtle">by {t.caller}</span>
                  </li>
                ))}
              </ul>
            )}
          </Step>

          <Step n={6} title="Suspension and reopen" ok={d.suspension ? (d.compensation ? d.compensation.status === 'confirmed' : false) : d.approval ? true : null}>
            {d.suspension ? (
              <p>
                <span className="mono">{d.suspension.reviewer_id}</span> suspended by <b>{d.suspension.source}</b> · rule{' '}
                <span className="tag red">{d.suspension.rule}</span> · {when(d.suspension.ts)}
              </p>
            ) : (
              <p className="subtle">Reviewer not suspended.</p>
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
    </>
  )
}
