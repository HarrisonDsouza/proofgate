# What the demo must show

Source: PRD §13 and START-HERE §3. **Never improvise numbers.** Read them off the screen, or from `make eval` and `make rules` output produced today.

## The four moments that must work no matter what

1. **Bulk 50 → executed 0.**
   - `dr-stamper` clicks the red "Select all, approve 50". The banner shows "Executed: 0 of 50" with reasons: no evidence opened (G4), dwell below the floor (G5), too fast (G6).
   - **The reviewer is suspended mid-run.**
2. **An honest review executes.**
   - `dr-demo` opens both cited evidence items. The server-timed meter passes 30 s. They click Approve.
   - The denial executes, and the claims system is **read back** to prove it.
3. **A bypass is refused.**
   - curl the claims system directly with no grant → **403**. The examiner page shows `REFUSED_NO_GRANT`.
4. **The examiner rebuilds a case.**
   - What the agent cited, what the reviewer opened and for how long, every gate rule ✓/✗, the policy version, the grant, and the read-back.

Each moment maps to Statement One:
- (1) and (3) answer "enforce before the action".
- (4) answers "record who, what and why".
- (1) plus the reopen answers "stop or roll back mid-run".

## Nice to show if built (in this order)

5. **Reopen.** After a suspension, an already-executed denial is reopened in the claims system and verified by read-back (M10, M11).
6. **`make test-conflict`.** A suspension during an in-flight approval forces a write conflict; the retry refuses (`txn_attempts=2`).
7. **Live policy edit.** Raise the floor from 30 s to 60 s; the next call is refused citing the new policy version. This needs the supervisor page (S5) or a curl.
8. **Eval table,** including the forger "null result" (a script that fakes interaction gets through, and we say so).
9. **Spoken attestation** (ElevenLabs, if it shipped): the transcript and audio hash show on the examiner page.
10. **LangSmith trace** of one denial, as the debugging view (Atlas stays the record).

## 1-minute submission video (PRD §13)

Neil generates the narration with ElevenLabs text-to-speech. Before recording, check every spoken figure against R1's verified wording.

| Seconds | Picture | Voice |
|---|---|---|
| 0-6 | Title: "1.2 seconds per claim", with the ProPublica headline (cited) | "ProPublica reported insurer physicians denying claims at about 1.2 seconds each. Fifty at a time." |
| 6-14 | `dr-stamper`'s review page, cursor on the red button | "Agents make this worse. They can queue thousands of denials an hour. So we gave our reviewer the exact batch button." |
| 14-24 | Click → "Executed: 0 of 50" → SUSPENDED | "Fifty approvals hit Atlas. The gate transaction refuses every one … the reviewer is suspended mid-run." |
| 24-36 | `dr-demo` opens E1 and E3, meter to 30 s, Approve → executed and read back | "A real review … timed by the server, not the browser … we read the claims system back to prove it." |
| 36-46 | Examiner timeline | "An examiner rebuilds any case …" |
| 46-54 | Reopen shown (if built; otherwise show the bypass 403) | "When authority is revoked, past denials are reopened and verified." |
| 54-60 | Logo + "MongoDB Atlas: transactions · $jsonSchema · change streams" | "ProofGate. No proof of review, no denial." |

**Must say somewhere** (on screen or in the description): synthetic data only; Cigna disputes the report; "the pattern as reported".

## 3-minute live table demo

**Prep before 17:15:**
- `make reset`
- start the target, gate, detector, agent and UI
- open tabs: review (`dr-stamper`), review (`dr-demo`), examiner, terminal, LangSmith (optional)
- the fallback video is downloaded locally

| Time | Step | Fallback |
|---|---|---|
| 0:00-0:20 | The problem in one breath, plus the buyer (Chief Compliance Officer / General Counsel) | - |
| 0:20-0:50 | **The judge clicks "approve 50"** → 0 of 50, suspended | Play the fallback video; run `make test-conflict` in the terminal (its last lines are the forged burst: 0 of 50) |
| 0:50-1:10 | `make bypass` → 403; the examiner shows the refusal | Show the `target_log` doc in Atlas Data Explorer |
| 1:10-1:50 | **The judge reviews as `dr-demo`** for 30 s → executed + read-back. Narrate the server timing during the wait. | Use the pre-approved `dr-prep` case |
| 1:50-2:15 | Policy floor 30→60 s, next call refused citing the new version (if built) | Screenshot from the dry run |
| 2:15-2:40 | `make test-conflict` output | Saved `docs/test-conflict.txt` (run 15:57 today) |
| 2:40-3:00 | Eval table incl. the forger null result; R1-R8 ✓ | README section |

## Rehearsal

- Two full dry runs between 16:00 and 16:30.
- Each teammate can deliver the 20-second problem statement and answer the top five questions in `judge-qa.md`.
