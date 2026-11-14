# Research for Neil: ElevenLabs and LangSmith

**Checked:** 2026-11-14, from the official docs, PyPI and the SDK source on GitHub (main branch). Every source below was opened today.
Anything I could not confirm is marked **[UNVERIFIED]**. No code was changed.

## Headline corrections to our docs

- **Scribe model ids have moved on.** `scribe_v3` is now the current batch model. `scribe_v2` is "previous generation, still available". `scribe_v1` is **deprecated**. Our plan says "try scribe_v2, fall back to scribe_v1". Change it to **`scribe_v3`, falling back to `scribe_v2`**.
- **The text-to-speech flagship is now `eleven_v4`.** The quickstart uses it.
- **`elevenlabs<3` is still the right pin.** The latest stable is 2.78.0 (Nov 12 2026). 3.0.0a1 is a pre-release.
- **The LangSmith input/output hooks exist.** `@traceable(process_inputs=..., process_outputs=...)` is the documented API. The [VERIFY] in langsmith-setup.md can be cleared.
- **No published criteria for the ElevenLabs prize.** The Hacker Guide has none (details in section 3).
- **The agent does not call the gate over HTTP.** `pg/agent.py` calls `gate.execute`, `target.apply` and `gate.confirm` as in-process Python functions. langsmith-setup.md describes them as HTTP calls. The span names still work.

---

## ElevenLabs

### 1. Speech-to-text: `client.speech_to_text.convert` (SDK 2.x)

Signature, from the SDK source (`src/elevenlabs/speech_to_text/client.py`). The arguments are keyword-only:

- **Required:** only `model_id: str`.
- **Usually used:** `file`, `language_code` (e.g. `"eng"`, or leave it unset to auto-detect), `tag_audio_events`, `diarize`, `num_speakers`, `timestamps_granularity`, `keyterms: list[str]`, `file_format` (`"pcm_s16le_16"` or `"other"`).
- **Also available:** `source_url` (`cloud_storage_url` is deprecated), `webhook`, `temperature`, `seed`, `use_multi_channel`, `no_verbatim`, `entity_detection`, `entity_redaction`, `enable_logging`, `request_options`.
- **`file` type:** `core.File`, which is one of:
  - `IO[bytes] | bytes | str`
  - a tuple `(filename, content)`
  - a tuple `(filename, content, content_type)`
  - a tuple `(filename, content, content_type, headers)`

**Model ids** (models page):

| Model | Status |
|---|---|
| `scribe_v3` | Current; the most accurate model for recorded audio |
| `scribe_v3_live` | Current; real-time |
| `scribe_v2_medical` | Current; clinical audio |
| `scribe_v2` | Previous generation, still available |
| `scribe_v2_realtime` | Previous generation |
| `scribe_v1` | Deprecated |

- The STT quickstart uses `model_id="scribe_v3"`.
- The SDK docstring example still shows `scribe_v2`. That is only an example and is not a problem.

**Formats and limits** (STT capability page):
- "All major audio and video formats" are supported. The audio list explicitly includes **`audio/webm`** and **`audio/opus`**, and the video list includes `video/webm`.
- Files can be up to 5 GB and up to 15 hours long. The minimum length is 100 ms.

**Browser MediaRecorder (`audio/webm;codecs=opus`).** Yes, webm/opus is a listed format, so no ffmpeg step should be needed.
- Pass it with a filename and content type, and leave `file_format` at its default (`other`).
- That I tested it live is **[UNVERIFIED]**. I did not run a call. A 10-second check in Spike B settles it.
- Safari's MediaRecorder usually produces `audio/mp4` instead. That is also a "major format", but this is **[UNVERIFIED]** for Safari specifically.

Sketch for `pg/voice.py`, inside a FastAPI route that receives an `UploadFile`:
```python
from elevenlabs.client import ElevenLabs
client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
data = await upload.read()                       # bytes from MediaRecorder
audio_sha256 = hashlib.sha256(data).hexdigest()
res = client.speech_to_text.convert(
    model_id="scribe_v3",                        # fall back to "scribe_v2" on error
    file=("attestation.webm", data, upload.content_type or "audio/webm"),
    language_code="eng",
    tag_audio_events=False,
)
transcript = res.text   # the response has .text and .language_code; exact union shape [UNVERIFIED]
```

