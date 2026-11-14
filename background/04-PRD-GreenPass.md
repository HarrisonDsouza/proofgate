# PRD: Green Pass

**A kitchen agent for the owner of an independent Toronto restaurant: it knows that restaurant's own DineSafe inspection history, runs a spoken closing check with hands busy in the cook's language, and keeps every breach open from shift to shift until a passing reading closes it.**

Status: **Runner-up 3** of the simulated 16-judge tournament (20 points, 1 first-place vote in the final round; avg impact 5.2, innovation 4.8, feasibility 7.1). It rose every round (7 → 10 → 20) because it is the **only project tested against real outcomes the team did not write**. Ahmed Radwan persona ranked it first; Amrit Krishnan moved it up for the same reason.
Read `00-README-HANDOFF.md` first.

> **Honest positioning:** this is the weakest of the four on impact and innovation. Choose it only if the team values real public data and a falsifiable result above a novel mechanism.

---

## 0. Problem statement fit (added after the official resource guide; read this first)

**Enter under Statement Two: Memory You Can Govern.** Fit is weak-moderate; the additions below are required to qualify.

| Statement Two asks | Green Pass's answer | Status |
|---|---|---|
| Atlas **and Vector Search** to persist and retrieve memory | Vector Search was only used to map infraction categories | **Add FR-14: store each corrective action and its outcome as a memory with an embedding; when a new breach opens, retrieve this location's past corrective actions for similar breaches (`$vectorSearch` filtered by `establishmentId`) and suggest the one that worked** |
| Memory changes the next run | Open cases lead the next shift; repeat breaches escalate | Designed |
| Who can read each memory | Not covered | **Add FR-15: multi-location operator with two locations; each location's staff see only their own cases and memories (filter by `establishmentId` in every query and vector search); the owner sees both. Demo: location B's cook cannot retrieve location A's cases** |
| How long it lives | Not covered | **Add FR-16: closed cases stop driving escalation after the window (e.g. 90 days), via an `expiresAt` field or TTL on a derived "active memory" collection; the audit record is kept** |
| Corrected or forgotten | Not covered | **Add FR-17: a misheard reading can be corrected by the owner; the old value is kept with `correctedBy`, and any case it opened is re-evaluated** |
| Prove memory changed behaviour | Scenario test vs. a stateless checklist (§11 measurement 2) | Designed |

**Timing and submission:** use `00-README-HANDOFF.md` §8 instead of §14 below. The 1-minute video: breach opens a case, next shift starts with it, "it's fixed" refused without a reading, location B isolated from A, misheard reading corrected.

---

## 1. One-paragraph summary

Toronto publishes every DineSafe restaurant inspection: establishment, date, infraction text, severity and outcome. Green Pass loads one restaurant's history, builds a short closing checklist weighted toward the categories **that location** has been cited for, and runs it by voice at closing (ElevenLabs speech in and out, English plus one other language a teammate speaks). Readings like "walk-in is at six degrees" are read back, stored, and tested against **fixed thresholds from Ontario's Food Premises Regulation**, not a model's opinion. A breach opens a **corrective-action case** the owner approves on their phone; the next shift's check **starts with every open case**; a case closes **only on a passing reading for the same unit**, never because someone says it is fixed; a second breach in the same category within the window makes that item mandatory every shift.

## 2. The problem and why it matters

- **User:** the owner of an independent Toronto restaurant, and the cooks who close.
- **Costly failure:** repeating the same infraction the inspector already cited, leading to a conditional pass or closure; breaches "fixed" by assertion.
- **Headline (compute on the morning from the open data):** number of establishments with a conditional pass or closure in the available data, and the share whose infraction repeated a category from an earlier inspection.

### What it helps with

| For | Helps by |
|---|---|
| Owner | Knows the kitchen is checking the things *this* restaurant gets cited for; approves fixes from a phone; has a dated record to show the inspector |
| Cooks | A hands-free check in their own language at closing |
| Multi-location operators | The same per-location targeting and case discipline across sites |

### Buyer
Multi-location operators and franchise groups (single independents rarely pay for software).

## 3. Why it can win (and why it may not)

| Winning pattern | How Green Pass meets it |
|---|---|
| Hard check | Fixed regulatory thresholds; cases close only on a passing reading, enforced by rule over stored state |
| Evidence the team did not author | Temporal split of real DineSafe histories against what inspectors actually cited next |
| Context across sessions | Open cases lead the next shift; repeat breaches escalate |
| Local, public data | Toronto Open Data |
| Voice intrinsic | Hands busy at closing; cook's language |

**Weaknesses the panel scored down:** a per-establishment frequency count achieves the targeting with no agent or voice (Singh); nothing built in a day shows fewer infractions (Strelnikov); readings are self-reported and can be falsified; the mechanism (voice HACCP logging) exists commercially.

### Nearest existing things
- iFactory voice HACCP agent (spoken readings checked against critical limits); Xenia and other restaurant line-check software; FoodDocs, Jolt (digital food-safety logs). DrivenData/Yelp "Keeping It Fresh" (inspection-outcome prediction from open data).
- *Difference:* the checklist comes from that kitchen's own public enforcement record, and cases close only on a measured pass.

