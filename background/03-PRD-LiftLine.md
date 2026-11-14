# PRD: LiftLine

**An agent that calls a wheelchair user before they leave home when an elevator on their usual subway trip has just gone out of service, with a step-free reroute already worked out and independently checked.**

Status: **Runner-up 2** of the simulated 16-judge tournament (36 points, 3 first-place votes in the final round; avg impact 6.9, innovation 5.2, **feasibility 8.1, the highest in the field**). Two of the three MongoDB personas (Maissan, Shah T.) and Gomes ranked it first throughout.
Read `00-README-HANDOFF.md` first.

> **Go/no-go before choosing this project:** confirm on the morning whether a Toronto elevator-status source exists that you can read or archive (TTC website, open data, or a published outage list). If not, everything runs on a **labelled synthetic outage log**, which several personas said turns it into "a notification app with a synthetic log". Decide by 9:30 AM.

---

## 0. Problem statement fit (added after the official resource guide; read this first)

**Enter under Statement Two: Memory You Can Govern.** The original design has per-rider memory that changes the next call, but it **did not use Vector Search**, which Statement Two names explicitly. Without the additions below it does not qualify convincingly.

| Statement Two asks | LiftLine's answer | Status |
|---|---|---|
| Atlas **and Vector Search** to persist and retrieve memory | Rider constraints and preferences in Atlas | **Add FR-15: store each spoken rider memory ("the ramp at X is too steep", "I can manage short stairs with help") with an embedding (Voyage AI, 200M free tokens); retrieve relevant memories with `$vectorSearch` filtered by `riderId` when planning a route** |
| Memory changes what it does on the next run | A refusal excludes a station on every future outage | Designed |
| Who can read each memory | Not covered | **Add FR-16: every memory carries `riderId` (and `agencyId`); every `$vectorSearch` and find filters on it; an operator role sees aggregates only. Show a second rider's search returning none of Maria's memories** |
| How long it lives | Not covered | **Add FR-17: temporary memories ("elevator at X unreliable this week") get `expiresAt` with a **TTL index**; permanent ones do not** |
| Corrected or forgotten | Not covered | **Add FR-18: the rider can say "Union station is fine now" or "forget that"; the memory is retired (kept for audit with `retiredAt`, excluded from retrieval) and the next route changes** |
| **Prove memory changed behaviour, not just the prompt** | The route is computed by the database from stored constraints, so the change is deterministic | Show the same outage before and after the memory, with the decision log listing which memory ids excluded which station |

**Alternative:** Statement Three (Finish the Job) also partly fits (resume token = resume after a crash; call states = "took effect vs only sent"), but it requires a long multi-step task across several systems and past-experience retrieval, which LiftLine lacks. Prefer Statement Two.

**Timing and submission:** use `00-README-HANDOFF.md` §8 instead of §14 below; reduce the synthetic load to ~10,000 trips. The 1-minute video: outage triggers the call, spoken refusal stored, rider corrects the memory, same outage gives a different route, second rider cannot see Maria's memories.

---

## 1. One-paragraph summary

Maria uses a wheelchair and takes the subway at 8:40 every weekday. Last month the only elevator at her transfer station was broken and nobody told her. LiftLine keeps a persistent trip profile for each rider in Atlas (regular trips, departure windows, stations they refuse, the transfer distance they tolerate, quiet hours, a daily call cap) and updates it after every call. When an elevator goes out, a **change stream** wakes the agent; an **indexed fan-out query** finds only riders whose stored path crosses that station inside their travel window; **the database computes the step-free alternative** with `$graphLookup`; a **checker** walks the route against the elevator **event log** at the call time; and an ElevenLabs voice calls the rider. If she says "not that station, the ramp is too steep", that becomes a stored constraint that changes every future call.

## 2. The problem and why it matters

- **User:** a Toronto wheelchair user who rides the subway.
- **Costly failure:** arriving at a station to find the only elevator broken, stranded on a platform, with no warning and no step-free alternative.
- **Headline:** Use a number from a **sourced** TTC or City of Toronto elevator-outage report, or the count of outages in the replayed log. No paratransit cost figure goes on a slide unless it comes from the agency's own published reports.

