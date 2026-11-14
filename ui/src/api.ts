// Thin client for the ProofGate API (PRD §8). The server decides everything; the browser only reports what it can see.

const KEY = 'pg.consoleKey'
const SESSION = 'pg.session'

export const TENANT = 'payer-acme'

export type Session = { session_id: string; reviewer_id: string; specialty?: string }

export const store = {
  key: () => sessionStorage.getItem(KEY) ?? '',
  setKey: (k: string) => sessionStorage.setItem(KEY, k),
  session: (): Session | null => JSON.parse(sessionStorage.getItem(SESSION) ?? 'null'),
  setSession: (s: Session | null) =>
    s ? sessionStorage.setItem(SESSION, JSON.stringify(s)) : sessionStorage.removeItem(SESSION),
}

export class ApiError extends Error {
  status: number
  body: unknown
  constructor(status: number, body: unknown) {
    super(`HTTP ${status}`)
    this.status = status
    this.body = body
  }
}

export async function api<T = unknown>(path: string, body?: unknown, method?: string): Promise<T> {
  const s = store.session()
  const headers: Record<string, string> = {
    'content-type': 'application/json',
    'X-Tenant-Id': TENANT,
    'X-Console-Key': store.key(),
  }
  if (s) headers['X-Session-Id'] = s.session_id
  const r = await fetch(path, {
    method: method ?? (body === undefined ? 'GET' : 'POST'),
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const text = await r.text()
  const data = text ? JSON.parse(text) : null
  if (!r.ok) throw new ApiError(r.status, data)
  return data as T
}

export type Evidence = { evidence_id: string; label: string }
export type QueueItem = {
  proposal_id: string
  case_id: string
  summary: string
  rationale: string
  codes: string[] | Record<string, unknown>
  billed_amount: number
  cited_evidence: Evidence[]
  all_evidence: Evidence[]
}
export type Policy = { version: number; status: string; rules: Record<string, number | boolean> }
export type Dashboard = {
  executed: number
  reversed: number
  refused: number
  pending: number
  suspended_reviewers: string[]
  suspensions: Suspension[]
  last_burst: { submitted: number; executed: number; top_reasons: Record<string, number> } | null
}
export type Suspension = { suspension_id: string; reviewer_id: string; active: boolean; source: string; rule: string; ts: string }
export type RunOnce = { submitted: number; executed: number; refused: number; top_reasons: Record<string, number> }

export const RULE_NAMES: Record<string, string> = {
  G1: 'Approval matches proposal',
  G2: 'Reviewer not suspended',
  G3: 'Credential and specialty',
  G4: 'Every cited item opened',
  G5: 'Server-timed dwell at the floor',
  G6: 'Not approving in bulk',
  G7: 'Evidence unchanged since viewed',
  G8: 'Separation of duties',
}

export const ruleName = (code: string) => {
  const g = code.split('_')[0]
  return `${g} ${RULE_NAMES[g] ?? code}`
}

export const secs = (ms: number | undefined | null) => `${((ms ?? 0) / 1000).toFixed(1)} s`