## 4. Judge feedback this PRD answers (simulated personas)

| Judge persona | Objection or demand | Where answered |
|---|---|---|
| Radwan, Krishnan | Keep the held-out test on real data; report a null if it happens | §11 measurement 1 |
| Strelnikov | Add the **trivial baseline** (the restaurant's own most recent categories); a restaurant's own past category will beat city-wide top three trivially | §11 measurement 1, two baselines |
| Strelnikov, Singh | The DineSafe number **tests a predictor, not the agent** | §11 measurement 2: multi-shift scenarios vs. a stateless checklist |
| Strelnikov | Cross-session behaviour must be concrete | FR-7 to FR-10 case state machine |
| Original risk | Misheard numbers in a noisy hall | FR-5 read-back, clip-on mic, recorded fallback |
| Unresolved after r3 | Cannot show changed inspection outcomes in a day; scenarios are team-written; checklist may not beat the trivial baseline; self-reported readings | §15 disclose |

## 5. Scope

### Goals
1. Load DineSafe into Atlas; map infraction text to a hand-written category list.
2. Per-location checklist from that location's history.
3. Voice closing check with read-back, regulation thresholds and structured readings.
4. Corrective-action case file across shifts with owner approval by phone.
5. Three labelled measurements (§11).

### Non-goals
- Claims of reduced infractions. Sensor integration. More than two languages. "Restaurants like mine" neighbour search (unless measurement shows it adds something). Naming real establishments negatively on stage (anonymise).

## 6. Users

| User | Can |
|---|---|
| Cook (logged in on the kitchen tablet) | Run the closing check, give readings |
| Owner (phone) | Approve corrective actions, see cases and escalations |
| Inspector view (read-only) | Dated readings, breaches, closures |
| Agent service identity | Open cases, record readings; cannot close a case without a passing reading |

## 7. Functional requirements

- **FR-1 MUST** Load the DineSafe dataset from Toronto Open Data into Atlas as nested documents (establishment → inspections → infractions). **Confirm field names from the downloaded file on the morning.**
- **FR-2 MUST** Map infraction free text to ~10–15 hand-written categories (e.g. cold holding, hot holding, pest control, handwashing). Use **Atlas Vector Search only for this mapping**; report the mapping is hand-defined.
- **FR-3 MUST** Per-location top-three checklist from that establishment's earlier inspections, plus fixed daily items (cold holding, hot holding).
- **FR-4 MUST** Voice closing check: ElevenLabs speech in and out in English and **one** other language a teammate speaks and can verify; typed fallback.
- **FR-5 MUST** Parse each reading into `{unit, value, measure}` and **read it back for confirmation** before storing ("Walk-in, six degrees, correct?").
- **FR-6 MUST** Test readings against fixed thresholds: cold holding ≤ 4 °C, hot holding ≥ 60 °C (**verify against O. Reg. 493/17 text on the day**). The model never decides pass/fail.
- **FR-7 MUST** A breach opens a **corrective-action case**; a **change stream** pushes it to the owner's phone for approval.
- **FR-8 MUST** The next shift's check **starts with every open case** before the normal checklist.
- **FR-9 MUST** A case closes **only on a passing reading for the same unit**. "It's fixed" without a reading → the agent asks for the reading; no reading → case stays open.
- **FR-10 MUST** A second breach in the same category within the escalation window (e.g. 14 days) makes that item **mandatory every shift** and notifies the owner. Rules are fixed and written by the team, not learned.
- **FR-11 MUST** Inspector view: dated readings, breaches and closures (fallback: a plain dated list).
- **FR-12 SHOULD** LangSmith traces for parsing and each agent turn.
- **FR-13 COULD** Temperature trend chart from the time-series collection. **COULD** neighbour search.

## 8. Data model

```
establishments   { _id, name (anonymised for demo), address, type,
                   inspections: [ { date, outcome, infractions: [ { text, severity, category, categoryScore } ] } ] }
categories       { _id, name, description, embedding }
checklists       { _id, establishmentId, items: [ { category, unit, source: "history"|"fixed", mandatory } ],
                   builtFromInspectionsBefore }
readings         time-series { ts, meta: { establishmentId, unit, category }, value, measure,
                   passed, confirmedBy, shiftId, language, rawTranscript }
cases            { _id, establishmentId, unit, category, state: "open"|"approved"|"closed",
                   openedByReadingId, approvals: [ {userId, at} ], closingReadingId, escalated: bool, history: [..] }
shifts           { _id, establishmentId, cookId, startedAt, endedAt, openCasesAtStart: [..] }
eval_runs        { _id, measurement: 1|2|3, results }
```

Indexes: `cases { establishmentId: 1, state: 1 }`; vector index on `categories.embedding`; time-series on `readings`.

## 9. Architecture

```
Angular: owner phone page, cook tablet UI, dashboard, inspector view
Spring Boot: DineSafe loader, category mapping, case state machine, thresholds, change stream to owner
Python: ElevenLabs voice loop, reading parser, the three evaluation scripts
All on MongoDB Atlas (event sandbox)
```

## 10. Key flows

1. Morning: load DineSafe, compute headline numbers, build checklists.
2. Closing: cook speaks readings → read-back → stored → threshold check → breach opens a case → owner's phone.
3. Next shift: agent opens with the open case → "it's fixed" → "what's the reading?" → "three degrees" → case closes.
4. A second breach a week later → item mandatory every shift → owner notified.

## 11. Evaluation plan (pre-register before the first run)

Each measurement is labelled with what it does **and does not** show.

1. **Checklist targeting on real data.** Split each establishment's history in time; does the top-three checklist built from earlier inspections contain the category cited at the next inspection? Compare against **two baselines**: city-wide top three, and the **trivial baseline** (that establishment's own most recent categories). If it does not beat the trivial baseline, say so. *This justifies personalising the checklist and nothing more.*
2. **The agent itself.** About 15 scripted two-week kitchen scenarios with seeded breaches, false "fixed" claims and recurrences, run against Green Pass and against a **stateless voice checklist with no case memory**. Counted: open breaches raised again next shift, cases wrongly closed without a passing reading, recurrences escalated. Checked by rule over stored cases.
3. **Parsing.** About 40 scripted voice readings across the two languages, scored for value, unit and pass/fail.