### What it helps with

| For | Helps by |
|---|---|
| Wheelchair riders | A call **before leaving home** with a route that respects their own constraints |
| Transit accessibility / paratransit programme | Keeps riders on conventional accessible service rather than falling back to paratransit, because outages stop being a surprise |
| Operations | A visible record of every outage, who was affected, who was reached and who was not |

### Buyer

The transit agency's accessibility and paratransit programme. Be honest about the weakness: a **public agency with a long procurement cycle** (Kirthiraj: "an 18-month procurement cycle; who signs the cheque, and why this year?"). Possible faster wedge: disability-advocacy organisations or accessible-travel apps licensing the alerting engine.

## 3. Why it can win

| Winning pattern | How LiftLine meets it |
|---|---|
| One user, one costly failure | Maria; stranded at a dead elevator |
| Theme | Context across sessions: per-rider constraints learned from calls change the next answer. Reliable under real workloads: fan-out at 100,000 trips, restart without missing or double-calling. Guardrails: quiet hours, call caps, never proposing a route the database did not return |
| Atlas load-bearing | Filtered change stream with persisted resume token; multikey compound index for fan-out with explain plan; `$graphLookup` with `restrictSearchWithMatch`; time-series event log; unique index for idempotent calls; `2dsphere` |
| Hard check | Route checker reads the event log, not the flag the traversal used, so it **can** fail |
| Live-stage moment | A judge clicks an elevator out of service and the phone on the podium rings |
| Local user | Toronto; the judges' city |

### Nearest existing things

- **Elevate Chicago / CTA elevator status alerts** (push, text, email). **Transit app** pushes elevator outages. A Sym AI Open 2026 team's step-free routing on Transport for NSW lift status (low confidence).
- *Difference:* LiftLine **calls before departure with a checked personalised reroute**, stores spoken refusals as constraints, and is measured **against a plain push alert**.

## 4. Judge feedback this PRD answers (simulated personas)

| Judge persona | Objection or demand | Where answered |
|---|---|---|
| Gomes, Radwan, Krishnan, Shah V., Patel, Kirthiraj, Singh, Monga | **Strawman baseline:** transit apps already push elevator alerts; "no system" is not the comparison | §11 three arms: no alert, plain push alert, LiftLine |
| Krishnan, Ahmed A., Radwan | **Tautological checker:** a traversal restricted to step-free stations always passes a step-free checker | FR-9 checker reads time-series events at the call timestamp; delayed-write test |
| Shah T., Maissan | Show the **fan-out index and explain plan**; a change stream that **loses its resume token** means the phone never rings and nobody knows | FR-4, FR-2, demo kill-and-restart beat |
| Maissan (r1), Jimenez | The station graph is a few dozen nodes; `$graphLookup` does what a 20-line BFS does | Say so honestly (FR-6 note); the load-bearing part is the rider fan-out |
| Monga | **Call storm:** one outage hits thousands of riders at once | FR-11 per-rider caps, queue with rate limit, call states |
| Gomes | A missed alert must be **visible** | FR-10 call states with retry and `unreached` |
| Shah V., Patel | The phone call is the most likely thing to die on venue Wi-Fi | FR-12 browser voice built first |
| Patel, Singh, Jimenez | **The agent decides little**: it phrases a graph result and stores a blocklist | FR-7 constraint learning, FR-11 call decisions; Monga's defence: "a per-user constraint that deterministically changes the next session is what production agent memory looks like" |
| Kirthiraj | Who pays? | §2 Buyer |
| Unresolved after r3 | Graph traversal not load-bearing; fan-out load is synthetic; memory is mostly an exclusion list; no real rider; no confirmed live feed | §15 disclose |

## 5. Scope

