# Plan critique (R5, dev-system:plan-critic, 13:00 EST)

The critic is read-only, so the tech lead saved its report here.
**Already out of date at 13:00:** the zip import (Q3) is merged (PR #1), both teammates are collaborators (Q8), and `main` holds the code. The rest stands.

**Verdict: CONCERNS.** The architecture is sound. The schedule and ownership are not: there is no cluster yet, `make smoke` has never passed, and Harry is a single point of failure.

## Ranked changes

1. **Make `static/index.html` the primary UI, and React a stretch goal** (only if `core-ok` is tagged by 14:15 and someone is idle). Saves Harry about 2-3 h and removes the Vite proxy, port 4200 and TypeScript as failure modes.
2. **Take Harry off the critical path.** Move eval, calibration and PREREGISTRATION to Sukhman (he wrote them). Move the live agent run to Sukhman or Neil. Harry keeps Atlas, `.env`, target, the reviewer path and the submission.
3. **Unblock the cluster now.** Create it inside the sandbox project from the invite email (a personal account makes us ineligible as finalists). DM the `.env` values to Sukhman early, so Harry is not the only one holding the credentials.
4. **Re-baseline the timeline:** smoke, setup and seed by 13:30; `core-ok` by 14:15. Keep the 16:00 freeze.
5. **Record a safe 1-minute video early** (about 14:30, after `core-ok`), with Neil as the single owner (ElevenLabs voiceover plus editing). Test the upload host by 14:30.
6. **Add a 6-second code shot to the video** (`pg/gate.py` plus the `make test-conflict` PASS lines). The rules require the video to show the code. Also say aloud: "synthetic data; Cigna disputes the report".
7. **Name an owner and a time for each submission task:**
   - Harry submits on Cerebral Valley by 16:30 and adds all three teammates.
   - Sukhman checks the repo while logged out and runs `make install test` on a fresh clone.
   - Neil owns the video and checks its audio on a second device.
   - The tech lead drafts the README results and the 120-word description as a PR.
   - `docs/enforcement-map.md` (PRD §16) does not exist: write it or drop it.
8. **Close the demo-fragility holes:**
   - `make burst-forged` is referenced in demo.md but missing from the Makefile.
   - Save `make test-conflict > docs/test-conflict.txt` as a fallback.
   - Time `make reset` (it should take under 60 s).
   - Keep a phone hotspot ready in case the Wi-Fi fails.
9. **Cut voice attestation and LangSmith tracing; keep only the ElevenLabs voiceover.** Bring tracing back only after `core-ok`. This frees Neil for the video, the repo check and the rehearsal.
10. **Drop volunteer sessions (Q2).** Use `make calibrate-prd`, labelled synthetic, and quote only numbers printed by `make eval`.

## Gaps against the hackathon must-dos

- **Video:** no code shot, no single owner for the final edit, and the upload host is untested.
- **Description:** no owner and no time slot.
- **Teammates on the submission:** each person's Cerebral Valley approval is unverified.
- **README:** must name the sandbox project or cluster.
- **Presenting:** nobody is named as presenter or driver for live judging from 17:15, and the dry runs collide with the video slot.
- **Freeze:** nobody enforces it. The tech lead refuses non-bugfix PRs after 16:00.
