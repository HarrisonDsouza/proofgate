# LangSmith tracing: setup guide

**Owner:** Neil.
**Status:** guide only. Run it after the plan is approved.

## What it is, in plain words

LangSmith records each step our Python agent takes as a "trace". A trace is a timeline you can open in the browser:
1. triage the case
2. call the gate
3. call the claims system with the grant
4. confirm by read-back

It helps us debug, and it gives judges a second view of what the agent did.

**Important line for judges:** LangSmith is our *debugging* view. **MongoDB Atlas is the record of authority.** Approvals, gate decisions, grants and audit live in Atlas. The examiner page and rules R1-R8 read Atlas, not LangSmith. (This is PRD item C3, a COULD. It is fine because Neil does it in parallel.)

Our agent is rules-based (PRD M3) and has no LLM unless we build S6. Tracing still works: we trace our own Python functions.

## Steps

1. **Account.**
   - Sign up at LangSmith; the app is at smith.langchain.com [VERIFY current URL].
   - Note your region. If you are on the EU region, you also need `LANGSMITH_ENDPOINT`.
2. **API key.** Settings → API Keys → create one. It starts with `ls_`.
3. **Add to `.env`.** Never commit this file. Put no quotes or spaces around the values.
   ```
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=ls_...
   LANGSMITH_PROJECT=proofgate
   # LANGSMITH_ENDPOINT=...   only if not on the default US region (copy it from your settings page)
   # LANGSMITH_WORKSPACE_ID=... only if the key is org-scoped
   ```
4. **Install** in the shared Python virtual environment:
   ```bash
   pip install -U langsmith python-dotenv
   ```
5. **Hello trace** (a throwaway script; do not commit it):
   ```python
   from dotenv import load_dotenv; load_dotenv()   # must run before importing langsmith
   from langsmith import traceable

   @traceable(name="hello_proofgate")
   def hello(case_id: str) -> dict:
       return {"case_id": case_id, "ok": True}

   hello("CLM-A-0001")
   ```
   Run it, then open the `proofgate` project in LangSmith. One run should appear.
6. **Credits.** Submit the LangSmith Airtable form (link in `Resources.md`) with the hackathon name. You can do this after today; the window is 10 days.

## Wiring into the agent (handoff from Harry, after the agent code exists)

The agent lives in `pg/agent.py` (Harry), and `pg/observability.py` already has a LangSmith wrapper. Once the agent runs live, Neil adds tracing (through that wrapper):
- `@traceable(name="triage_one")` on the function that writes one proposal.
- `@traceable(name="execute_one")` on the function that handles one approved proposal. Nested calls go inside it:
  - `@traceable(name="gate_execute")` around the HTTP call to `POST /api/gate/execute`
  - `@traceable(name="target_apply")` around the call to the claims system
  - `@traceable(name="gate_confirm")` around the confirm call
- Tag each run with metadata such as `tenant_id`, `case_id`, `proposal_id` and `decision`, so a judge can search by case id.

**Do not leak credentials into traces.**
- The grant id is a 60-second, single-use bearer credential. Show only its first 6 characters in traces.
- Use a small wrapper, or `@traceable`'s input and output processing hooks if the researcher confirms they exist [VERIFY].
- Never trace `.env` values or the `AGENT_SERVICE_KEY`.

**Must not break the core.**
- If `LANGSMITH_TRACING` is false or unset, the code must behave exactly the same.
- If tracing breaks anything, set it to false. Do not debug it during the core build.

## Done when

- [ ] The hello trace is visible in the project.
- [ ] One honest denial shows a trace from triage → gate → apply → confirm, tagged with its case id.
- [ ] A burst shows refused `gate_execute` runs with reasons in their outputs.
- [ ] A public share link to one trace is saved for the README [VERIFY that sharing is available on our plan].