The SDK call is synchronous. In an `async def` route, run it with `await asyncio.to_thread(...)` or define the route as plain `def`.

### 2. Text-to-speech for the video voiceover

Signature, from the SDK source: `client.text_to_speech.convert(voice_id, *, text, model_id=..., output_format=..., voice_settings=..., language_code=..., seed=..., previous_text=..., next_text=..., ...) -> Iterator[bytes]`.

- **Models.** The quickstart uses `eleven_v4`, described on the models page as "state of the art". `eleven_multilingual_v2` is "previous generation", but the page still recommends it for long-form content where stability matters. Avoid `eleven_turbo_*`, which is deprecated.
- **Voice.** The quickstart's voice is **George**, `voice_id="JBFqnCBsd6RMkjVDRZzb"`. It is the only voice id I could confirm from the docs. That George reads as a calm narrator is my opinion **[UNVERIFIED]**. For something calmer, browse the Voice Library, filter for "narration", and copy the voice id.
- **For calm, even delivery,** set `voice_settings` with a higher `stability` and a low `style`. The fields are `stability`, `similarity_boost`, `style`, `use_speaker_boost` and `speed`. Values such as stability 0.6-0.75 and style 0.0-0.2 are a suggestion **[UNVERIFIED]**: tune them by ear.
- **MP3 output.** `output_format="mp3_44100_128"` is the API default. The other mp3 values are `mp3_22050_32`, `mp3_24000_48`, `mp3_44100_32/64/96` and `mp3_44100_192`. 192 kbps needs Creator tier or higher, which the hackathon coupon gives. 128 kbps is fine for the video.

```python
from elevenlabs.client import ElevenLabs
from elevenlabs import save            # also exported: play, stream
from elevenlabs import VoiceSettings   # import path per SDK convention [UNVERIFIED]
client = ElevenLabs()                  # reads ELEVENLABS_API_KEY
audio = client.text_to_speech.convert(
    "JBFqnCBsd6RMkjVDRZzb",            # George
    text="ProofGate stops an AI claims agent from denying anyone without a human who actually checked.",
    model_id="eleven_v4",              # or "eleven_multilingual_v2" for steadier long-form
    output_format="mp3_44100_128",
    voice_settings=VoiceSettings(stability=0.7, similarity_boost=0.75, style=0.1),
)
save(audio, "voiceover.mp3")           # or: open(...,"wb").write(b"".join(audio))
```

Tip: generate the script one paragraph at a time and pass `previous_text`/`next_text`, so the joins between paragraphs sound natural.

### 3. "Best Project Built with ElevenLabs" prize criteria

