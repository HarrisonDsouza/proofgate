import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

type Info = { enabled: boolean; project: string; project_url: string | null }

/* A pointer to the agent's LangSmith trace for this case. LangSmith is the debugging view; the examiner
   record above is read from Atlas and is the authority. The browser never sees a LangSmith key. */
export function AgentTrace({ caseId }: { caseId: string }) {
  const q = useQuery({ queryKey: ['langsmith'], queryFn: () => fetch('/api/observability/langsmith').then((r) => r.json() as Promise<Info>), retry: false })
  const [copied, setCopied] = useState(false)
  if (!q.data) return null
  const { enabled, project, project_url } = q.data
  const copy = () => {
    navigator.clipboard?.writeText(caseId).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    }, () => {})
  }
  return (
    <p className="subtle" style={{ margin: '10px 0 0', fontSize: 14 }}>
      <strong>Agent trace (LangSmith, project {project}):</strong>{' '}
      {enabled ? 'recording' : 'tracing is off, so no new runs are recorded'}. Debugging view only; the record above comes from Atlas.{' '}
      <button type="button" className="btn" onClick={copy}>{copied ? 'Copied' : `Copy ${caseId}`}</button>{' '}
      {project_url && (
        <a className="btn" href={project_url} target="_blank" rel="noreferrer noopener">Open traces in LangSmith</a>
      )}
    </p>
  )
}