### Goals
1. Persistent rider profiles and trips, updated after every call.
2. Change-stream-driven, idempotent, restart-safe outage processing.
3. Indexed fan-out over a large synthetic rider set with an explain plan.
4. Step-free reroute computed in the database, checked against the event log.
5. Voice call (browser first, phone as upgrade) that captures refusals as constraints.
6. Replay evaluation against a push-alert baseline.

### Non-goals
- Real riders or real phone numbers of the public. Real-time control of transit systems.
- Surface-route (bus) alternatives. Per-elevator reliability ranking (stretch).
- Claims about paratransit savings without a published source.

## 6. Users

| User | Notes |
|---|---|
| Rider (synthetic, plus one team member playing Maria) | Profile, trips, constraints, quiet hours, call cap |
| Operator dashboard user | Sees outages, affected riders, call states, unreached riders |
| Agent service identity | Reads profiles, writes calls and constraints; cannot alter elevator status |

## 7. Functional requirements

### Data and events
- **FR-1 MUST** Station graph loaded from the public system map: stations, edges (line segments and transfers with distances), elevators per station, `stepFree` flags. Done by hand in hour 1 (~75 stations).
- **FR-2 MUST Change stream** on elevator status with a server-side `$match` (status changes to `out_of_service` or back). **Persist the resume token after each processed event**; on restart, resume from it. [Maissan, Shah T.]
- **FR-3 MUST** Every elevator status change is also written to a **time-series** collection `elevator_events`.
- **FR-4 MUST Fan-out.** Rider trips carry `pathStationIds` (array) and `windowStart`; a **multikey compound index `{pathStationIds: 1, windowStart: 1}`** serves "who is affected". Load a **synthetic rider set targeting 100,000 trips** so the index does real work; show the explain plan (index scan, documents examined vs. returned). [Shah T., Ahmed A.]
- **FR-5 MUST Idempotent calls.** `calls` has a **unique index on `{outageEventId, riderId, tripId}`**, so a restarted service replays missed outages without double-calling.

### Routing and checking
- **FR-6 MUST** `$graphLookup` over stations/edges with `restrictSearchWithMatch: {stepFree: true}` and the rider's excluded stations, returning the reachable step-free set with depth; the service reconstructs the shortest path and respects the rider's max transfer distance. *Say plainly that at this graph size an in-memory search would also work; the reason to keep it in the database is that the route, the status and the profile are read from the same store.* [Jimenez]
- **FR-7 MUST Constraint learning.** The rider's spoken refusal ("not that station, the ramp is too steep") is stored as an exclusion on the profile (the reason is stored but only the exclusion is acted on); the route is recomputed and offered again. The next outage uses the updated profile.
- **FR-8 MUST** The language model only **phrases** the route returned by the database. It never proposes a station or route itself.
- **FR-9 MUST Independent checker.** Before any call, walk the proposed path and assert that each elevator on it had, as its **last event in `elevator_events` before the call timestamp**, status `in_service`. It must not read the `stepFree` flag the traversal used. Test with **deliberately delayed status writes** so the checker can and does reject routes. [Krishnan, Ahmed A.]

### Calls
- **FR-10 MUST Call states:** `queued → ringing → answered | declined | unreached`. An unanswered call is retried once, then shown as `unreached` on the dashboard, so a miss is visible. [Gomes]
- **FR-11 MUST Agent guardrails per rider:** quiet hours, max calls per day, call only if departure is within the next N minutes; a global rate-limited queue so one outage affecting thousands of riders does not create a call storm; riders past their cap get a text-only fallback (logged). [Monga]
- **FR-12 MUST Browser voice first** (ElevenLabs conversational voice in a browser tab on a phone on speaker), with two tools: `get_reroute`, `save_constraint`. **Real telephony is an upgrade**, not a dependency. [Shah V., Patel]
- **FR-13 SHOULD** LangSmith traces for each call and tool call.
- **FR-14 COULD** `2dsphere` `$geoNear` for the nearest step-free station to home. **COULD** per-elevator reliability ranking from the time-series log. **COULD** real telephony.

## 8. Data model

