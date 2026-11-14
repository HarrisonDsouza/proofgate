# Hackathon rules, judging and deliverables

Sources:
- **The official resource guide.** This is the file you attached, "[EXTERNAL] AGENTS IN CONTEXT TORONTO … RESOURCE GUIDE". It is the same document as `Resources.md` and `docs/OFFICIAL-RESOURCE-GUIDE.md`. The only difference is that four links in `Resources.md` are newer.
- **Event facts** in `background/00-README-HANDOFF.md`, gathered from organiser emails on Nov 13-14.

> **Note:** no separate "guidelines and instructions" document was attached. The resource guide is the only official rules text we have. If the organisers sent another document (in Discord or by email), add it here and I will re-check everything below against it.

## Rules (losing these loses the event)

| Rule | What it means for us |
|---|---|
| **Build in the MongoDB Atlas Hackathon Sandbox** (the invite email link; org "Agents in Context Toronto"). | Create the cluster inside the sandbox project. A personal Atlas account makes us **ineligible as a finalist**. |
| **No prior projects: all work original.** | All code is written today. Planning documents are fine. Copy no code from other projects. |
| **Pick one of the three problem statements.** | We are in **Statement One: Agents You Can Audit.** |
| **MongoDB Atlas is the data, memory and state layer.** | Atlas is our only state store (PRD rule 1). |
| **Team of up to 4**, all approved on the Cerebral Valley platform. | Harry, Sukhman, Neil. All three must be checked in and approved. |
| **Demos are live and in person.** | Someone has to be at the table from 5:15 PM. |
| **Repository is public and the demo link works.** | Check from a logged-out browser before submitting. |

## Statement One, word for word, and what it asks

> Build an agent using MongoDB Atlas as the identity, policy and audit layer (collections, schema validation, change streams) that takes real actions across systems, where every action is tied to an identity, checked against policy before it runs, and recorded so a reviewer can reconstruct it afterward.

The statement asks three questions. Each has to be answered on screen:
1. How do you decide what an agent may do, and enforce it **before** the action?
   - Our answer: the gate transaction, plus the grant the claims system requires.
2. How do you record what the agent did, why, and under whose authority?
   - Our answer: approvals, gate decisions, the examiner page, and rules R1-R8.
3. How do you stop or roll back an agent mid-run?
   - Our answer: suspension, grant revocation, and reopened denials checked by read-back.

The statement names three MongoDB features: **collections, schema validation and change streams.** We use all three visibly.

## Judging

- **Criteria:** impact, innovation and technical feasibility. **No weights are published.**
  - This comes from a CompeteHub listing (medium confidence). The official guide lists no criteria.
- **Judges** (from the event page): Robert Maissan, Raschid Jimenez, Tapan Shah (all MongoDB), Leo Gomes, Aasawari Sahasrabuddhe, Sergey Strelnikov, Anamika Ahmed, Pablo Vallejo, Amrit Krishnan, Vatsal Shah, Parth Patel, Ahmed Radwan, Pahul Hallan, Noel Kirthiraj, Rudraksh Monga, Aasheesh Singh.
  - The "judge statements" in `docs/DECISION-RECORD.md` and PRD §4 come from **simulated personas**, not from these people. Never quote them as real.
- **Format:**
  - 5:15-6:45 PM: first round, live at our table. Plan for the 3-minute demo plus Q&A.
  - 7:00 PM: the top 6 present on stage.
  - 8:15 PM: winners announced.

## Prizes

| Place | Prize |
|---|---|
| 1st | US$7,000 + $3,000 LangSmith credits + 3 months ElevenLabs Pro |
| 2nd | US$5,000 + $2,000 LangSmith credits |
| 3rd | US$3,000 + $1,000 LangSmith credits |
| **Best Project Built with ElevenLabs** | 3 months ElevenLabs Scale tier (a separate category) |

There is **no separate LangSmith category.** LangSmith credits only come bundled with the placed prizes.

## Deliverables (submitted on the Cerebral Valley platform by 5:00 PM; our target is 4:45 PM)

1. A link to a **public GitHub repository**.
2. A **1-minute demo video** showing the code and the features built today, **with working video and audio**.
3. A **concise project description**. The draft is in PRD §16.
4. **Every teammate added to the submission.**

## Partner credits

| Partner | What we get | How | Do we use it? |
|---|---|---|---|
| ElevenLabs | 1 month Creator plan (131k credits) | ElevenLabs Discord `#coupon-codes` → Start Redemption → use the Cerebral Valley email. **Only for people checked in by 11 AM.** | Yes, Neil. See `elevenlabs.md`. |
| LangSmith | $50 credits plus Deployments | Airtable form within 10 days. A card is needed to display credits; it is not charged. | Yes, Neil. Tracing only. See `langsmith-setup.md`. |
| Voyage AI | 200M free tokens | dashboard.voyageai.com → API key → add a payment method | Only for S7 path B, which is cut early. Probably not used. |

## Schedule (EST)

| Time | Event |
|---|---|
| 10:45 | Hacking began |
| **12:40** | Our checkpoint: data in Atlas, transactions and change streams confirmed |
| **13:45** | Our checkpoint: core demo works |
| 14:15 | Commit `docs/preregistration.md` before any eval run |
| **15:30** | Feature freeze |
| 15:30-16:15 | Record the fallback video and the 1-minute video |
| **16:45** | Submitted (our target) |
| **17:00** | Submissions close |
| 17:15-18:45 | Live judging at our table |
| 19:00 | Top 6 on stage |
| 20:15 | Winners |