**Limits to state:** nothing shows fewer infractions in a real kitchen; DineSafe exposes only a few recent years; the category mapping is hand-written; scenarios are team-written.

## 12. Demo script (3:00)

| Time | Beat | Fallback |
|---|---|---|
| 0:00 | Headline numbers computed that morning from DineSafe | Static slide |
| 0:25 | An anonymised real establishment: its history and the three-item checklist derived from it | — |
| 0:45 | Teammate speaks the closing check in the second language: walk-in reads six degrees. Read-back, logged 6 °C, flagged against 4 °C, and "this is the category you were cited for on" the real past date | Recorded clip |
| 1:20 | Owner's phone gets the corrective action; taps approve | — |
| 1:35 | New session, next shift: agent opens with the unresolved case. "It's fixed." "What's the reading?" "Three degrees." Case closes | Typed |
| 2:05 | Seeded second breach a week later: item becomes mandatory every shift | — |
| 2:20 | Inspector view: dated readings, breaches, closures | Dated list |
| 2:35 | Evidence slide, all three measurements with baselines; buyer: multi-location operators | — |

## 13. Questions judges will ask, and the answers

| Question | Answer |
|---|---|
| "A frequency count does your targeting." | Correct, and it is our trivial baseline; we show whether we beat it. The product is the case discipline, tested in measurement 2. |
| "Does this reduce infractions?" | We cannot show that in a day; it needs months in real kitchens. |
| "Can't a cook lie about the reading?" | Yes, without a sensor. Disclosed. |
| "Why MongoDB?" | Nested irregular inspection documents, vector mapping of infraction text, time-series readings, change stream to the owner's phone, case history as cross-session state. |

## 14. Build schedule (EST)

| Time | Engineer 1 (Java/Spring) | Engineer 2 (Angular) | Engineer 3 (Python) |
|---|---|---|---|
| 9:00–9:30 | All: rules, download DineSafe, confirm fields, schema, category list | | |
| 9:30–12:00 | Loader, category mapping, checklist builder | Cook tablet UI, history view | Voice loop, reading parser, read-back |
| 12:00–14:30 | Thresholds, case state machine, change stream | Owner phone approval page | Measurement 1 (temporal split, two baselines) |
| 14:30 | **Commit PREREGISTRATION.md** | | |
| 14:30–16:30 | Escalation rule, inspector data | Dashboard, inspector view | Measurements 2 and 3 |
| 16:30–17:30 | All: rehearse ×3; record backup video | | |
| 17:30–18:30 | All: submit, README | | |

**Cut order:** neighbour search → second language (keep English) → trend charts → inspector view (plain dated list). **Never cut:** trivial baseline, case closes only on a passing reading, measurement 2.

## 15. Risks and what to disclose

Misheard numbers (clip-on mic, read-back, recorded clip); the targeting may not beat the trivial baseline (then the case file is the product); low judge scores for impact and innovation.

**Disclose:** no outcome change shown; team-written scenarios; hand-written category mapping; self-reported readings.

## 16. Acceptance checklist

- [ ] DineSafe loaded; checklist built from a real (anonymised) establishment's history.
- [ ] Spoken reading read back, stored, failed against the regulation threshold.
- [ ] Owner approves the case on a phone via change stream.
- [ ] Next shift opens with the case; "it's fixed" alone does not close it.
- [ ] Repeat breach makes the item mandatory.
- [ ] Three measurements with baselines, including the trivial one, results shown as-is.
- [ ] PREREGISTRATION.md first; backup video; everything in the event Atlas sandbox.
