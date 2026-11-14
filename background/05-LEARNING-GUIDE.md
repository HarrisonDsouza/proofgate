# Beginner's Guide to Every Technology in This Hackathon

Written for someone who knows Java/Spring Boot, Angular/TypeScript and REST APIs, but is new to AI agents, MongoDB and voice. It is not tied to any one project. Read it top to bottom once, then use the glossary (Part 10) as a reference.

**How sure am I?** Every section carries one of these tags:
- **[Searched]**: I checked it by web search on Nov 13-14, 2026. Product details still change, so confirm in the official docs.
- **[General knowledge]**: from my training (before mid-2025 or so). Core concepts rarely change; product details can.
- **[Team notes]**: from the plan the team wrote earlier. I have not verified it.

---

## Part 0: The map

```
  PERSON  --types or speaks-->  FRONTEND (Angular / React / Next.js)
                                      |  REST, WebSocket
                                      v
                    BACKEND (Spring Boot and/or Python FastAPI)
                      |              |               |
                      v              v               v
                 AI MODELS       VOICE APIs       DATABASE
           (LLM, embeddings)    (ElevenLabs)   (MongoDB Atlas)
                      \_______________|_______________/
                                      |
                      LangSmith watches every AI call
```

Everything in this hackathon is one of those boxes. You already know the top two. The rest of this guide is the other four, plus the vocabulary that connects them.

---

## Part 1: The core problem the whole event is about

**Feel the problem.** Imagine a brilliant new employee who gets amnesia every time you hang up the phone. Each call, they know everything about the world but nothing about you, your company or the last call. To get useful work from them, you must read them a briefing at the start of every call.

That is how a large language model (LLM) behaves. [General knowledge] Each API call is a fresh start. The model remembers nothing between calls except what you put in the request.

From that, the hackathon's vocabulary falls out:

- **Context** = the text you hand the model on each call (instructions, history, retrieved facts).
- **Memory** = storing information *outside* the model (in a database) and choosing what to put back into the context next time.
- **Agent** = an LLM running in a loop where it can *act*: it asks to use tools (your functions or REST endpoints), sees the results, and decides the next step. Think of a Spring service orchestrator whose routing logic is written by an LLM instead of by you.
- **Guardrail** = a rule that limits what the agent may do, enforced somewhere the LLM cannot talk its way around.
- **"Agents in Context" theme** = agents that keep context *across sessions*, adapt their own guardrails, and keep working reliably under real load.

**The one design rule to remember: the LLM proposes, code decides.** An LLM is sometimes wrong, confidently. So anything that matters (can this payment go out, may this machine start) is decided by ordinary deterministic code and database state, and the LLM only helps with language. The judges returned to this rule constantly.

---

## Part 2: AI building blocks

### 2.1 LLM (large language model) [General knowledge]
A program that takes text in and predicts text out, one piece at a time. Claude, GPT and Gemini are LLMs. You call them over an HTTPS API, like any third-party REST service.
- **Token**: the unit models read and bill by, a word fragment. Roughly four characters of English, or three-quarters of a word. You pay per token in and out.
- **Prompt**: the text you send. A **system prompt** sets the role and rules; **user messages** carry the request.
- **Context window**: the maximum tokens the model can see in one call. Too small to hold everything you know, hence the need for memory and retrieval.
- **Non-determinism**: the same prompt can give different answers. A setting called *temperature* controls randomness, but even at zero you do not get a guarantee. Never build a safety property on the model being consistent.
- **Hallucination**: fluent, confident, wrong output.
- **Cost and keys**: you need an **API key** and a funded **API balance**. A chat subscription (such as a Claude Max plan) is billed separately and does not pay for API calls. [Team notes: check keys and credits before the event.]

### 2.2 Structured output and schema validation [General knowledge]
**Problem:** you ask the model to "extract the asset name and the hazard" and it replies with a friendly paragraph your code cannot parse.
**Idea:** give the model a JSON *schema* and require output in that shape, then validate it in code.
**Java analogy:** a DTO with Bean Validation (`@Valid`, `@NotNull`). In Python the library is **Pydantic**.
```python
from pydantic import BaseModel
from typing import Literal

class Claim(BaseModel):
    asset_ref: str
    claim_type: Literal["hazard", "release"]
    constraint: str
```
If the model's output does not fit, validation fails and you can retry or reject. Treat the failure as normal, not rare.

### 2.3 Tool use (function calling) [General knowledge]
**Problem:** a model can only produce text; it cannot check a database or send an email.
**Idea:** you describe your functions to the model (name, purpose, JSON schema for arguments). The model replies, "please call `get_route` with `{...}`". *Your code* runs it and sends the result back. The model never executes anything itself.
**Analogy:** the model is the person ordering at a restaurant; your code is the kitchen. A **tool** is usually just one of your REST endpoints with a description attached.
**Why it matters for safety:** the model can only *ask*. Your code decides whether to run it. That is where guardrails live.

### 2.4 Agent loop [General knowledge]
```
loop:
   model reads context -> asks for tool X  (or answers)
   your code runs X, checks it is allowed
   result goes back into the context
until the model gives a final answer or a limit is hit
```
Always cap the number of steps and tool calls; a stuck loop costs money.
- **Multi-agent**: several such loops that hand work or context to each other.
- **Human-in-the-loop**: the loop pauses for a person to approve a risky step.

