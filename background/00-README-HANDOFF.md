# MongoDB Toronto Hackathon 2026: Handoff and Shared Requirements

Read this file first. It gives any person or AI session everything that was decided before the build, so nothing has to be re-derived. The four project PRDs in this folder each assume you have read it.

| File | What it is |
|---|---|
| `00-README-HANDOFF.md` | This file: event facts, how the ideas were chosen, rules every project must follow, the "don't lose points" checklist |
| `01-PRD-Shiftline.md` | **Winner.** Spoken shift handover that compiles into live equipment lockouts |
| `02-PRD-Countersign.md` | **Runner-up 1.** Voice-clone-proof step-up check before an agent moves money |
| `03-PRD-LiftLine.md` | **Runner-up 2.** Calls a wheelchair user before they leave home when an elevator on their trip breaks |
| `04-PRD-GreenPass.md` | **Runner-up 3.** Spoken kitchen closing check built on a restaurant's own Toronto inspection history |

Pick **one** project. A team of three cannot build two in a day.

---

## 1. The event (verified Nov 13–14, 2026)

| Item | Value | Source / confidence |
|---|---|---|
| Name | Agents in Context Toronto: a MongoDB Hackathon | Cerebral Valley and Luma emails to the team; high |
| Date and hours | Saturday Nov 14, 2026, 9:00 AM – 9:00 PM EST | Approval emails; high |
| Venue | The Quay, 100 Queens Quay E, 3rd Floor, Toronto. Lobby entrance off Queens Quay East, right of the LCBO doors. Bring government photo ID | Organizer blast, Nov 13; high |
| Team size | Up to 4 | Event listings; high |
| Hard rule | **To be eligible as a finalist, the project must be built inside the MongoDB Atlas sandbox** the team was invited to (org "Agents in Context Toronto") | Organizer blast, Nov 13; high |
| Registration | Every teammate must be **approved on the Cerebral Valley platform**; approval is used for partner resource access | Organizer blast; high |
| Theme | Agents that hold context across sessions, adapt their own guardrails, and operate reliably under real workloads; "infrastructure future agents can run on". Built with MongoDB Atlas, Atlas Vector Search and agentic memory tooling | Event listings; high |
| Judging criteria | Impact, innovation, technical feasibility. **No weights published** | CompeteHub listing; medium |
| Prizes | 1st: US$7,000 + $3,000 LangSmith credits + 3 months ElevenLabs Pro. 2nd: US$5,000 + $2,000 LangSmith credits. 3rd: US$3,000 + $1,000 LangSmith credits. **Best Project Built with ElevenLabs:** 3 months ElevenLabs Scale | Official resource guide; high |
| **Submission deadline** | **5:00 PM EST, Saturday Nov 14.** Hacking started about 10:30 AM after a 10:00 AM kickoff, so there are about **6 build hours, not 10**. Every schedule in the PRDs must be compressed: see §8 | Organizer blast, 10:28 AM Nov 14; high |
| ElevenLabs credits | 1 free month of Creator tier, only for people who **checked in before 11:00 AM** | Organizer blasts, Nov 14; high |
| Atlas sandbox invite | Sent in batches; if missing, contact the Cerebral Valley organizer named in the 8:00 AM blast | Organizer blast, Nov 14; high |
| Questions on the day | `#questions` channel in Discord, or any MongoDB or Cerebral Valley team member | Organizer blast; high |
| Problem statements | **Every project must be built in one of three official statements**, with MongoDB Atlas as the data, memory and state layer. See §1.1 | Official resource guide; high |
| Schedule | 9:00 doors, **10:45 hacking begins**, **5:00 PM submissions due**, 5:15–6:45 first-round judging (live, in person), 7:00 top 6 present, 8:15 winners | Official resource guide; high |
| **What you submit** | On the **Cerebral Valley platform**: (1) link to a **public GitHub repo**, (2) a **1-minute demo video** showing the code and functionality built today, with working audio, (3) a concise project description. **Add every teammate to the submission** | Official resource guide; high |
| Originality | **No prior projects: all work must be original** (built today). The planning documents are fine; do not reuse code from other projects | Official resource guide; high |
| Partner credits | ElevenLabs Creator plan, 1 month, 131k credits (ElevenLabs Discord `#coupon-codes`, only if checked in by 11 AM). **Voyage AI: 200 million free tokens** (create an account, API key, and add a payment method to unlock rate limits; no charge within the allowance). LangSmith: $50 credits via a form within 10 days | Official resource guide; high |
| Discord | Linked in the organizer emails; all logistics are posted there | — |

