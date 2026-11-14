import { useEffect, useRef, useState } from 'react'
import { api } from './api'

type Beat = { active_ms: number; idle_ms: number; credited_ms: number }

// Reports what the browser can honestly see every 5 s: is the tab visible, and how long since the last input.
// The server decides how much time to credit (PRD M4); nothing here is trusted as dwell.
export function useHeartbeat(token: string | null, everyMs = 5000) {
  const lastInput = useRef(Date.now())
  const [beat, setBeat] = useState<Beat | null>(null)

  useEffect(() => {
    const mark = () => (lastInput.current = Date.now())
    const evs = ['keydown', 'pointermove', 'pointerdown', 'wheel', 'scroll'] as const
    evs.forEach((e) => window.addEventListener(e, mark, { passive: true }))
    return () => evs.forEach((e) => window.removeEventListener(e, mark))
  }, [])

  useEffect(() => {
    setBeat(null)
    if (!token) return
    let alive = true
    const id = setInterval(async () => {
      try {
        const b = await api<Beat>(`/api/views/${token}/heartbeat`, {
          visible: document.visibilityState === 'visible',
          interacted_within_ms: Date.now() - lastInput.current,
        })
        if (alive) setBeat(b)
      } catch {
        /* a missed beat simply credits nothing */
      }
    }, everyMs)
    return () => {
      alive = false
      clearInterval(id)
    }
  }, [token, everyMs])

  return beat
}