### 2.5 Frameworks: LangChain and LangGraph [Searched / General knowledge]
Libraries that give you ready-made agent loops, memory hooks and tool wiring, so you do not write the loop by hand. **LangChain** is the general toolkit; **LangGraph** models an agent as a graph of steps with saved state. They are optional; many winning projects use a plain loop. MongoDB advertises a LangGraph integration, and its new Atlas Agent Engine supports LangGraph and Google's Agent Development Kit. [Searched]

### 2.6 MCP (Model Context Protocol) [General knowledge]
An open standard (introduced by Anthropic in late 2024) for plugging tools and data sources into models in a uniform way, a bit like USB for AI tools. You may see "MCP server" in docs. **This event recommends one:** the MongoDB MCP Server lets your AI coding assistant connect to your live Atlas database to inspect data and run queries (see Part 8).

### 2.7 Memory types [General knowledge]
Researchers split agent memory into kinds; the words show up in judging conversations:
- **Working memory**: what is in the current prompt.
- **Episodic memory**: records of past events ("on Tuesday the user rejected vendor X").
- **Semantic memory**: stable facts ("this user's preferred airport is YYZ").
- **Procedural memory**: how to do things (a checklist or workflow learned from before).

A hackathon warning from the research: a generic "chatbot with long-term memory" was the most common entry in past galleries and none placed. Memory only impresses when it *changes what the agent is allowed or able to do*.

### 2.8 Embeddings [General knowledge]
**Problem:** a user says "the east booster" but your database says "Pump A, P-101". Exact text matching fails, and no list of synonyms will cover everything people say.
**Idea:** an **embedding model** turns a piece of text into a long list of numbers (a *vector*, typically hundreds to a few thousand numbers) so that texts with similar *meaning* get similar numbers. Think of every phrase as a point on a huge map where related phrases sit close together.
**Example:** "east booster" and "pump on the east side" land close; "compressor 2" lands far away.
**Rules:** you must use the *same* embedding model for stored text and for the query, and the vector length must match your index setting.

### 2.9 Vector search [General knowledge / Searched]
Given a query vector, find the stored vectors nearest to it. "Nearest" is measured with a *similarity function*, commonly cosine similarity (the angle between the two vectors).
- **Exact (ENN)** search compares against everything: precise but slow at scale.
- **Approximate (ANN)** search uses a clever index to find *very probably* the nearest ones quickly. Atlas uses this by default. It can occasionally miss the true best match.
- The result carries a **score**. Your code can use the score (and the gap between the top two) to decide "I am sure" versus "this is ambiguous".

**Use it for:** fuzzy matching of names, finding similar past cases, excluding near-duplicates. **Do not use it for:** making safety decisions by itself.

### 2.10 Keyword search, BM25, hybrid search and reranking [Searched / Team notes]
- **Keyword (full-text) search** matches words. **BM25** is the standard scoring formula behind it: it rewards rare words that appear often in a document.
- Vector search is good at meaning; keyword search is good at exact IDs, codes and rare words ("permit 4471"). Real systems use both: **hybrid search**.
- To merge two ranked lists you need a rule. **Reciprocal Rank Fusion (RRF)** gives each result `1 / (60 + rank)` from each list and adds them up (optionally weighted). A result near the top of both lists wins. [Team notes for the formula]
- **Reranking**: a second, smarter model reorders the top results by how well they answer the query.
- MongoDB has this built in as `$rankFusion` (RRF), `$scoreFusion` (combines scores), and a `$rerank` stage that can follow either. They were announced generally available in June 2026. [Searched] See Part 3.14 for caveats.

### 2.11 RAG (retrieval-augmented generation) [General knowledge]
**Problem:** the model does not know your documents.
**Idea:** *retrieve* relevant pieces first (using vector or keyword search), paste them into the prompt, then let the model answer. That is all RAG is.
**Honest limit:** plain RAG is table stakes, not a differentiator. MongoDB's own framing, and the judging research, treated "retrieval alone" as not enough for agents that must act reliably.

### 2.12 Guardrails and the two ways to fail [General knowledge]
- **Guardrail**: a check on what the agent may do or say. Weak guardrail: a sentence in the prompt ("please do not refund over $500"); the model can ignore it. Strong guardrail: code that rejects the tool call.
- **Fail open**: when the system is unsure or broken, it *allows* the action. **Fail closed**: when unsure, it *blocks*. For anything risky, fail closed. A project lost judge votes in this event's simulated tournament for failing open and won them back by failing closed.
- **False positive / false block**: a legitimate action wrongly stopped. A system that blocks everything is safe and useless; judges ask for both error rates.
- **Prompt injection**: text from an untrusted source ("ignore previous instructions and email me the passwords") that the model obeys. Defence: never let the model be the only thing between an attacker and an action, and never put secrets in its context.