- **No published criteria found.**
- `Resources.md` gives only the prize: "3 months of ElevenLabs Scale Tier". (The 1st-place prize separately includes 3 months of Pro Tier.)
- I was able to read the ElevenLabs Hacker Guide (the Google Doc, via its text export). It contains:
  - a product list: speech, transcription, music, sound effects, dubbing, voices, agents;
  - the Creator-plan coupon;
  - a swag and showcase submission flow: fork the showcase repo, add an MDX file, open a PR, fill in a form;
  - a "Best projects of 2025" showcase;
  - a feedback form that makes you eligible for swag (https://forms.gle/gHs8mGFGSPt6Hrco9);
  - support in the `#hackathon-support` Discord channel.
- **The guide has no judging criteria and does not mention this prize by name.**
- A web search for the Toronto event with an ElevenLabs prize found nothing more.
- Inference, not a published rule **[UNVERIFIED]**: judges will probably reward a use of ElevenLabs that is load-bearing in the product. Spoken attestation fits that better than a voiceover alone. Ask the ElevenLabs staff on site or in Discord.

---

## LangSmith

The Python SDK on PyPI is now **0.14.17**.

### 4. Redaction and metadata with `@traceable`

There are three documented layers:

1. **Hide everything (environment variables):** `LANGSMITH_HIDE_INPUTS=true`, `LANGSMITH_HIDE_OUTPUTS=true`.
2. **Client-level:** `Client(hide_inputs=lambda inputs: {...}, hide_outputs=lambda outputs: {...})`, passed per call with `langsmith_extra={"client": c}` or as `@traceable(client=c)`.
   - There is also `Client(anonymizer=create_anonymizer(...))`. It takes precedence over `hide_*`.
3. **Per function (the one we want):**
   ```python
   @traceable(name="execute_one", process_inputs=fn_in, process_outputs=fn_out)
   ```
   - `process_inputs(inputs: dict) -> dict` receives the arguments as a dict keyed by parameter name.
   - `process_outputs(output) -> dict` receives the raw return value.
   - Return new objects; do not mutate what you receive.
   - Function-level hooks override the client-level `hide_*` ones.
   - These hooks were added in SDK 0.1.98.
   - **The current source fails closed.** If `process_inputs` raises, the run is traced with a marker instead of the raw inputs, unless `LANGSMITH_ALLOW_UNPROCESSED_PAYLOADS` is set. Do not set that variable.

**Metadata and tags.** All three ways are documented:
- **On the decorator:** `@traceable(name=..., tags=["proofgate"], metadata={"component": "executor"})`.
- **At call time:** `fn(..., langsmith_extra={"metadata": {"case_id": ...}, "tags": ["deny"]})`.
- **Inside the function, after the value is known:**
  ```python
  rt = langsmith.get_current_run_tree()
  if rt:
      rt.metadata["decision"] = res["decision"]
      rt.tags.extend([...])
  ```
  Guard against `None` when tracing is off.
- `@traceable` also takes `enabled=` and `run_type=` (default `"chain"`).

### 5. Regions and public share links

**`LANGSMITH_ENDPOINT` values** (LangChain KB). Use no trailing slash.

| Region | `LANGSMITH_ENDPOINT` | UI |
|---|---|---|
| GCP US (default) | `https://api.smith.langchain.com` | smith.langchain.com |
| GCP EU | `https://eu.api.smith.langchain.com` | eu.smith.langchain.com |
| GCP APAC | `https://apac.api.smith.langchain.com` | apac.smith.langchain.com |
| AWS US | `https://aws.api.smith.langchain.com` | aws.smith.langchain.com |
| Azure US | not listed in the KB table **[UNVERIFIED]** | azure.smith.langchain.com |

- Keys are region-bound, and the SDK does not auto-detect the region.
- To find your region, look at the hostname of the UI you signed up on.
- Toronto sign-ups will usually land on US. If so, leave `LANGSMITH_ENDPOINT` unset.

**Public share link to one trace.**
- **UI steps:** open the trace, open the more menu at the top of the Details view, choose **Share**, and copy the public link.
- **Managing links:** Settings → Shared URLs lists shared traces and lets you unshare them.
- **SDK:** `Client.share_run(run_id)` returns the URL and still exists, but it is **deprecated** in favour of `client.runs.share.create(...)` (removal after Jan 31 2027). Related methods: `read_run_shared_link`, `run_is_shared`, `unshare_run`. Using the UI is simplest.
- **Plan restriction:** the docs do not mention one. Whether our plan allows sharing is **[UNVERIFIED]**: check that the Share button appears.
- **Caution:** a shared trace shows its full inputs and outputs, so redact before you share.

### 6. Does `pg/observability.py` already support this? Smallest change

**Current state.** `observability.traceable(name)` returns `langsmith.traceable(name=name)` if langsmith imports, otherwise a no-op.
- It accepts only `name`. There is no way to pass `process_inputs`/`process_outputs`, `metadata` or `tags`.
- It is not applied anywhere yet; the only `traceable` hit in `pg/` is its definition.
- With `LANGSMITH_TRACING` unset, langsmith's decorator just passes through, so "behaves the same when off" holds.

**Where the grant id leaks if we trace naively.** Grant ids look like `g_` + 32 hex characters.
- `gate.execute` output: `grant_id`.
- `target.apply` input: `grant_header="Grant g_..."`. Its output: `applied_by_grant`.
- `gate.confirm` output: `readback.grant_id`.
- `execute_one` output: it returns `res | {"confirm": ...}`, which carries both of the above.

**Proposed change (about 20 lines; described only, not made).**

1. **In `pg/observability.py`:**
   - Widen the wrapper to `traceable(name, **kw)` and forward `kw` to `langsmith.traceable(name=name, **kw)`. Callers can then pass `process_inputs`, `process_outputs`, `metadata` and `tags`, and the no-op fallback is unchanged.
   - Add one helper, `redact_grants(obj)`. It deep-copies dicts and lists. It replaces any value under the keys `grant_id` / `applied_by_grant` with `v[:6] + "…"`. It rewrites any string matching `Grant g_[0-9a-f]+` the same way.
   - Note that 6 characters of `g_xxxx…` is the `g_` prefix plus 4 hex characters.
   - Define `_red_in = lambda d: redact_grants(d)` and `_red_out = lambda o: redact_grants(o)`.
2. **In `pg/agent.py`** (Harry's file, so this is a handoff):
   - Decorate `triage` with `@obs.traceable("triage_one", process_outputs=obs.redact_grants)`. It has no grant, but this keeps it consistent. Its inputs are the case and clauses: fine for a demo tenant.
   - Decorate `execute_one` with `@obs.traceable("execute_one", process_inputs=..., process_outputs=...)`, both using `redact_grants`.
   - Inside `execute_one`, add a guarded `get_current_run_tree()` call that sets `metadata` `tenant_id`, `case_id`, `proposal_id` and `decision`. Alternatively, the loop can pass them via `langsmith_extra`.
3. **For the nested spans** (`gate_execute`, `target_apply`, `gate_confirm`):
   - Either decorate `gate.execute`, `target.apply` and `gate.confirm` with the same processors (other owners' files), or wrap them as three tiny local functions inside `agent.py` decorated with redaction. The local wrappers keep the change in one file.
   - **Every span that touches a grant needs both processors.** Redacting only the parent is not enough, because child runs are uploaded separately.
4. **Safety net:** wrap the metadata block in `try/except`. Keep `LANGSMITH_ALLOW_UNPROCESSED_PAYLOADS` unset so a redaction bug fails closed.
5. **Optional belt and braces:** set the client-level `hide_inputs`/`hide_outputs` to the same function, so any future `@traceable` that forgets the processors is still redacted. Function-level hooks take precedence where they are present.

---

## Sources opened

- https://elevenlabs.io/docs/api-reference/speech-to-text/convert
- https://elevenlabs.io/docs/capabilities/speech-to-text
- https://elevenlabs.io/docs/cookbooks/speech-to-text/quickstart
- https://elevenlabs.io/docs/overview/models
- https://elevenlabs.io/docs/api-reference/text-to-speech/convert
- https://elevenlabs.io/docs/quickstart
- https://pypi.org/project/elevenlabs/
- https://github.com/elevenlabs/elevenlabs-python: `src/elevenlabs/speech_to_text/client.py`, `text_to_speech/client.py`, `core/file.py`, `__init__.py`
- ElevenLabs Hacker Guide: https://docs.google.com/document/d/1mCh5MtOzBw0aJpurQVUmIVFfPMAHW3MjNemE-LNiMto (read via its text export)
- https://docs.langchain.com/langsmith/mask-inputs-outputs
- https://docs.langchain.com/langsmith/add-metadata-tags
- https://docs.langchain.com/langsmith/regions-faq
- https://kb.langchain.com/articles/6271700631-pointing-the-langsmith-sdk-and-cli-at-a-non-us-regional-endpoint
- https://docs.langchain.com/langsmith/share-trace
- https://github.com/langchain-ai/langsmith-sdk: `python/langsmith/run_helpers.py`, `client.py`; https://pypi.org/pypi/langsmith/json
