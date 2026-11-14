import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api'

type Beat = { active_ms: number; idle_ms: number; credited_ms: number }
export type Live = {
  token: string
  serverMs: number // what the server has credited so far (the only number the gate uses)
  shownMs: number // serverMs plus the time since the last heartbeat that the server will credit if you stay active
  counting: boolean // tab visible and input in the last 15 s
  pending: boolean // a heartbeat is in flight
}

const INTERACTION_WINDOW_MS = 15000 // same rule as the server (pg/checks.py)
const MAX_GAP_MS = 7000

// Reports what the browser can honestly see: is the tab visible, and how long since the last input.
// The server decides how much time to credit (PRD M4); the live counter between beats is a preview of the same rule,
// and snaps to the server's figure on every heartbeat.
export function useHeartbeat(token: string | null, everyMs = 2000) {
  const lastInput = useRef(Date.now())
  const lastBeatAt = useRef(Date.now())
  const server = useRef<{ token: string; ms: number } | null>(null)
  const inflight = useRef<Promise<number> | null>(null)
  const [, setTick] = useState(0)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    const mark = () => (lastInput.current = Date.now())
    const evs = ['keydown', 'pointermove', 'pointerdown', 'wheel', 'scroll'] as const
    evs.forEach((e) => window.addEventListener(e, mark, { passive: true, capture: true }))
    return () => evs.forEach((e) => window.removeEventListener(e, mark, { capture: true }))
  }, [])

  const beat = useCallback(async (tok: string): Promise<number> => {
    if (inflight.current) await inflight.current.catch(() => 0) // one at a time: the server credits a gap only once
    setPending(true)
    const p = api<Beat>(`/api/views/${tok}/heartbeat`, {
      visible: document.visibilityState === 'visible',
      interacted_within_ms: Date.now() - lastInput.current,
    })
      .then((b) => {
        if (server.current?.token === tok) {
          server.current = { token: tok, ms: b.active_ms }
          lastBeatAt.current = Date.now()
        }
        return b.active_ms
      })
      .finally(() => {
        inflight.current = null
        setPending(false)
      })
    inflight.current = p
    return p
  }, [])

  useEffect(() => {
    if (!token) {
      server.current = null
      return
    }
    server.current = { token, ms: 0 }
    lastBeatAt.current = Date.now()
    let alive = true
    let timer: ReturnType<typeof setTimeout>
    const loop = async () => {
      try {
        await beat(token)
      } catch {
        /* a missed beat simply credits nothing */
      }
      if (alive) timer = setTimeout(loop, everyMs)
    }
    timer = setTimeout(loop, everyMs)
    const ui = setInterval(() => setTick((t) => t + 1), 200) // smooth display between beats
    return () => {
      alive = false
      clearTimeout(timer)
      clearInterval(ui)
    }
  }, [token, everyMs, beat])

  // Send one last heartbeat for the open document so the time since the previous beat is not lost on switch or approve.
  const flush = useCallback(async () => {
    const s = server.current
    if (!s) return null
    try {
      return await beat(s.token)
    } catch {
      return s.ms
    }
  }, [beat])

  let live: Live | null = null
  if (token && server.current?.token === token) {
    const now = Date.now()
    const counting = document.visibilityState === 'visible' && now - lastInput.current <= INTERACTION_WINDOW_MS
    const since = Math.min(now - lastBeatAt.current, MAX_GAP_MS)
    live = { token, serverMs: server.current.ms, shownMs: server.current.ms + (counting ? since : 0), counting, pending }
  }
  return { live, flush }
}
