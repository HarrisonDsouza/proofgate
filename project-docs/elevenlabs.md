# ElevenLabs: can it improve our chances?

**Owner:** Neil.
**Status:** proposal. Nothing is built until the plan is approved.

## Short answer

- **For the main prizes: probably very little.**
  - The published criteria are impact, innovation and feasibility.
  - Most judges are infrastructure and security people (MongoDB, Okta, Microsoft, Cohere, Wealthsimple). Their likely questions are about transactions, bypasses and forged dwell, not voice.
  - Bolting voice onto the core story could even blur it.
- **For the separate "Best Project Built with ElevenLabs" prize: a real extra chance.**
  - It is an extra prize category, and Neil works on it in parallel, so it costs the core build nothing.
  - We have not seen that prize's judging criteria. The ElevenLabs Hacker Guide (a Google Doc linked from the resource guide) may list them. A researcher agent will check after approval.
- **For the 1-minute video, a guaranteed practical win.** The submission needs a video with working audio. An ElevenLabs voiceover gives clean, consistent narration that we can regenerate in seconds if the script changes.

**Recommendation:** do option 1 for certain, and option 2 as a contained add-on. Skip options 3 and 4.

## Options considered

| # | Idea | Helps us how | Risk | Verdict |
|---|---|---|---|---|
| 1 | **Voiceover for the 1-minute video.** Generate the narration from the PRD §13 script with ElevenLabs text-to-speech. | Clean audio, which the submission requires. Also a small credible use of ElevenLabs. | Very low. No product code. | **Do it.** |
| 2 | **Spoken attestation.** The reviewer says aloud what they checked. ElevenLabs speech-to-text (Scribe) transcribes it on the server. The transcript and a SHA-256 hash of the audio are stored in Atlas as attestation evidence, and the examiner page shows it. | Fits the product: a spoken, case-specific statement is much harder to bulk-stamp than a checkbox, and it becomes part of the audit record. Real use of ElevenLabs for the category prize. | Medium. It touches the approval flow. It is kept **out of the gate rules** so it cannot break the core demo. | **Do it after the 13:45 checkpoint, behind a feature flag.** This is PRD item C4. |
| 3 | Examiner page reads the case timeline aloud with text-to-speech. | Little. | Low | Skip (gimmick) |
| 4 | Voice agent for the supervisor ("halt dr-stamper"). | Little. It adds a new path that can take actions, which judges will probe. | High | Skip |

## Option 2 design (deliberately minimal)

1. The review page gets a **"Speak attestation"** button. The browser records audio with the standard MediaRecorder API.
2. The browser posts the audio to **our Python service**, at a new route such as `POST /voice/attest`.
   - **The ElevenLabs key never goes to the browser.** Only the server calls ElevenLabs.
3. The server calls ElevenLabs speech-to-text and writes a new `attestations` document:
   - fields: `tenant_id, attestation_id, session_id, reviewer_id, case_id, transcript, audio_sha256, stt_model, created_at`
   - it has its own `$jsonSchema` validator, and its index leads with `tenant_id`.
4. The approval request can carry `attestation_id`. The gate service copies the transcript into `attestation_text` and stores the id on the approval. The examiner page shows "spoken attestation: transcript + audio hash".
5. **No change to gate rules G1-G8.** The voice is evidence, not a decision-maker. This keeps the PRD rule "the LLM proposes, code decides". It also means a voice failure can never block or allow a denial.
6. Fallback: if speech-to-text fails, the reviewer types the attestation as today.

**Handoffs this needs.** All of these happen after 13:45, and only if the core is green:
- Sukhman: accept `attestation_id` on `POST /api/approvals`, and show it in the examiner API. About 20 lines.
- Harry: add the `attestations` validator and index to `setup_db.py`, and place Neil's Angular button component on the review page.

## Steps for Neil

1. Redeem the Creator coupon (ElevenLabs Discord `#coupon-codes`; this only works if you checked in by 11 AM). Otherwise use a free account, but check its credit limits first.
2. Create an API key and put it in `.env` as `ELEVENLABS_API_KEY`. Never commit it.
3. Run `pip install "elevenlabs<3"`. Version 2.x is pinned because a 3.0 pre-release exists.
4. Spike A, text-to-speech: generate one line of the video script to an mp3 and listen to it.
5. Spike B, speech-to-text: transcribe a 10-second phone recording.
   - Try model `scribe_v2` first and fall back to `scribe_v1`. The exact model ids are [VERIFY]; the researcher agent will confirm them.
6. After 13:45: build `/voice/attest` and the Angular button, then hand off as above.
7. From 15:30: generate the final video voiceover from the agreed script.

## Cut rule

- If option 2 is not working end to end by **15:00**, drop it and ship option 1 only.
- Option 2 must never delay a MUST item.