```
stations         { _id, name, line(s), location: GeoJSON Point, stepFree: bool, elevatorIds: [..] }
edges            { _id, from, to, kind: "segment"|"transfer", distanceM, minutes }
elevators        { _id, stationId, status: "in_service"|"out_of_service", updatedAt }
elevator_events  time-series { ts, meta: { elevatorId, stationId }, status }
riders           { _id, name, phone, home: GeoJSON, maxTransferM, quietHours, maxCallsPerDay,
                   excludedStations: [ {stationId, reason, addedAt, sourceCallId} ] }
trips            { _id, riderId, label, pathStationIds: [..], windowStart: "08:40", days: [..] }
outage_events    { _id, elevatorId, stationId, at, resumeTokenAtProcess }
calls            { _id, outageEventId, riderId, tripId, state, attempts, route: [..],
                   checker: { passed, checkedAt, failures: [..] }, transcript, at }
stream_state     { _id: "elevator-listener", resumeToken, updatedAt }
eval_runs        { _id, arm: "none"|"push"|"liftline", log: "real"|"synthetic", results }
```

### Indexes
- `trips { pathStationIds: 1, windowStart: 1 }` (multikey compound; fan-out)
- `calls { outageEventId: 1, riderId: 1, tripId: 1 }` **unique**
- `stations { location: "2dsphere" }` (if FR-14 built)
- time-series on `elevator_events` with `meta.elevatorId`

## 9. Architecture

```
Browser (Angular)                Spring Boot                               Python
- map dashboard, click-to-break  - change-stream listener + resume token   - ElevenLabs voice agent (browser)
- rider profile + constraints    - fan-out query, calls queue, rate limit   - tools: get_reroute, save_constraint
- call states, unreached list    - $graphLookup route + path reconstruction - synthetic rider loader (100k trips)
- explain plan, replay table     - checker over elevator_events             - replay harness, push-alert baseline
                  \__________________ MongoDB Atlas (event sandbox) ___________________/
```

API contract: `POST /elevators/{id}/status`, `GET /outages/{id}/affected`, `GET /reroute?riderId&tripId`, `POST /riders/{id}/constraints`, `GET /calls?state=`, `GET /explain/fanout?stationId`.

## 10. Key flows

1. Judge clicks an elevator out of service → status write → event to time-series → change stream → fan-out → for each affected rider within window and caps: route → checker → call queued.
2. Call: voice names the elevator and the alternative with extra minutes → rider refuses a station → constraint saved → new route → accepted.
3. Restart: kill listener → flip another elevator → restart → resume from stored token → exactly one call for the missed outage.
4. Repeat first outage → agent goes straight to the second route because of the stored constraint.

## 11. Evaluation plan (pre-register before the first run)

Replay an outage log (**real if obtainable, otherwise labelled synthetic**) against about **200 scripted trips**, three arms on the **same log**:

| Arm | Description |
|---|---|
| No alert | Rider learns at the station |
| **Plain push alert** | "Elevator out at X", no route, no profile (the real baseline) |
| LiftLine | Call with checked, personalised route |

**Measured:**
1. Trips where the rider had a **usable step-free route that respects their own constraints before leaving home**, per arm.
2. Median seconds from status change to call start.
3. Events recovered after a forced restart vs. events sent; duplicate calls (should be 0).
4. Fan-out query time and documents examined at the loaded rider count.
5. Routes **rejected by the checker** when status writes are deliberately delayed.

