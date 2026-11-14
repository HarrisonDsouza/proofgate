# Neil: starting prompt

## What to pull

```bash
git clone https://github.com/HarrisonDsouza/proofgate.git && cd proofgate
git checkout neil
cp .env.example .env     # paste MONGODB_URI from Harry's DM; add your LangSmith and ElevenLabs keys
```

## What you own (COMBINED-PLAN §2)

**LangSmith and ElevenLabs only.** None of it is on the critical path; the core demo never waits on it.

| Piece | Where | Detail |
|---|---|---|
| LangSmith tracing of the agent | tracing lines via `pg/observability.py` and `pg/agent.py` (agree with Harry first) | [project-docs/langsmith-setup.md](../project-docs/langsmith-setup.md) |
| ElevenLabs voiceover for the 1-minute video | outside the code | [project-docs/elevenlabs.md](../project-docs/elevenlabs.md), option 1 |
| Spoken attestation: `POST /api/voice/attest` (ElevenLabs speech-to-text, writes `attestations`) + a React "Speak attestation" button | `pg/voice.py`, `ui/src/voice/` | `elevenlabs.md` option 2. **15:00 go/no-go.** |

## First steps, in order

1. **LangSmith** (`langsmith-setup.md` steps 1-5):
   - Create the account and key; put `LANGSMITH_*` in `.env`.
   - Run `make install`.
   - Run the hello trace and confirm one run appears in project `proofgate`.
2. **ElevenLabs:**
   - Redeem the Creator coupon (ElevenLabs Discord `#coupon-codes`; only if you checked in by 11 AM).
   - Put `ELEVENLABS_API_KEY` in `.env`, then run `pip install "elevenlabs<3"`.
3. **Spikes** (throwaway, don't commit): text-to-speech of one video-script line (`project-docs/demo.md`) to mp3; speech-to-text of a 10-second clip.
4. **Tracing:** once Harry's agent runs live (handoff H5), add tracing to the agent steps with grant ids redacted (H6). Open a PR.
5. **After 13:45, only if the core is green:**
   - `pg/voice.py` + `attestations` (validator, `tenant_id`), and the React button (H7).
   - The approval endpoint needs a small change to accept `attestation_id` (H8). Ask Sukhman or Harry; don't edit their files.
6. **15:30-16:30:** generate the final voiceover and help record and upload the 1-minute video with working audio.

## Paste into Claude Code

```
You are helping a 3-person team build "ProofGate" at a MongoDB hackathon today. Read CLAUDE.md, README.md,
WORKFLOW.md, project-docs/COMBINED-PLAN.md, project-docs/hackathon-rules.md, project-docs/langsmith-setup.md
and project-docs/elevenlabs.md first.

My role (Neil): LangSmith and ElevenLabs only. I work on branch `neil` and only touch pg/voice.py,
ui/src/voice/, and tracing lines in pg/observability.py and pg/agent.py (after agreeing with Harry).

Before building, check the hackathon must-dos in project-docs/hackathon-rules.md (the 1-minute video needs
working audio) and these rules:
1. Never commit or print secrets. Keys live only in .env (git-ignored). The ElevenLabs key never reaches the
   browser: the browser sends audio to our Python route, and only the server calls ElevenLabs.
2. Tracing must change nothing when LANGSMITH_TRACING is false. Redact grant ids (first 6 chars only).
3. Voice is evidence only: it never affects gate rules G1-G8 or any decision.
4. Atlas documents I write have tenant_id and a $jsonSchema validator; indexes lead with tenant_id.
5. Pin elevenlabs to 2.x. Mark anything about model ids or SDK calls you are unsure of and check it.
6. After each piece, give me the exact command that proves it works.

Start now: walk me through the LangSmith setup in project-docs/langsmith-setup.md, one step at a time,
waiting for me to confirm each step.
```
