# Plan: a real agent built from the resource guide (draft for Harry's approval, 16:00)

Source: `[EXTERNAL] AGENTS IN CONTEXT TORONTO_ A MONGODB HACKATHON RESOURCE GUIDE.md`, read in full.

## 1. What the guide names

**Sponsors (prizes):** MongoDB, LangSmith (LangChain), ElevenLabs.
**Partner credits:** ElevenLabs (voice), LangChain (LangSmith credits, LangGraph, Deep Agents), Voyage AI (embeddings and rerankers, 200M free tokens).
**MongoDB resources:** Agent Skills, MCP Server, Natural Language to MongoDB Queries, Atlas Managed MCP Server, Frontier Marketplace Connectors, Sample Movie Dataset, Data Modeling, Vector Search, Atlas Search, Automated Embeddings, Embedding and Reranking API, "Building an Agent with Memory and Function Calling", LangChain memory (Python/JS), **LangGraph + MongoDB checkpointer**, State & Persistence blog, GraphRAG, GenAI Showcase, Python quickstart, MERN starter.
**Required:** Atlas Hackathon Sandbox, original work, public repo, 1-minute video with audio, all teammates on Cerebral Valley.

**Important fact:** none of the sponsors offers a text LLM. Voyage and the MongoDB Embedding API do embeddings and reranking only. LangChain is a framework and tracing service. ElevenLabs does voice. So "an LLM from a sponsor" is not possible. An LLM step needs a non-sponsor provider, or the decision has to come from Voyage models instead of an LLM. This is the decision Harry needs to make (section 4).

## 2. LangGraph history
LangGraph was never code in this repo. It shows up only in docs: a sample snippet in `docs/SETUP-RESEARCH.md` (commit b6c20dc) and the PRD's note about `langgraph-checkpoint-mongodb`. No branch has LangGraph code (harry, main, neil, sukhman). Nothing was lost. It is not installed.

## 3. Checklist: guide vs code today
| Guide item | Today | After this plan |
|---|---|---|
| Atlas Sandbox: collections, `$jsonSchema`, transactions, change streams | Yes (gate, detector) | Unchanged |
| LangGraph agent, MongoDB checkpointer | No | **Yes:** `pg/graph_agent.py`, `MongoDBSaver` checkpoints in Atlas |
| Function calling / agent takes actions | Fixed rule, no model | **Yes:** the graph reads the case, looks up clauses, then decides and writes a proposal |
| Vector Search | No | **Yes:** vector index on `policy_clauses`, `$vectorSearch` retrieval |
| Voyage AI embeddings and reranker | No (key not set) | **Yes:** `voyage-3.5` embeddings, `rerank-2.5` |
| LangSmith tracing | Decorator only, key not set | Traces each graph node (grant data never traced) |
| ElevenLabs | Code exists (`pg/voice.py`), key not set | Unchanged; needs key |
| MongoDB MCP Server, Agent Skills | Used in dev sessions, not in repo | List in README (dev tooling) |
| Anthropic triage agent (`pg/llm_agent.py`, added 15:52) | On harry / PR #13 | **Removed** (not a sponsor) |
| Gate, dwell, suspension | Unchanged | Unchanged: the agent only proposes |

## 4. The decision: where does the agent's judgment come from?
- **A. Sponsor-only (recommended).** A LangGraph graph whose decision comes from Voyage models plus Atlas Vector Search. It retrieves the relevant clauses with `$vectorSearch` and reranks them against the evidence with `rerank-2.5`. A decision node then scores whether the evidence meets each clause's conditions. That makes it a model-driven agent, but not a generative LLM: its rationale is built from the top clause and the evidence it relied on. Needs only `VOYAGE_API_KEY` (free).
- **B. A + a non-Anthropic LLM.** Same graph, but the decision node calls an LLM, such as Gemini or OpenAI through `langchain` chat models, using the retrieved clauses. It returns deny or pay, citations and a rationale through a tool call, and code validates the result. Needs that provider's key plus `VOYAGE_API_KEY`. Neither provider is a sponsor.
- Either way, if a key is missing or a call fails, the proposal is marked `proposer: rules-v1` and is visible as such. Nothing pretends to be a model.

## 5. Build steps (after approval)
1. Remove `pg/llm_agent.py` and its tests, route, button and the `anthropic` dependency.
2. Add `langgraph`, `langgraph-checkpoint-mongodb`, `voyageai` (and `langchain-google-genai` or `langchain-openai` for B).
3. `seed`: embed policy clauses with Voyage; `pg/db.py setup` creates the Vector Search index on `policy_clauses.embedding` (filter `tenant_id`).
4. `pg/graph_agent.py`: nodes `load_case` → `retrieve_clauses` ($vectorSearch) → `rerank` (Voyage) → `decide` (A: scores / B: LLM tool call) → `validate` (code: ids exist, hashes from the case, clause real) → `write_proposal`. Checkpointer: `MongoDBSaver` in Atlas, one thread per case, so a crash resumes mid-case.
5. Route `POST /api/agent/triage-new` and the Supervisor button use the graph. The seed and the pre-registered eval keep using the rule, so today's numbers stay valid.
6. Tests: graph runs with Voyage/LLM stubbed. Validation rejects invented evidence and clauses. A missing key falls back and is labelled. The checkpoint resumes. The existing 80 tests still pass. Lint and secret scan pass.
7. README: a "Guide resources used" checklist (section 3), plus keys and a demo command.

## 6. Time and risk (said plainly)
It is 16:00. The 1-minute video is not recorded yet. Submission is due at 17:00 and our target is 16:45. All 16 judge personas put the video and submission first. Building this is about 40-50 minutes for option A and 50-60 for B. Then it needs the keys, a reseed and a re-check, and the video would not show it.
**Recommendation:** Harry records the video and submits on the current build now. In parallel I build option A on `harry`. If it's tested by 16:40, it goes in the repo and in the table demo. If not, it stays off. Nothing merges to `main` without Harry.

## 7. Keys
Set: `MONGODB_URI`. Not set: `VOYAGE_API_KEY` (needed for A and B), `LANGSMITH_API_KEY`, `ELEVENLABS_API_KEY`, plus the LLM key for B (`GOOGLE_API_KEY` or `OPENAI_API_KEY`). `ANTHROPIC_API_KEY` is not set and won't be used.