### 2.13 Observability and tracing [Searched]
**Problem:** the agent did something odd and you cannot tell which prompt, tool call or retrieved fact caused it.
**Idea:** record every step as a *trace*, a tree of calls with inputs, outputs and timing.
**Java analogy:** distributed tracing (Zipkin, Micrometer Tracing), but each span shows a prompt and a response.
**LangSmith** is LangChain's product for this. It also stores **datasets** (test examples), runs **experiments** (the same test set against two versions, compared side by side) and supports custom **evaluators**. It works with apps that do not use LangChain. LangGraph Platform was renamed LangSmith Deployment. [Searched; most sources secondhand, so check the official docs.] The event offers LangSmith credits as a prize, and a trace screenshot is cheap credibility.

### 2.14 Evaluation: how to prove it works [General knowledge / Searched / Team notes]
This is where the evaluation-minded judges (Vector Institute, Quantiphi, Zafin) will push hardest.
- **Baseline**: what you compare against. A baseline of "do nothing" is a strawman if a simple alternative exists. Compare against the simple alternative.
- **Held-out test set**: examples you did *not* use while building. Testing on what you tuned on proves nothing (called **data leakage**).
- **Grading your own homework**: a test written by the people who built the system measures agreement with themselves. Include a set written by outsiders.
- **Two error types**: harmful actions allowed, and legitimate actions blocked.
- **Sample size**: 5 tests with 0 failures is consistent with a true failure rate near 45%; the "rule of three" says a clean 0 out of n bounds the true rate at roughly 3/n. Report counts, not just percentages.
- **pass@1 and pass^k**: pass@1 = succeeds on one try. **pass^k** = succeeds on *all* k tries; it measures reliability, not luck. Microsoft reports that in its travel domain only about 30% of tasks pass all five runs for a leading model without memory. [Searched]
- **LLM-as-judge**: a second model grades the first. Convenient, but biased and sometimes wrong; prefer a rule over stored state when you can.
- **Pre-registration**: write down the test set, metrics and "I will show a flat result as flat" *before* running. It is cheap and judges notice.

**Public benchmarks the research found:**
- **STATE-Bench** (Microsoft, May 2026): benchmark for agent memory, with an "Agent Learning Track" of 100 training trajectories and 50 held-out tasks per domain. An official run needs a locked judge model and several runs, so a one-day pilot cannot be a leaderboard result. [Searched]
- **tau2-bench** (Sierra): tool-using customer-service tasks (airline, retail, telecom); installs with `uv sync`. Use the maintained tau2 repo, not the older tau-bench. [Searched]
- **LongMemEval** and **MemoryArena**: academic long-memory benchmarks, heavy for a day. [Team notes]

---

## Part 3: MongoDB from zero

### 3.1 Why databases at all, and how MongoDB differs [General knowledge]
A database stores data so it survives restarts and can be searched fast. You know relational databases: tables, rows, fixed columns, joins, migrations. **MongoDB** is a *document* database: instead of rows it stores JSON-like **documents**, and documents in one collection need not have the same fields.
```json
{ "_id": "P-101", "name": "Pump A", "aliases": ["east booster"],
  "areaId": "AREA-EAST", "ancestors": ["AREA-EAST"], "lockSeq": 0 }
```
Why that suits agents: records are nested and irregular (a conversation, a claim with attached evidence), and you can add a field today without a migration.

| Relational / JPA | MongoDB |
|---|---|
| Database | Database |
| Table | **Collection** |
| Row | **Document** |
| Column | Field |
| Primary key | `_id` (auto-created) |
| Foreign key + JOIN | Embed the child inside the parent, or use `$lookup` |
| Schema migration | Optional validation rules |

Documents are stored as **BSON**, a binary JSON that adds types such as dates, `ObjectId` and 64-bit integers.

### 3.2 Atlas, clusters, projects [General knowledge]
**MongoDB Atlas** is MongoDB run for you in the cloud, comparable to RDS for relational databases. The nesting is **Organization > Project > Cluster**. A **cluster** is a set of servers holding your data, normally a **replica set**: three copies of the data, one *primary* taking writes and two *secondaries* following it. That detail matters, because transactions and change streams both need a replica set (Atlas always gives you one).

**This event:** you were invited to an Atlas organization named "Agents in Context Toronto". To be eligible as a finalist, your project must be built inside the sandbox project there. [Organizer email, Nov 13]

**First-time pitfalls [General knowledge]:**
1. Atlas blocks all connections until you add your IP address to the **Network Access** list.
2. You connect as a **database user** you create (not your Atlas login).
3. The **connection string** (`mongodb+srv://user:password@cluster...`) contains a password. Keep it in an environment variable and never commit it to Git.

**Tools:** the Atlas web **Data Explorer**; **mongosh** (command-line shell); **Compass** (desktop GUI); and **drivers** for code: **PyMongo** (Python), the Java driver or **Spring Data MongoDB**, and the Node driver.

**Free-tier facts [Searched, partly unverified]:** free clusters were formerly "M0"; they have a rate limit of 100 operations per second, a roughly 512 MB data cap, may be paused when idle, and Vector Search works on them according to MongoDB staff. The sandbox's tier is unknown; look at it when you create the cluster.

