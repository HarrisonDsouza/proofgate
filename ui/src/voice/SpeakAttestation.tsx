import { Mic, Square } from 'lucide-react'
import { useRef, useState } from 'react'
import { store, TENANT } from '../api'
import './speak.css'

// Spoken attestation (ElevenLabs Scribe, server side). Voice is EVIDENCE only: the gate never reads it, a failure
// falls back to the typed text, and the ElevenLabs key never reaches the browser (see docs/VOICE.md).
export type Attestation = {
  attestation_id: string
  transcript: string
  source: 'elevenlabs_stt' | 'typed_fallback'
  score: { specificity: number; boilerplate: number; attestation_score: number; unviewed_hits: string[] }
}

async function send(audio: Blob | null, caseId: string, fallbackText: string): Promise<Attestation> {
  const s = store.session()
  if (!s) throw new Error('Start a session first.')
  const r = await fetch('/api/voice/attest', {
    method: 'POST',
    headers: {
      'content-type': 'audio/webm',
      'X-Tenant-Id': TENANT,
      'X-Console-Key': store.key(),
      'X-Session-Id': s.session_id,
      'X-Case-Id': caseId,
      // HTTP headers carry ASCII only; the server stores this only if speech-to-text is unavailable.
      'X-Fallback-Text': fallbackText.replace(/[^\x20-\x7e]/g, ' ').slice(0, 1000),
    },
    body: audio ?? new Blob([]),
  })
  const body = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(body.error ?? body.detail ?? `HTTP ${r.status}`)
  return body as Attestation
}

export function SpeakAttestation({ caseId, typedText, onAttested }: {
  caseId: string
  typedText: string
  onAttested: (a: Attestation) => void
}) {
  const rec = useRef<MediaRecorder | null>(null)
  const [state, setState] = useState<'idle' | 'recording' | 'saving'>('idle')
  const [note, setNote] = useState('Optional: say what you checked. Typed text is used if voice is unavailable.')

  async function finish(blob: Blob | null) {
    setState('saving')
    try {
      const a = await send(blob, caseId, typedText)
      onAttested(a)
      const sc = a.score
      setNote(
        `${a.source === 'elevenlabs_stt' ? 'Spoken' : 'Typed (voice unavailable)'} · specificity ${sc.specificity} · repeats earlier ${sc.boilerplate}` +
          (sc.unviewed_hits.length ? ` · names unopened evidence: ${sc.unviewed_hits.join(', ')}` : ''),
      )
    } catch (e) {
      setNote(`Attestation not saved: ${e instanceof Error ? e.message : 'error'}. The typed text will be used.`)
    } finally {
      setState('idle')
    }
  }

  async function toggle() {
    if (state === 'recording') {
      rec.current?.stop()
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const chunks: Blob[] = []
      const r = new MediaRecorder(stream)
      rec.current = r
      r.ondataavailable = (e) => chunks.push(e.data)
      r.onstop = () => {
        stream.getTracks().forEach((t) => t.stop())
        rec.current = null
        void finish(new Blob(chunks, { type: 'audio/webm' }))
      }
      r.start()
      setState('recording')
      setNote('Recording… say what you checked, then stop.')
    } catch {
      setNote('No microphone: using the typed text.')
      void finish(null)
    }
  }

  return (
    <div className="speak">
      <button type="button" className="btn" onClick={toggle} disabled={state === 'saving' || !caseId}>
        {state === 'recording' ? <><Square aria-hidden /> Stop and save</> : <><Mic aria-hidden /> Speak attestation</>}
      </button>
      <small role="status" aria-live="polite">{note}</small>
    </div>
  )
}