**Reporting rules:** state the assumption that a push-alert rider cannot work out a reroute alone (stated, not proven); expect the gap over push alerts to come mainly from stored-constraint cases (Krishnan's prediction) and show it either way; synthetic riders labelled; real feed latency is outside our control.

## 12. Demo script (3:00) with fallbacks

| Time | Beat | Fallback |
|---|---|---|
| 0:00 | "Maria uses a wheelchair. Last month the only elevator at her station was broken and nobody told her." | — |
| 0:20 | Dashboard: her 8:40 commute; profile from earlier sessions (avoids one station, max 200 m transfer) | — |
| 0:35 | A judge clicks an elevator out of service. The phone on the podium rings; the voice names the elevator and the alternative with extra minutes | Browser voice on laptop speaker |
| 1:10 | Maria: "Not that station, the ramp is too steep." Second route offered and accepted; the constraint appears in her profile | Typed reply |
| 1:40 | Kill the listener. Flip another elevator while it is down. Restart: it resumes from the stored token and the phone rings once for the missed outage | Recorded run |
| 2:10 | Trigger the first outage again: the agent goes straight to the second route | — |
| 2:25 | One screen: fan-out explain plan at 100,000 trips; replay table vs. push alert, including checker rejections | Screenshot |
| 2:50 | Buyer: the transit agency's accessibility/paratransit programme | — |

## 13. Questions judges will ask, and the answers

| Question | Answer |
|---|---|
| "Transit apps already push elevator alerts." | Yes; that is our baseline arm. We count riders with a usable, personal route before leaving home. |
| "Your checker can't fail." | It reads the event log at the call time, not the traversal's flag; with delayed writes it rejected N routes. |
| "Isn't `$graphLookup` overkill for 75 stations?" | Yes, performance-wise; we keep it because route, status and profile live in one store. The load-bearing query is the fan-out. |
| "What if the service restarts?" | Resume token persisted after each event; unique call index prevents double calls. We just showed it. |
| "What does the agent actually decide?" | Whether and when to call within the rider's caps and quiet hours, and how her spoken constraints change every future route. |
| "Who pays?" | The agency's accessibility programme; we know procurement is slow. |

## 14. Build schedule (EST)

| Time | Engineer 1 (Java/Spring) | Engineer 2 (Angular) | Engineer 3 (Python) |
|---|---|---|---|
| 9:00–9:30 | All: rules, **elevator data go/no-go**, Atlas sandbox, schema, API contract | | |
| 9:30–11:00 | Load stations/edges by hand; elevators; indexes | Map dashboard, click-to-break | Synthetic rider/trip loader (100k) |
| 11:00–13:00 | Change stream + resume token; fan-out; unique call index | Rider profile, constraints panel | ElevenLabs browser voice agent with two tools |
| 13:00–14:30 | `$graphLookup` route + reconstruction; checker on time-series | Call states, unreached list | Constraint capture; wire calls end to end |
| 14:30 | **Commit PREREGISTRATION.md** | | |
| 14:30–16:30 | Rate limits, caps, explain endpoint | Explain + replay table | Replay harness, push-alert arm, delayed-write test |
| 16:30–17:30 | All: rehearse ×3 incl. kill-and-restart; record backup video | | |
| 17:30–18:30 | All: submit, README | | |

**Cut order:** real telephony (browser voice stays) → `$geoNear` → reliability ranking → free-text refusal reasons. **Never cut:** resume token + unique index, push-alert baseline, checker on the event log, explain plan, stored constraint changing the next call.

## 15. Risks and what to disclose

| Risk | Mitigation |
|---|---|
| No real elevator feed | Labelled synthetic log; say so |
| Phone call fails on venue network | Browser voice built first |
| Judges see a notification app | Lead with constraint learning, restart recovery and the push-alert comparison |
| Low innovation score (5.2) | Accept; this project wins on reliability and execution, not novelty |

**Disclose:** the subway graph is small, so the traversal is not load-bearing; the fan-out load is synthetic; the memory is mostly a per-rider exclusion list plus preferences; no real rider; no confirmed live feed.

## 16. Acceptance checklist

- [ ] Clicking an elevator out of service triggers a call within seconds.
- [ ] Spoken refusal stored as a constraint and used on the next outage.
- [ ] Kill-and-restart replays a missed outage exactly once.
- [ ] Explain plan shows the multikey compound index at ~100,000 trips.
- [ ] Checker rejects routes under delayed status writes, and the count is shown.
- [ ] Unreached calls are visible; caps and quiet hours enforced.
- [ ] Replay table with three arms on the same log; synthetic data labelled.
- [ ] PREREGISTRATION.md committed first; backup video; everything in the event Atlas sandbox.