### 3.3 CRUD [General knowledge]
```js
db.assets.insertOne({ _id: "P-101", name: "Pump A", areaId: "AREA-EAST" })
db.assets.find({ areaId: "AREA-EAST" })                  // read
db.assets.updateOne({ _id: "P-101" }, { $set: { lockSeq: 1 } })
db.assets.deleteOne({ _id: "P-101" })
```
Operators start with `$`: `$gt`, `$in`, `$and`, `$set`, `$inc`. A query is itself a JSON document.

### 3.4 Aggregation pipeline [General knowledge]
Think of Java Streams: data flows through stages.
```js
db.decisions.aggregate([
  { $match: { outcome: "BLOCKED" } },
  { $group: { _id: "$assetId", blocks: { $sum: 1 } } },
  { $sort: { blocks: -1 } }
])
```
Common stages: `$match` (filter), `$group`, `$project` (shape output), `$lookup` (a join), `$sort`, `$limit`. Nearly every special feature below (vector search, graph walks, geo queries, hybrid search) is "just another stage" in this pipeline.

### 3.5 Indexes and the explain plan [General knowledge]
**Problem:** with a million documents, "find all locks on pump A" reads every document to answer.
**Idea:** an **index** is a sorted lookup structure, like the index at the back of a textbook: go straight to the page.
- **Compound index** `{assetId: 1, state: 1}`: supports queries on `assetId` alone or both fields; field *order* matters.
- **Multikey index**: if the indexed field is an array, MongoDB indexes each element. This is how "which riders' routes include station X" becomes fast.
- **Unique index**: rejects duplicates. A cheap way to make an operation idempotent (Part 6).
- **TTL index**: deletes documents automatically after a set time. Handy for anything that should expire.
- **Cost:** every index slows writes slightly and uses memory. Index what you query.