### Judges (from the user; roles from the event page)

MongoDB: Robert Maissan (Senior Lead, Engineering), Raschid Jimenez (Senior PM), Tapan Shah (Service Engineer). Others: Leo Gomes (Pelmorex), Aasawari Sahasrabuddhe (Okta), Sergey Strelnikov (Acerta), Anamika Ahmed (Microsoft), Pablo Vallejo (Wealthsimple), Amrit Krishnan (Vector Institute), Vatsal Shah (Speak AI), Parth Patel (Cohere), Ahmed Radwan (Vector Institute), Pahul Hallan (Zafin), Noel Kirthiraj (Omni), Rudraksh Monga (Stan), Aasheesh Singh (Quantiphi).

---

## 1.1 The three official problem statements (from the organizers' resource guide)

**Pick exactly one and say its name in the pitch, the video and the description.**

| Statement | What must be built | The three questions judges will ask |
|---|---|---|
| **One: Agents You Can Audit** | An agent using Atlas as the **identity, policy and audit layer** (collections, **schema validation**, **change streams**) that takes **real actions across systems**; every action tied to an identity, checked against policy **before** it runs, and recorded so a reviewer can reconstruct it | How do you decide what an agent may do and enforce it before the action? How do you record what it did, why, and under whose authority? **How do you stop or roll back an agent mid-run?** |
| **Two: Memory You Can Govern** | An agent using Atlas **and Vector Search** to persist and retrieve memory, so memory **changes what it does on the next run**, with rules for **who can read each memory, how long it lives, how it is corrected or forgotten** | How do you keep one client's or team's memory from leaking into another's? How does the agent fix or drop a wrong or expired memory? **How do you prove a memory changed behaviour and didn't just fill the prompt?** |
| **Three: Finish the Job** | An agent completing a **long multi-step task across several systems**, using Atlas to persist **verified task state** and **Vector Search to retrieve past experience**, surviving crashes and system changes | How does it tell an action that **took effect** from one that was only sent? How does it **resume after a crash** without replaying its whole history? How does it **adapt when a system's layout, fields or workflow change**? |

## 1.2 Which statement each project enters, and what it must add

