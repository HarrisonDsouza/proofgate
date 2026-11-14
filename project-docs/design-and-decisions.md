# Design and key decisions

Full spec: `docs/PRD.md` §7 (data) and §8 (architecture). How the idea was chosen: `docs/DECISION-RECORD.md`.

## The parts

```
 Browser (Angular :4200)
   review page · examiner page
        │  /api                          /py
        ▼                                 ▼
 Gate service (Spring Boot :8080)    Python service (FastAPI :8000)
   sessions, evidence views,           mock claims system (needs a grant)
   heartbeats, approvals,              rules R1-R8, agent control
   THE GATE TRANSACTION,               [voice/attest - ElevenLabs, Neil]
   policies, suspensions, confirm
        │                                 │
 Detector (same Spring jar,         Python agent
   "detector" profile):               triage: proposes denials
   change stream → suspensions,       executor: gate → claims system → confirm
   compensation worker                [@traceable → LangSmith, Neil]
        │                                 │
        └──────────► MongoDB Atlas ◄──────┘   (the only place state lives)
```

## The flow of one denial

1. The **agent** reads a pending claim and writes a *proposal*: "deny, because of evidence E1 and E3, under policy clause MP-012".
2. A **reviewer** opens each cited item. The server creates a *view token* and credits active time from heartbeats. Only one item can be open at a time.
3. The reviewer clicks **Approve**. The server computes what was viewed and for how long from its own records. Anything the browser claims is ignored and logged.
4. The **executor** asks the **gate**. One Atlas transaction:
   - reads the approval, proposal, case, policy, reviewer and reviewer state
   - checks G1-G8
   - writes the decision
   - on ALLOW, mints a **single-use grant** that expires in 60 seconds
5. The executor calls the **claims system** with the grant. It consumes the grant atomically and changes the claim to DENIED.
6. The gate **reads the claim back** and marks the denial CONFIRMED only if it really changed.
7. If the reviewer is later suspended, a **compensation** reopens the claim and is verified by read-back.

## Key decisions and why

| Decision | Why | Alternative rejected |
|---|---|---|
| **Dwell time is measured by the server**, from view tokens and heartbeats | A browser can send any number it likes; judges will curl a fake `dwell_ms`. | Trusting a client timer |
| **Exclusive focus**: one open evidence item per session | Credited time across cases cannot exceed real time, so 50 approvals × 30 s needs 25 minutes. A burst can't pass whatever the rate. | Counting time per tab |
| **The gate is one transaction** (snapshot read, majority write) | Every check and write commits together or not at all. A crash mid-way leaves nothing half-done. | Checks in code, then separate writes |
| **Every gate call writes the reviewer's `reviewer_state` doc** (version guard) | Two approvals, or an approval and a suspension, for the same reviewer then *conflict*. MongoDB forces one to retry, and the retry sees the new state. This closes the race window. | Relying on the change-stream detector's timing |
| **Single-use, 60-second grant** bound to case, tenant, policy version and reviewer; the claims system requires it | Enforcement lives in the target, not in the agent's goodwill. The agent's own credentials alone get 403. | The agent calls the claims system directly after approval |
| **Read-back after every apply and every reopen** | Agents report effects that never happened (the Replit incident). We prove the effect from the target. | Trusting the 200 response |
| **Policy is a versioned document**, not code | Compliance can change a floor live; each decision stamps the version that allowed it; a second action type (`account_freeze`) needs only a new document. | Thresholds in code or config |
| **`$jsonSchema` checks shape only** | Thresholds belong in the policy so they can change without a deploy. | Thresholds in validators |
| **Change-stream detector as a second line**, with its resume token stored in Atlas | It catches slow-burn patterns (low median dwell) and survives being killed and restarted. The inline G6 check is the first line. | Detector-only enforcement |
| **`tenant_id` on every document and first in every index** | Two insurers on one cluster; one's suspension never touches the other. | A database per tenant |
| **The agent is rules-based; an LLM is optional and only drafts text** | "The LLM proposes, code decides." No model can grant itself authority. | An LLM deciding the denial |
| **Stack: Python + Spring Boot + Angular** | Matches the original three engineers' strengths. **Open question** now that the core team is two (see `PLAN.md` §9). | - |
| **No real auth, Docker or extra services** | Time. Demo login is a reviewer picker, and we say so. | - |
| **LangSmith = debugging view only** (new) | Atlas stays the single record of authority, which keeps the audit story simple. | Using traces as the audit log |
| **ElevenLabs spoken attestation is evidence, not a gate rule** (new) | Adds a meaningful, hard-to-bulk-stamp record without letting voice or AI influence a decision. | Making a voice check part of G1-G8 |

## Honest limits (say them first, before a judge finds them)

- **Dwell time is a proxy.** A script that fetches each item and fakes interaction for 31 s passes. We show it as the null result. Server timing raises the cost of faking from one click to sustained scripted work; it cannot prove reading.
- **The evaluation is simulated and time-scaled ÷10.** Synthetic data, not real reviewers.
- **Not a medical tool.** No PHI, no CPT text, no clinical validity.
- **Demo login is a reviewer picker.** In production: SSO plus licence checks against medical boards.
- **Cigna disputes the ProPublica report** and says PxDx is not AI. We say "the pattern as reported".
- **"None found" is not "proven new".** We ran four searches.
