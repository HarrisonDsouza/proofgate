# Neil: starting prompt

## What to pull

```bash
git clone https://github.com/HarrisonDsouza/proofgate.git && cd proofgate
git checkout neil
cp .env.example .env     # paste MONGODB_URI from Harry's DM; add your LangSmith and ElevenLabs keys
```

## What you own

**LangSmith and ElevenLabs only.** None of it is on the critical path, so the core demo must never wait on it.

| Piece | Where | Detail |
|---|---|---|
| LangSmith tracing of the agent | `@traceable` lines in `py/agent/` (agree with Harry first) | [project-docs/langsmith-setup.md](../project-docs/langsmith-setup.md) |
| ElevenLabs voiceover for the 1-minute video | outside the code | [project-docs/elevenlabs.md](../project-docs/elevenlabs.md), option 1 |
| Spoken attestation: `POST /voice/attest` (ElevenLabs speech-to-text, writes `attestations` to Atlas) + an Angular "Speak attestation" component | `py/voice/`, `ui/src/app/voice/` | `elevenlabs.md` option 2. **15:00 go/no-go.** |

## First steps, in order

1. **LangSmith** (`langsmith-setup.md` steps 1-5):
   - Create the account and key; put `LANGSMITH_*` in `.env`.
   - `pip install -U langsmith python-dotenv` (in the `.venv` from README step 5, or your own).
   - Run the hello trace and confirm one run appears in project `proofgate`.
2. **ElevenLabs key:**
   - Redeem the Creator coupon in the ElevenLabs Discord `#coupon-codes` (only if you checked in by 11 AM).
   - Put `ELEVENLABS_API_KEY` in `.env`, then run `pip install "elevenlabs<3"`.
3. **Spikes** (throwaway, don't commit): text-to-speech of one line of the video script (PRD §13) to mp3; speech-to-text of a 10-second phone clip.
4. **After Harry's agent runs** (handoff H5): add `@traceable` with grant ids redacted (H6). Open a PR.
5. **After 13:45, only if the core is green:**
   - `py/voice/` route + `attestations` writes, and the Angular component (H7, H8).
   - The gate needs a small change to accept `attestation_id`. Ask Sukhman; don't edit `gate/` yourself.
6. **15:30-16:15:** generate the final voiceover; help record and upload the 1-minute video with audio.

## Paste into Claude Code

```
You are helping a 3-person hackathon team build "ProofGate". Read CLAUDE.md, START-HERE.md, README.md,
WORKFLOW.md, project-docs/PLAN.md, project-docs/langsmith-setup.md and project-docs/elevenlabs.md first.

My role: LangSmith and ElevenLabs only. I work on branch `neil` and only touch py/voice/, ui/src/app/voice/,
and @traceable decorators in py/agent/ (after agreeing with Harry). I never edit gate/.

Rules:
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