| Project | Statement | Fit | Must add (details in each PRD's "Problem statement fit" section) |
|---|---|---|---|
| **Shiftline** | **One: Agents You Can Audit** | **Strong.** Identity (roles, service identity), policy before action (fail-closed operate check), audit (decision log), change streams already designed | `$jsonSchema` validation; a multi-step **agent run that is stopped mid-run** by a new lock, with rollback of completed steps; actions across separate systems (work orders, permits, equipment control) |
| **Countersign** | **One: Agents You Can Audit** | **Strong.** Identity, tiered policy before action, audit row per action | Schema validation; **mid-run stop** of a queued payment batch; **rollback** of a released bank-detail change within a hold window |
| **LiftLine** | **Two: Memory You Can Govern** | **Moderate.** Per-rider memory already changes the next call, but it used no Vector Search | Vector Search over rider memories; per-rider isolation filter; expiry (TTL) for temporary constraints; spoken correction or deletion of a memory; before/after proof |
| **Green Pass** | **Two: Memory You Can Govern** | **Weak-moderate.** Case memory changes the next shift | Per-location isolation for multi-location operators; correction of a wrong reading with audit; Vector Search retrieval of past corrective actions |
| RUNBOOK v2 (Appendix A) | **Three: Finish the Job** | **Strong, arguably the cleanest fit of any idea.** Statement Three asks for verified task state, past experience via Vector Search, crash resume, and adapting to system changes, which is RUNBOOK's design | It lost the simulated tournament as a "saturated theme", but the official statement explicitly asks for this. Reconsider it if the team prefers |

**Honest note:** the simulated judges ranked these ideas before the official statements were known. Statement fit is now a hard requirement, so Shiftline and Countersign gain, LiftLine and Green Pass need more work to qualify convincingly, and RUNBOOK v2 deserves a second look.

## 2. How these four ideas were chosen (so you know what the "judge" quotes are)

**Important caveat:** every judge opinion quoted in these PRDs comes from **simulated personas**, not the real people. Sixteen AI agents each role-played one judge, built from public information about that person where it could be found and otherwise from their job title and employer. They are one model playing sixteen roles, so their agreement is weaker evidence than it looks. Treat them as a stress test of the idea, not a prediction of the real panel.

The process, in order:

1. **Round 0 (rejected).** The panel first reviewed five ideas (Scar Tissue learned guardrails, Memory Time Machine, Handoff on-call agent, Permissioned Memory, CareLoop discharge calls), merged the favourite into "Policy Ledger + Guardrail CI", then compared it with the team's own plan **RUNBOOK** (verified procedural memory measured on a benchmark). The panel preferred a RUNBOOK-led hybrid ("RUNBOOK v2"). See Appendix A.
2. **Research.** Six agents searched for past MongoDB and Cerebral Valley hackathon winners (54 past projects found; see §3).
3. **New ideas.** Six agents generated 18 new ideas from six angles, explicitly barred from past winners and from saturated themes (including RUNBOOK's guardrail-learning family).
4. **Novelty check.** A sceptic per batch searched for existing projects or products doing the same thing. **12 of 18 were rejected as derivative.** The 6 survivors scored only 6–7/10 for novelty; each has a named nearest neighbour, listed in its PRD.
5. **Debate, three rounds.** All 16 judges scored the 6 survivors plus RUNBOOK v2. Round 1 independent; round 2 each judge read the others and replied to two by name; the top four were then **rewritten to answer the objections**; round 3 final ballots on the rewritten specs. No runoff was needed.

### Final result (4-3-2-1 points per ballot, 16 judges)

| Rank | Project | R1 → R2 → R3 points | R3 first-place votes | Avg impact / innovation / feasibility (R3) |
|---|---|---|---|---|
| 1 | **Shiftline** | 48 → 51 → 56 | 8 | 8.1 / 8.1 / 6.8 |
| 2 | **Countersign** | 44 → 50 → 47 | 4 | 7.8 / 7.4 / 6.9 |
| 3 | **LiftLine** | 44 → 38 → 36 | 3 | 6.9 / 5.2 / 8.1 |
| 4 | **Green Pass** | 7 → 10 → 20 | 1 | 5.2 / 4.8 / 7.1 |
| — | DockSwap, Surge Line | dropped out | 0 | — |
| — | RUNBOOK v2 (team's plan) | 0 every round | 0 | penalised as a saturated theme; see Appendix A |

---

## 3. What past winners did (learn the method, never the topic)

Found by search; placements are medium-to-high confidence, "why it won" is **inference** (no judge rationale was published for any event, and no official rubric was found).

| Event | Placed projects |
|---|---|
| MongoDB Agentic Memory & Context Engineering, San Francisco, Oct 11 2025 (~75 projects) | 1st ForgetMeNot (real-time context for people with dementia), 2nd ContextScope (evaluation of agent-to-agent context sharing, named metrics), 3rd WebBrain (browsing memory). Finalist MonGOD (incident copilot) |
| MongoDB Agentic Orchestration & Collaboration, San Francisco, Jan 10 2026 | Just Price (hospital billing advocate) reported as winner; finalists Moongrate (agentic Postgres→MongoDB migration), Watch and Learn, Polaris, EvacuTrace, SOGA |
| MongoDB Agentic Evolution, London, May 2 2026 (70+ teams) | 1st Plan Pass AI (planning-permission checks for homeowners; opened with a ~£900M/yr loss figure; also won community vote), 2nd RunwayOps (payroll-risk agent with human-approved actions and audit trail), 3rd Volt Control; finalists Substrate (shared memory layer, did not place), Glass Houses, Cooks |
| MongoDB Harness Engineering, NYC and SF Tech Week 2026 | MongoMation (PLC agent with durable checkpoints, 1st SF), LabRat (lab agent, approval boundary, 2nd SF), Ripple, Da Vinci, Ada (finalists). Gallery entries also exist for **Notary, Probity/Ratchet, Aegis** (memory admission, mistakes→tested rules, tool governance) |

### Winning patterns (apply all of them)

1. **One named user with one costly, concrete failure**, said in one sentence a non-specialist executive can repeat.
2. **Take the event theme literally and aim it at a sharp problem**, not a generic agent.
3. **Atlas is load-bearing inside the agent loop**, not a side datastore.
4. **Correctness checked by something harder than an LLM opinion** (rules over stored state, hashes, physics, tooling). A measured before/after number.
5. **A demo that survives a live stage**: one visible real-time moment, narrow scope. Top-6 finalists re-demo days later at MongoDB.local.
6. **A headline number for the size of the problem** opens the pitch.
7. **Consequential actions behind human approval gates with an audit trail.**
8. **A clear buyer or adopter.** Vertical applications took 1st and 2nd in London.

### Losing patterns (avoid every one)

1. Generic "memory engine" or "chatbot with long-term memory" (the galleries are full of them; none placed).
2. Treating the sponsor stack as the differentiator: Atlas Vector Search plus embeddings is table stakes.
3. General frameworks or shared-memory layers with no named user.
4. Scope too broad for one day; a demo that only works at a judging table.
5. Quality claimed by assertion or by an LLM judge alone.
6. Plain RAG.

### Saturated themes (do not drift into these)

Human memory aids and recall; agent memory/context infrastructure (shared layers, admission control, context evaluation); browser agents learning from demonstrations; developer/ops copilots (incident, migration); self-improving harnesses for physical engineering output; threat-intel feeds for agents; learned guardrails mined from agent mistakes; post-call/discharge voice companions.

---

## 4. Requirements every project must meet (the "don't lose points" checklist)

These came up repeatedly across all three debate rounds. Each PRD maps them to its own features.

### 4.1 Eligibility and logistics (lose everything if missed)

- [ ] Every teammate approved on Cerebral Valley before registration closes.
- [ ] **All code and data run in the event's Atlas sandbox project.** Create the cluster there on arrival; do not use a personal Atlas project.
- [ ] Name the official statement (§1.1) and answer its three questions explicitly in the demo, the video and the description, in the statement's own words.
- [ ] Submit on the Cerebral Valley platform **before 5:00 PM**: a **public** GitHub repo link, a **1-minute** demo video (check video and audio both play), and a concise description. **Add every teammate.**
- [ ] Create a **new public GitHub repo** for today's work; all code must be written today ("no prior projects"). Check the repo is public from a logged-out browser.
- [ ] Be at your table for **live in-person first-round judging from 5:15 PM**; the top 6 present on stage at 7:00 PM.
- [ ] Join the Discord.
- [ ] Check API keys and credits on arrival: LLM provider (an **API** balance, not a chat subscription), ElevenLabs, embeddings provider, LangSmith. Partner credits come through Cerebral Valley approval.
- [ ] Do not start coding before the official start unless the rules say pre-work is allowed. Reading docs and planning is fine.
- [ ] Use only synthetic or properly public data. No real personal, financial or plant records. Voice clones only of a consenting team member.

### 4.2 Theme fit (impact and innovation)

- [ ] Say in the first 30 seconds which part is **context held across sessions**, which part is a **guardrail the agent adapts**, and what makes it **reliable under load**.
- [ ] Show a **new session** inheriting state from an earlier one, live. Every judge persona asked for this; it is the theme.
- [ ] Name the one user and the one costly failure; open with a sourced headline number (verify it on the day; never show an unverified figure).
- [ ] Name the buyer in one sentence (Noel Kirthiraj persona asked "who pays?" of every project).

### 4.3 MongoDB depth (the three MongoDB judges)

- [ ] Atlas is in the action path: the decision the agent makes reads from Atlas at decision time.
- [ ] At least one capability beyond vector search does real work: change streams, multi-document transactions, time-series collections, `$graphLookup`, multikey/compound indexes, geospatial. Each PRD names its own.
- [ ] Show an **explain plan** for the hot query on screen (Tapan Shah and Robert Maissan personas asked for this on every project). An index scan with keys examined ≈ documents returned is the goal.
- [ ] No "dumb JSON bucket": real schema, indexes created deliberately, documents that model the domain.
- [ ] If you use change streams, **persist the resume token** so a restart does not silently miss events (Maissan, Shah).
- [ ] Be able to answer "what does this add beyond Atlas Agent Engine?" Atlas Agent Engine (public preview, Sept 2026) has a Policy Engine with **static** tool allowlists and execution budgets only; nothing in it learns or changes policy from context. Every project here adds a **dynamic, context-derived** control on top.

### 4.4 Evidence (the evaluation judges: Krishnan, Radwan, Singh, Hallan, Strelnikov)

- [ ] **Pre-register** before the first run: test set, number of trials, metrics, baselines, and the rule that a flat or negative result is shown as-is. Commit that file to the repo with a timestamp.
- [ ] Report **both error types**: harmful actions allowed **and** legitimate actions wrongly blocked (false-block / false-refusal rate). A system that blocks everything is useless; judges will ask.
- [ ] A **real baseline**, not a strawman. "No system" is a strawman whenever something simple already exists.
- [ ] **Do not grade your own homework.** At least one test set written by people outside the team, or drawn from public data, reported in its own row.
- [ ] Pass/fail decided by a **rule over stored state**, not by an LLM judge.
- [ ] Show counts and sample sizes (n), not just percentages. Small n gets an honest caveat.
- [ ] Never show a number you did not measure today. Label synthetic data as synthetic.

### 4.5 Safety and identity (Sahasrabuddhe, Vallejo, Hallan, Patel)

- [ ] **Fail closed.** When the system is unsure (ambiguous match, unconfirmed claim, missing record), it blocks or refuses. Shiftline lost points in round 1 for failing open and won after fixing it.
- [ ] **Voice is not identity.** Who someone is comes from a login with a role, not from how they sound.
- [ ] Agents get a **service identity** that can request but cannot approve or close.
- [ ] Consequential actions need a **human approval** with the approver recorded.
- [ ] An **audit/decision log** recording what was checked (ids read), not just "passed".

### 4.6 Demo robustness (Vatsal Shah, Leo Gomes personas)

- [ ] Build the **in-browser voice fallback first**; treat phone calls and live speech as upgrades.
- [ ] A typed-input fallback for every spoken step.
- [ ] Rehearse on the venue microphone; use a clip-on or headset mic.
- [ ] **Record a 2–3 minute backup video** by 5:30 PM.
- [ ] Pre-run the full evaluation and show stored results; run live only the one moment that matters.
- [ ] Pin the demo task so a non-deterministic model cannot "fail to fail" on stage.
- [ ] Keep total demo at or under 3 minutes; rehearse with a timer at least 3 times.

### 4.7 Sponsor prizes (cheap points)

- [ ] **LangSmith**: trace every LLM and tool call; show one trace in the demo or the submission. Use LangSmith experiments for the before/after table if time allows.
- [ ] **ElevenLabs**: voice must be intrinsic (hands-busy, phone-out, or clone-resistance), not bolted on. All four projects qualify; Countersign and Shiftline most strongly.

---

## 5. What each project would help with (plain-language summary)

| Project | Who it helps | The harm it prevents | Who would pay |
|---|---|---|---|
| **Shiftline** | Night-shift maintenance leads at transit yards and plants, and any AI agent acting for them | A worker or agent restarting equipment that the previous shift left unsafe because one fact was lost at handover (the 1988 Piper Alpha disaster followed exactly this) | Plant safety/operations managers; transit maintenance departments; permit-to-work software vendors as a voice layer |
| **Countersign** | Accounts-payable clerks and finance teams using voice agents | A cloned voice of the CFO telling an agent to change a supplier's bank details or send a payment (the 2024 Arup deepfake case, ~US$25M) | Finance controllers and fraud budgets; mid-market companies without enforced callback; AP automation vendors |
| **LiftLine** | Toronto wheelchair users who ride the subway | Arriving at a station to find the only elevator broken, with no warning and no step-free alternative | Transit agency accessibility/paratransit programmes (slow public procurement) |
| **Green Pass** | Owners and cooks of independent Toronto restaurants | Repeating the same food-safety infraction that the inspector already cited, and breaches that are "fixed" by someone saying so | Multi-location operators and franchise groups |

---

## 6. Recommended choice

- **Default: Shiftline, entered under Statement One (Agents You Can Audit).** The panel's clear winner, and it already answers two of Statement One's three questions; add the mid-run stop and schema validation. It also fits the ElevenLabs prize. Risks: no one on the team knows plants (all asset and work-order data is invented), and voice in a noisy hall is fragile.
- **Safest build: LiftLine** (feasibility 8.1), if a Toronto elevator-status source can be confirmed on the morning. Lowest innovation score.
- **Best evaluation story: Countersign**, if the team is comfortable cloning a teammate's voice live.
- **Green Pass** only if the team wants real public data above everything else.

---

## 7. How to hand this to another session

Give the build session this prompt:

> You are building a one-day hackathon project. Read `docs/hackathon/mongodb-toronto-2026/00-README-HANDOFF.md` fully, then `<chosen PRD file>` fully. Do not change the product's scope or invariants without asking. Follow the PRD's build schedule and cut order, implement requirements in priority order (all MUST before any SHOULD), and keep the pre-registered evaluation honest: never report a number that was not measured. Start by setting up the repository skeleton, the Atlas collections and indexes from the data model section, and the data contract between the three engineers.

---

## 8. Compressed schedule (deadline 5:00 PM, overrides every PRD's schedule)

The PRD schedules assumed submission at 6:30 PM. With a 5:00 PM deadline, use this instead and apply each PRD's cut order earlier.

| Time (EST) | All projects |
|---|---|
| 10:45–11:15 | Pick the project **and its statement**, agree the API contract and collections, create the public GitHub repo, create the Atlas cluster in the sandbox, get Voyage AI and LLM keys, redeem ElevenLabs credits |
| 11:15–13:00 | Core path only: the one MongoDB-backed decision (the PRD's "never cut" items) working end to end with typed input |
| 13:00–14:30 | The statement's third question (mid-run stop and rollback, governed memory, or crash resume), voice on top (browser first), explain plan |
| 14:30 | Commit `PREREGISTRATION.md`, then run the smallest honest evaluation (cut set sizes in half; keep the outside-written row and the false-block rate) |
| 15:30 | **Feature freeze.** Bug fixes only |
| 15:30–16:15 | Record the **1-minute submission video** (code plus working functionality, audio checked); rehearse the live demo |
| 16:15–16:45 | Write the description and README, confirm the repo is public, add all teammates, **submit on the Cerebral Valley platform** |
| 16:45–17:00 | Buffer. Do not start anything new |
| 17:15– | Live judging at your table; if top 6, stage at 7:00 PM |

Cut first, in every project: polish, stretch (COULD) items, the second language or second agent, and large synthetic data loads (use thousands, not 100,000).

---

## Appendix A: RUNBOOK v2 (the team's original plan, kept for reference)

Learned, versioned workflow "playbooks" (trigger, preconditions, forbidden transitions, postconditions, source trajectory ids, named approver, version, status candidate/active/retired, validity window) stored in Atlas; a deterministic validator at the tool-call boundary; a replay gate that promotes a playbook only if it causes no regressions on a dev split; measured on **tau2-bench airline** (not STATE-Bench) with the same frozen model with and without playbooks, labelled "pilot, not leaderboard". All 16 personas said "ship" after these fixes: pre-register ≥3 trials per task and show per-task pass/fail; define "false block" yourselves (validator rejects an action the reference solution takes); hand-write 2–3 seed playbooks labelled "human-authored" and report them separately from extracted ones; a blocked call must return the violated precondition so the model can retry; filter `status: active` and validity window inside `$vectorSearch`; validator enforces approver and expiry; Python in one process for agent/validator/harness, Angular for the console, no Spring. It scored 0 in the final tournament because it sits in a saturated theme (Notary, Probity/Ratchet and Aegis exist in a 2026 MongoDB gallery, and a public STATE-Bench entry mines rules from trajectories). Choose it only if the team prefers benchmark evidence over a novel product.

## Appendix B: Facts to verify on the day before they go on a slide

| Claim | Status |
|---|---|
| Piper Alpha, 6 July 1988, 167 deaths; a pump restarted after a handover failed to pass on that its pressure safety valve had been removed | Widely documented; from training data, not re-checked during planning |
| Arup lost about US$25M (HK$200M) to a deepfake video call in 2024 | Widely reported; from training data, not re-checked |
| Ontario Food Premises Regulation (O. Reg. 493/17): cold holding ≤ 4 °C, hot holding ≥ 60 °C | From training data; check the regulation text |
| DineSafe dataset on Toronto Open Data and its field names | Dataset exists; field names must be checked from the file |
| TTC elevator outage information: a machine-readable feed or archive | **Not confirmed.** Check on the morning before choosing LiftLine |
| Atlas Agent Engine Policy Engine = static tool allowlists and execution budgets | From MongoDB docs via search, Nov 13 2026 |
| Plan Pass AI's ~£900M figure | The team's own claim, not independently verified; cite as such if mentioned |