**Explain plan** (SQL's `EXPLAIN`): ask the database how it answered.
```js
db.guardrails.find({ assetId: { $in: ["P-101","AREA-EAST"] }, state: "LOCKED" })
  .explain("executionStats")
```
Look for `IXSCAN` (used an index, good) versus `COLLSCAN` (scanned everything, bad), and compare `totalKeysExamined` and `totalDocsExamined` with `nReturned`. Close numbers mean an efficient query. MongoDB judges asked for this on screen on every project.

### 3.6 Transactions [General knowledge]
Any *single* document write is already atomic. A **multi-document transaction** makes several writes (possibly in different collections) succeed or fail together, the equivalent of `@Transactional`.
```python
with client.start_session() as session:
    with session.start_transaction():
        facts.update_one({"_id": fid}, {"$set": {"burned": True}}, session=session)
        decisions.insert_one({"fact": fid, "outcome": "refused"}, session=session)
```
**When you need one:** a *check-then-act* race. Process A checks "is it safe?" and says yes; process B writes a lock a millisecond later; A proceeds. Doing check and write in one transaction, with writes that touch the same document, makes one side fail and retry instead of both succeeding.
**Practical notes:** keep them short; handle a transient "write conflict" by retrying; in Spring you need the `MongoTransactionManager` bean configured before `@Transactional` does anything. Transactions need a replica set (Atlas is one). Whether the sandbox tier has any transaction limits is unverified.

### 3.7 Change streams [General knowledge]
**Problem:** "do something the moment this document changes" without polling the database every second.
**Idea:** open a **change stream** on a collection or database and the server *pushes* you each insert, update or delete as an event.
**Analogy:** Postgres `LISTEN/NOTIFY`, or reading a Kafka topic fed by change-data-capture.
```python
pipeline = [{"$match": {"operationType": "update",
                        "updateDescription.updatedFields.status": "closed"}}]
with db.permits.watch(pipeline, full_document="updateLookup") as stream:
    for change in stream:
        handle(change)
        save_token(stream.resume_token)      # remember where we are
```
- The `$match` runs *on the server*, so you only receive events you care about.
- **Resume token**: a bookmark for the stream, like a Kafka offset. Save it after each processed event; after a crash, reopen the stream with `resume_after=token` and you replay what you missed instead of silently dropping it. Judges asked for this on every project that used change streams.
- Delivery can repeat after a restart, so the handler must be safe to run twice (idempotent).

### 3.8 Time-series collections [General knowledge]
A collection type optimised for readings that arrive with timestamps: sensor values, status events, logs.
```js
db.createCollection("readings", { timeseries: { timeField: "ts", metaField: "meta" } })
```
`ts` is the timestamp; `meta` describes the source (which sensor). Storage is compact and range queries ("last hour of readings for sensor X") are fast.

### 3.9 `$graphLookup` [General knowledge]
A pipeline stage that follows links recursively, to walk a graph or a hierarchy (stations connected to stations, a category tree). `restrictSearchWithMatch` limits which nodes the walk may pass through, so a path through a "bad" node is impossible. Honest note: for a few dozen nodes, an in-memory algorithm does the same job; the argument for the database is that the data already lives there.

### 3.10 Geospatial queries [General knowledge]
Store a location as GeoJSON, `{type: "Point", coordinates: [longitude, latitude]}` (**longitude first**, a classic bug). Add a `2dsphere` index, then `$geoNear` (it must be the first stage) returns the nearest documents with distances.

### 3.11 Atlas Search (full-text) [General knowledge]
Keyword search inside Atlas, built on Apache Lucene, scored with BM25. You define a *search index* in Atlas and query it with the `$search` stage. This is a separate index from ordinary indexes.

### 3.12 Atlas Vector Search [Searched]
Vector search stored beside your documents. Two steps:

**1. Create a vector index** (in the Atlas UI or API). The vector length must equal your embedding model's output size, and any field you want to filter on must be declared:
```json
{ "fields": [
  { "type": "vector", "path": "embedding", "numDimensions": 1024, "similarity": "cosine" },
  { "type": "filter", "path": "areaId" }
]}
```

**2. Query with the `$vectorSearch` stage:**
```js
db.assets.aggregate([
  { $vectorSearch: {
      index: "assets_vector_index",
      path: "embedding",
      queryVector: [/* the embedding of "east booster" */],
      numCandidates: 200,
      limit: 5,
      filter: { areaId: "AREA-EAST" } } },
  { $project: { name: 1, score: { $meta: "vectorSearchScore" } } }
])
```
Rules from MongoDB's documentation:
- `limit` cannot exceed `numCandidates`. `numCandidates` is how many nearest-neighbour candidates are examined before returning the best `limit`; the docs suggest at least about 20 times `limit` for better accuracy. (Larger is slower but more accurate.)
- `filter` is applied *during* the search and only works on fields you declared as filter fields, with simple types and operators. An unsupported operator makes the stage fail.
- An `exact: true` option does exact search and does not use `numCandidates`.
- The English stage-reference page is the one to trust; some details above came from localised copies.

### 3.13 Voyage AI and automated embedding [Searched]
**Voyage AI** makes embedding and reranking models; MongoDB acquired it and now offers them inside Atlas. The Voyage 4 family (voyage-4-large, voyage-4, voyage-4-lite) and code models were announced in 2026. **Automated embedding** means you choose a Voyage model when defining a vector index and Atlas creates and refreshes the embeddings itself whenever the indexed field changes, so you do not call an embedding API from your code. MongoDB's pages say it reached general availability in August 2026; I found no independent confirmation, and availability and pricing may vary by region and tier. Voyage models are also available through a standalone API. **Voyage AI is a partner at this event:** every participant gets 200 million free tokens (create an account at dashboard.voyageai.com, generate an API key and save it immediately, and add a payment method to unlock normal rate limits; you are not charged within the allowance). The Voyage team is on site. [Official resource guide]

### 3.14 Hybrid search stages [Searched]
`$rankFusion` merges ranked results from several pipelines (for example one `$vectorSearch` and one `$search`) with RRF. `$scoreFusion` merges using their scores, with weights. `$rerank` can reorder afterwards. Limits: all sub-pipelines must use the same collection, and the stages do not support pagination. Version requirements conflict across MongoDB's pages (`$rankFusion` from 8.0; `$scoreFusion` from 8.2 or 8.3), so check your cluster version first.

### 3.15 Atlas Agent Engine [Searched]
MongoDB's own product for running agents, launched in public preview on Sept 29, 2026 alongside MongoDB 9.0. It runs agents written with the LangGraph SDKs or Google's Agent Development Kit, keeps their state, offers memory and long-term retrieval (powered by Voyage AI), and adds governance. Its **Policy Engine** currently enforces *fixed* rules: a **tool allowlist** (a call to a tool not on the list halts the run) and **execution budgets** (such as a maximum number of tool calls). It routes calls through wrapper functions, `app.tool(...)` and `app.llm(...)`, that also give audit logging. Policy changes do not affect runs already in progress. **Why you should know it:** MongoDB judges will ask what your project adds beyond it. The honest gap: nothing in it *learns* a rule from what happened or *changes* policy from conversations. [Memory prerequisites such as cluster tier or a Voyage key are unconfirmed.]

### 3.16 Users, roles and access control [General knowledge]
Atlas has **database users** with **roles** (read, readWrite, or custom roles with specific privileges). Privileges apply to a *collection*, not to a single field, so to hide one field from one service you move it into a different collection and grant access to that collection only. Whether the event sandbox lets you create custom roles is unverified.

### 3.17 Schema validation [General knowledge]
You can attach a `$jsonSchema` validator to a collection so MongoDB rejects documents of the wrong shape. "Flexible schema" does not mean "no schema"; judges disliked "a dumb JSON bucket" with no indexes or structure.

---

## Part 4: Voice

### 4.1 Speech-to-text (STT) and text-to-speech (TTS) [General knowledge]
- **STT** (also ASR): audio in, text out. **Batch** transcribes a finished recording; **streaming** returns words as you speak (lower delay, slightly less accurate). Weak spots: numbers, names, tag codes and noisy rooms. This is why serious voice systems **read back** what they heard and ask for confirmation.
- **TTS**: text in, audio out. Good TTS is fast enough to stream as it is generated.
- **Voice agent** = STT, then an LLM, then TTS, in a loop. Two hard problems: **latency** (a pause over about a second feels broken) and **turn-taking** (knowing when the person has finished, and handling **barge-in**, when they interrupt).

### 4.2 ElevenLabs [Searched; sources partly secondhand, so check the docs]
One company, one API key, several products:
- **Text to speech**: many voices and languages; supports streaming.
- **Speech to text, "Scribe"**: Scribe v2 for batch transcription in 90+ languages with timestamps and speaker labels; a realtime variant with roughly 150 ms latency.
- **Agents platform** (formerly "Conversational AI"): hosted voice agents that combine STT, an LLM, TTS and a turn-taking model, which can call your tools.
- **Voice cloning**: copy a voice from a short sample.
- Billing is by credits. The hackathon offers ElevenLabs prizes, including one for the best project built with it.

### 4.3 Voice cloning and deepfakes [General knowledge]
A convincing clone needs only seconds to minutes of audio, so *sounding like someone is no longer evidence of being them*. Rules: only clone a person who has consented (a teammate's own voice), say so on stage, and never treat voice as identity (use a login).

### 4.4 Practical voice pitfalls [General knowledge]
- Browsers only allow microphone access on HTTPS or `localhost`, and ask permission.
- Build a typed fallback and the in-browser voice path *first*; real phone calls need a separate telephony provider and are the likeliest thing to fail on venue Wi-Fi. (I did not research telephony providers.)
- Test on the venue microphone; use a headset.

---

## Part 5: The application stack

### 5.1 Web basics you already know, in one paragraph [General knowledge]
REST over HTTP with JSON bodies; verbs and status codes. Two extras: **WebSocket** (a persistent two-way connection) and **Server-Sent Events** (the server streams events to the browser). These are how a database change reaches a live screen: change stream, backend, push to browser.

### 5.2 Spring Boot (Java) [General knowledge]
Use **Spring Data MongoDB**: `MongoRepository` for simple CRUD, `MongoTemplate` for aggregation pipelines, and a `MongoTransactionManager` bean to make `@Transactional` work. Good for deterministic rule services, indexes, state machines and APIs.

### 5.3 Python, FastAPI, Pydantic, PyMongo [General knowledge]
Most AI libraries and examples are Python, so the AI side is usually Python. **FastAPI** is a small web framework (roughly Spring MVC for Python) that generates interactive API docs at `/docs`. **Pydantic** validates data (Part 2.2). **PyMongo** is the MongoDB driver. Keep the synchronous driver for a one-day build.
Splitting languages (Python for AI, Java for rules) works but adds a service boundary. Whatever must sit in the same process as a benchmark or an agent loop should be in that language.

### 5.4 Angular, React, Next.js, Tailwind [General knowledge]
You know Angular. **React** is the other main UI library; **Next.js** is a framework on top of React; **Tailwind** is a utility-class CSS library. The team's earlier plan listed Next.js, but Angular is the better choice for people who already know it.

### 5.5 pytest and Git [General knowledge]
**pytest** is Python's unit-test tool. For three engineers in one day: one Git branch per person, small commits, and no risky merges in the last two hours.

### 5.6 Secrets and keys [General knowledge]
API keys (LLM, ElevenLabs, LangSmith, Atlas) are passwords with a billing account attached. Put them in environment variables or a `.env` file listed in `.gitignore`. A key pushed to a public repository is typically found and abused within minutes.

---

## Part 6: Security and reliability ideas the judges cared about

### 6.1 Identity and permissions [General knowledge]
- **Authentication**: proving who you are. **Authorization**: what you may do.
- **RBAC** (role-based access control): permissions attach to roles, people get roles.
- **Least privilege**: give each user or service only what it needs.
- **Service identity**: a non-human account for an agent. Good design: it can *request* actions but cannot *approve* them.
- **Voice is not identity**: identity comes from a login with a role.

### 6.2 Hashing and keyed hashes [General knowledge]
A **hash** turns data into a fixed-length fingerprint that cannot be reversed. Store the fingerprint of a secret instead of the secret and you can still check a guess by hashing it. An **HMAC** is a hash that also uses a secret key, so an attacker who steals the database but not the key cannot test guesses.

### 6.3 Step-up authentication, KBA, human approval, audit [General knowledge]
- **Knowledge-based authentication (KBA)**: proving identity by something you know ("your first pet"). Weak when the answer can be found elsewhere.
- **Step-up**: ask for stronger proof only when the action is risky.
- **Out-of-band approval**: confirm through a separate channel or device.
- **Human-in-the-loop** and an **audit log** (who did what, when, and what was checked) are what regulated industries ask for first.

### 6.4 Reliability vocabulary [General knowledge]
- **Race condition**: two things happen "at once" and the result depends on the order. The check-then-act example in 3.6.
- **Idempotent**: doing it twice has the same effect as once. A **unique index** on (event, user) makes "send this alert" safe to retry.
- **At-least-once delivery**: after a crash you may see an event again; design for it.
- **Retry with backoff**: retry after growing delays rather than hammering.
- **Rate limiting and queues**: stop one big event from creating thousands of simultaneous actions (a "call storm").
- **Fail open vs fail closed**: Part 2.12.

---

## Part 7: Public data and other pieces the research touched

| Item | What it is |
|---|---|
| Toronto Open Data / DineSafe | City-published restaurant inspection records. Field names must be checked from the actual file. [Team notes] |
| Public transit maps and status | Stations and lines can be typed in by hand; whether a live elevator feed exists is unconfirmed. |
| Ontario Food Premises Regulation | The source of fixed temperature limits; check the text before quoting numbers. [General knowledge, unverified] |
| Synthetic data | Data you invent. Always label it as synthetic on stage. |

---

## Part 8: Hackathon logistics tools

### 8.0 Tools the organizers recommend (official resource guide)
**Recommended sequence before building:** install MongoDB Agent Skills, connect the MongoDB MCP Server, then use the natural-language prompting guide.
- **MongoDB Agent Skills** (mongodb.com/docs/agent-skills): instructions you install into an AI coding assistant (Claude, Cursor, Copilot) so it follows MongoDB best practices for connecting, modelling data, writing queries and implementing search.
- **MongoDB MCP Server** (mongodb.com/docs/mcp-server/get-started): lets the coding assistant connect to your live database to inspect data, run queries, count documents and manage Atlas resources.
- **Natural Language to MongoDB Queries** (mongodb.com/docs/manual/natural-language-to-mongodb): how to prompt an assistant to write correct queries (describe the task, the data shape and the output you want).
- **Atlas Managed MCP Server**: a hosted version that uses Atlas service accounts instead of your personal credentials.
- **Sample Movie Dataset (sample_mflix)**: loads in minutes and is preconfigured for AI search; good for the vector search exercise in Part 11.
- **Embedding and Reranking API**: one endpoint for Voyage embeddings and reranking from any language.
- **Memory and state examples**: an agent with memory and function calling; memory for a chat app in Python or JavaScript with LangChain; **LangGraph with MongoDB checkpoints** (saves an agent's state per conversation thread so it can resume); a MongoDB blog post on state, persistence, suspend/resume and crash recovery; GraphRAG with LangChain.
- **Starter code**: the GenAI Showcase repository (many example apps), a Python quickstart notebook, and a MERN (MongoDB, Express, React, Node) starter.
- **LangChain**: $50 LangSmith credits plus Deployments access (redeem by form within 10 days; a card is needed to display the credits but is not charged), LangGraph docs and a "Deep Agents" quickstart.
- **ElevenLabs**: one month of the Creator plan (131k credits), redeemed in the ElevenLabs Discord `#coupon-codes` channel with your Cerebral Valley email, only if checked in by 11 AM.

### 8.0.1 The official rules that shape what you build
- Every project must fit one of **three problem statements**: Agents You Can Audit, Memory You Can Govern, Finish the Job. See `00-README-HANDOFF.md` §1.1.
- Build in the **Atlas Hackathon Sandbox**; all work original and built today; teams up to 4.
- Submit on the Cerebral Valley platform by **5:00 PM**: public GitHub repo, **1-minute video** with audio, short description, all teammates added. Live judging from 5:15 PM; top 6 on stage at 7:00 PM.


- **Cerebral Valley platform**: where the event page, approval status, resources and the project gallery live. Every teammate must be approved; approval also unlocks partner resources.
- **Luma**: the registration emails and tickets.
- **Discord**: where organizers post updates. Join it.
- **Atlas sandbox**: build inside it to be eligible as a finalist.
- **LangSmith and ElevenLabs credits**: partner prizes and resources; check the details page on the day.
- **Past galleries**: Cerebral Valley hosts a gallery page per event, which is how the research found past winners.

---

## Part 9: How this fits together, in one paragraph

A person speaks or types. The frontend sends it to your backend. A voice service (STT) turns audio to text. An LLM turns text into a structured request. Vector search (an embedding lookup in Atlas) maps loose phrases to the right records. Plain code reads MongoDB state through indexed queries, inside a transaction, and decides allow or block. Change streams notify other parts of the system when state changes. Voice (TTS) speaks the result. Every AI call is traced in LangSmith, and an evaluation script measures how often the system was right *and* how often it wrongly blocked. The LLM never makes the final call on anything risky.

---

## Part 10: Glossary (A-Z)

| Term | One-line meaning |
|---|---|
| Agent | An LLM in a loop that can call tools |
| Aggregation pipeline | MongoDB's staged data-processing query |
| ANN | Approximate nearest neighbour: fast, probably-closest vector search |
| API key | A secret that identifies and bills your app to a service |
| Atlas | MongoDB's hosted cloud service |
| Atlas Agent Engine | MongoDB's agent-running product (preview), with fixed policy rules |
| Audit log | Record of who did what and what was checked |
| Baseline | The simple alternative you compare against |
| Barge-in | A speaker interrupting a voice agent |
| BM25 | The standard keyword-relevance scoring formula |
| BSON | MongoDB's binary JSON format |
| Change stream | Server push of database changes |
| Cluster | A set of database servers holding your data |
| Collection | MongoDB's table-like group of documents |
| Compound index | An index over several fields |
| Context window | Max tokens a model can read in one call |
| Cosine similarity | Similarity measure based on the angle between vectors |
| Data leakage | Testing on data you also tuned on |
| Document | One JSON-like record |
| Embedding | A list of numbers capturing a text's meaning |
| ENN | Exact nearest neighbour search |
| Explain plan | The database's account of how it ran a query |
| Fail closed / open | Block / allow when unsure |
| False block | A legitimate action wrongly stopped |
| FastAPI | Python web framework |
| Guardrail | A limit on what an agent may do |
| Hallucination | Confident wrong model output |
| HMAC | A hash that uses a secret key |
| Human-in-the-loop | A person approves a step |
| Hybrid search | Vector plus keyword search, merged |
| Idempotent | Safe to do twice |
| Index | A lookup structure that speeds queries |
| KBA | Knowledge-based authentication |
| LangChain / LangGraph | Libraries for building LLM apps and agent graphs |
| LangSmith | Tracing and evaluation service for LLM apps |
| LLM | Large language model |
| LLM-as-judge | A model grading another model's output |
| MCP | A standard for connecting tools to models |
| Multikey index | An index over an array's elements |
| Non-deterministic | Same input, possibly different output |
| Out-of-band | Via a separate channel or device |
| pass@1 / pass^k | Succeeds once / succeeds on all k tries |
| Prompt | The text sent to a model |
| Prompt injection | Untrusted text that hijacks the model |
| Pydantic | Python data validation library |
| PyMongo | MongoDB driver for Python |
| RAG | Retrieve relevant text, then generate an answer |
| RBAC | Role-based access control |
| Replica set | Copies of the data across servers |
| Rerank | A second model reorders top results |
| Resume token | A bookmark for a change stream |
| RRF | Reciprocal Rank Fusion: merges ranked lists |
| Schema | The expected shape of data |
| Service identity | A non-human account |
| STT / TTS | Speech to text / text to speech |
| Time-series collection | Collection built for timestamped readings |
| Token | The unit models read and bill by |
| Tool use | The model asks your code to run a function |
| Transaction | Several writes that succeed or fail together |
| TTL index | Deletes documents automatically after a time |
| Vector | A list of numbers |
| Voyage AI | MongoDB's embedding and reranking models |
| WebSocket | A persistent two-way connection |

---

## Part 11: A learning path

**Do these six small exercises first (about 90 minutes in total).** Each is a "hello world" for one layer. If one stalls for 30 minutes, ask in the Discord; MongoDB staff are around.

1. **Atlas:** open the sandbox project, create a cluster, add your IP to Network Access, create a database user, connect with `mongosh` or Compass, insert a document, read it back.
2. **Indexes:** insert 10,000 dummy documents, run a query with `.explain("executionStats")` (you should see `COLLSCAN`), create an index, run it again (you should see `IXSCAN`).
3. **LLM + schema:** call an LLM API with a short prompt and make it return JSON that a Pydantic model accepts. Then deliberately give it a confusing input and watch validation fail.
4. **Vector search:** embed five short phrases, store the vectors, create the vector index, query with a paraphrase, and print the scores.
5. **Voice:** make ElevenLabs speak one sentence, and transcribe one recorded sentence, noting what it gets wrong.
6. **Tracing:** send one LLM call to LangSmith and open the trace.

**Self-test (explain each in two sentences, out loud):**
- Why does an LLM need memory outside itself?
- What is the difference between the model *asking* for a tool call and the tool *running*?
- Why use vector search for names but code for decisions?
- What does an explain plan show, and what do you want to see?
- When do you need a transaction, and what goes wrong without one?
- What is a resume token for?
- What is the difference between fail open and fail closed, and which do you pick for a risky action?
- Why is a test set you wrote yourself a weak proof?

**A fast way to learn:** when a coding assistant writes something, ask it to explain each file and each MongoDB query in plain language, and ask "what would break if I removed this line?" That tests your understanding as you go.

---

## Part 12: Sources

Searched on Nov 13-14, 2026; most are vendor pages, so verify against the official docs:
- MongoDB `$vectorSearch` stage: https://mongodb.com/ko-kr/docs/atlas/atlas-vector-search/vector-search-stage (localised copy; use the English page)
- Hybrid search GA: https://www.mongodb.com/products/updates/now-ga-hybrid-search-with-rankfusion-and-scorefusion/ and https://www.mongodb.com/docs/vector-search/hybrid-search/hybrid-search-overview/
- Automated embedding and Voyage 4: https://www.mongodb.com/products/updates/now-ga-automated-embedding-in-atlas-vector-search/ and https://www.mongodb.com/press/mongodb-sets-a-new-standard-for-retrieval-accuracy-with-voyage-4-models
- Atlas Agent Engine and Policy Engine: https://www.mongodb.com/docs/agentengine/manage/governance/policy-engine/ and https://www.mongodb.com/company/newsroom/press-releases/mongodb-launches-atlas-agent-engine-to-put-ai-agents-in-production-without-a-new-stack
- Atlas free cluster limits: https://mongodb.com/docs/atlas/reference/free-shared-limitations/
- ElevenLabs (secondhand reviews and changelog pages): https://elevenlabs.io/
- LangSmith (secondhand): https://langchain.com/resources/llm-observability-tools
- STATE-Bench: https://github.com/microsoft/STATE-Bench and https://opensource.microsoft.com/blog/2026/05/19/introducing-state-bench-a-benchmark-for-ai-agent-memory/
- tau2-bench: https://github.com/sierra-research/tau2-bench
