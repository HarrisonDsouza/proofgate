# Setup research (verified by search, Nov 14 2026)

Collected by research agents before the build. Items they could not confirm are listed under 'Unverified' in each section. The PRD's Section 9 is built from this.

## How to install the MongoDB Agent Skills and the MongoDB MCP Server (local, plus the Atlas Managed/remote MCP server) in Claude Code: exact commands, config, read-only mode and gotchas
Steps:
Check prerequisites: Node.js v22.13.0 or later (run `node -v`; Node 20.x is deprecated) and Claude Code. You also need either a MongoDB connection string (Atlas or local) or an Atlas service account (client ID and secret).
PATH A, recommended for Atlas (skills + Atlas Managed MCP in one plugin). In a terminal, add the MongoDB marketplace: `claude plugin marketplace add https://github.com/mongodb/agent-skills.git`.
Inside Claude Code, run `/plugin` and select the official MongoDB plugin. The agent-skills README names it `mongodb-atlas` (`/plugin install mongodb-atlas`). For self-managed Community or Enterprise Advanced deployments, use the `mongodb` plugin instead (see README.community.md in the repo).
Run `/reload-plugins`, or restart Claude Code, so the skills and the MCP server load.
On first use of the mongodb-atlas plugin, sign in to MongoDB Atlas in the browser when prompted. This plugin connects to the MongoDB-hosted Atlas MCP server over HTTP with OAuth and needs no env vars.
PATH B, skills only (no MCP server): `npx skills add mongodb/agent-skills` (Vercel skills CLI). To add an MCP server afterwards, run the interactive setup: `npx -y mongodb-mcp-server@latest setup`.
PATH C, local stdio MCP server added manually to Claude Code. Register `npx -y mongodb-mcp-server@latest --readOnly` and pass the secret through env: `MDB_MCP_CONNECTION_STRING` for direct DB access, or `MDB_MCP_API_CLIENT_ID` + `MDB_MCP_API_CLIENT_SECRET` for Atlas admin tools (see the snippets).
For an Atlas service account: create it in Atlas with the least-privilege role (do NOT use Organization Owner), then add your machine's IP to the service account's API access list.
Enable read-only mode for the demo and judging: pass the `--readOnly` flag or set `MDB_MCP_READ_ONLY=true`. This allows only read, connect and metadata operations. To turn off specific tools or categories, use `MDB_MCP_DISABLED_TOOLS` (comma-separated) or `--disabledTools` (space-separated).
Verify: run `claude mcp list` (or `/mcp` inside Claude Code) and confirm the MongoDB server is connected. Then ask the agent to list databases or collections.
Snippets:
# Path A: official plugin (skills + Atlas-hosted MCP over OAuth)
claude plugin marketplace add https://github.com/mongodb/agent-skills.git
# then inside Claude Code:
/plugin            # choose the MongoDB plugin (mongodb-atlas for Atlas, mongodb for self-managed)
/reload-plugins
---
# Path B: skills only
npx skills add mongodb/agent-skills
# optional interactive MCP setup afterwards
npx -y mongodb-mcp-server@latest setup
---
# Path C: local MCP server with connection string, read-only (form from playbooks.com, adapted to the official package)
claude mcp add-json "MongoDB" '{"command":"npx","args":["-y","mongodb-mcp-server@latest","--readOnly"],"env":{"MDB_MCP_CONNECTION_STRING":"mongodb+srv://<user>:<pass>@<cluster>/<db>"}}'
---
# Path C variant: Atlas service account (Atlas admin tools), read-only
claude mcp add-json "MongoDB" '{"command":"npx","args":["-y","mongodb-mcp-server@latest","--readOnly"],"env":{"MDB_MCP_API_CLIENT_ID":"<client-id>","MDB_MCP_API_CLIENT_SECRET":"<client-secret>"}}'
---
# Generic mcpServers JSON (e.g. a project .mcp.json), per the official README pattern
{
  "mcpServers": {
    "MongoDB": {
      "command": "npx",
      "args": ["-y", "mongodb-mcp-server@latest", "--readOnly"],
      "env": { "MDB_MCP_CONNECTION_STRING": "mongodb+srv://..." }
    }
  }
}
Gotchas:
Node must be v22.13.0 or later. Node 20 is deprecated and may fail.
Put secrets (connection string, client secret) in env vars, not CLI args. Arguments show up in process lists.
Atlas admin tools only appear when API client credentials are set. A connection string alone gives database tools only.
Service account: grant minimum roles (Organization Owner is a security risk) and add your IP to the API access list, or Atlas API calls fail.
Remote/managed Atlas MCP server: you cannot authenticate with a static API key over HTTP. It uses OAuth with a browser sign-in. For headless or CI use with service-account credentials, the `mongodb-atlas-mcp-remote` stdio package exists.
Unattended agents: if no user can answer a confirmation prompt, the server treats it as a decline. The agent run may still exit 'successfully', so the failure is easy to miss.
HTTP transport (`MDB_MCP_TRANSPORT=http`) on a non-loopback host refuses to start unless `dangerousHostBinding` is enabled. It is off by default. Keep stdio for local Claude Code.
Disabled-tools lists: env var is comma-separated, CLI flag is space-separated.
Skills-only install (npx skills / copying skills/) does NOT configure any MCP server.
After installing a plugin, run `/reload-plugins` or restart, otherwise the skills don't load.
Third-party sites list conflicting plugin IDs (`mongodb@claude-plugins-official`, `mongodb-atlas@mongodb-plugins`). Pick from the `/plugin` menu rather than guessing the @marketplace suffix.
www.mongodb.com was unreachable from this sandbox (DNS blocked). Its docs pages were seen only through search summaries; the GitHub READMEs were fetched directly.
Sources: https://www.mongodb.com/docs/agent-skills/ https://www.mongodb.com/docs/claude/ https://www.mongodb.com/docs/mcp-server/get-started/ https://raw.githubusercontent.com/mongodb-js/mongodb-mcp-server/main/README.md https://raw.githubusercontent.com/mongodb/agent-skills/main/README.md https://mongodb.com/company/blog/product-release-announcements/introducing-mongodb-agent-skills https://playbooks.com/mcp/mongodb-js-mongodb https://codewithmukesh.com/blog/mongodb-agent-skills-dotnet/ https://claudeskills.info/plugins/mongodb/agent-skills/mongodb-atlas/
Unverified: I could not open www.mongodb.com from this sandbox (DNS blocked), so the official docs pages at /docs/agent-skills, /docs/claude and /docs/mcp-server/get-started were not read directly. What I have from them comes from search-result summaries.

Not confirmed:
(1) The exact @marketplace suffix for the plugin IDs. Third-party sites give `mongodb@claude-plugins-official` and `mongodb-atlas@mongodb-plugins`; the agent-skills README shows only `/plugin install mongodb-atlas`.
(2) Whether the official mongodb.com Claude Code page uses `claude mcp add` or `claude mcp add-json`. The add-json form comes from playbooks.com, a third-party site. `@latest` and `--readOnly` were added by analogy with the official README's npx config.
(3) The full list of individual skill names. Third-party marketplace URLs suggest mongodb-schema-design, mongodb-natural-language-querying, mongodb-search-and-ai, mongodb-atlas-stream-processing and others, but the official README describes the skills only by topic.
(4) Any separate 'Atlas Managed MCP Server' setup page beyond the fact that the mongodb-atlas plugin connects to the MongoDB-hosted server via OAuth.
(5) The `dangerousHostBinding` flag/env spelling and the exact usage of the `mongodb-atlas-mcp-remote` package.

To confirm, allow www.mongodb.com in the session network settings and re-fetch the three docs pages.

## Atlas Vector Search index + $vectorSearch, Atlas Automated Embedding (Voyage autoEmbed), Voyage AI Python client (voyage-4 / voyage-4-lite), and the MongoDB Embedding and Reranking API (setup as of Nov 2026)
Steps:
Create an Atlas project and cluster. The docs say Automated Embedding works on Free (M0), Flex and dedicated (M10+) clusters, so a hackathon team can start on M0. Add your IP to the Network Access list and create a database user. Copy the SRV connection string into the MONGODB_URI environment variable.
Install the drivers with `pip install pymongo voyageai`.
Choose an embedding path. (A) Automated Embedding: Atlas embeds a text field for you with a Voyage model. This is GA as of the 12 Aug 2026 MongoDB announcement, and you write no embedding code. (B) Manual: call Voyage (voyageai.Client) yourself, store the vectors in a field, and index that field with type 'vector'. Use B if you need full control or need numbers the model API does not give you.
For path A, create a search index of type 'vectorSearch' whose fields include {type:'autoEmbed', modality:'text', path:'<textField>', model:'voyage-4'}. Add {type:'filter', path:'<field>'} entries for every field you want to pre-filter on. You can mix autoEmbed fields and filter fields in one index. You cannot put a raw vector field on the same path as an autoEmbed field.
For path B, create a 'vectorSearch' index with {type:'vector', path:'embedding', numDimensions:1024, similarity:'cosine'} plus filter fields. numDimensions must match the output_dimension you embed with. The default for voyage-4 and voyage-4-lite is 1024. You can also use 2048, 512 or 256.
Create the index in the Atlas UI (Atlas Search / Vector Search tab, JSON editor) or from pymongo with SearchIndexModel(type='vectorSearch') and collection.create_search_index(). Wait until the index status is READY before you query it. Queries against an index that is still building return nothing.
Query with an aggregation whose first stage is $vectorSearch. On an autoEmbed index, pass query: {text: '...'} and Atlas embeds the query with the same model. On a vector index, pass queryVector, which you get by embedding the query yourself with input_type='query'. Set numCandidates to roughly 10-20x limit and add a filter on the indexed filter fields.
Get Voyage API keys. A model API key created in Atlas (under AI Models / Embedding and Reranking API) goes to https://ai.mongodb.com/v1. A key from the Voyage dashboard goes to https://api.voyageai.com/v1. Set VOYAGE_API_KEY and the Python client reads it automatically.
Optional rerank: after $vectorSearch returns its top-N, call the rerank endpoint (POST https://ai.mongodb.com/v1/rerank, or vo.rerank() in Python) on the candidate texts to reorder them.
Add a payment method on the platform that issued your key right away. Unpaid accounts get very low rate limits, and you will hit 429 errors as soon as you bulk-embed. If you use the autoEmbed path, check the Atlas query-time embedding rate limits as well.
Snippets:
# Automated Embedding index (path A), created via pymongo
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel
import os
coll = MongoClient(os.environ['MONGODB_URI'])['hack']['docs']
coll.create_search_index(SearchIndexModel(
    name='auto_idx', type='vectorSearch',
    definition={'fields': [
        {'type': 'autoEmbed', 'modality': 'text', 'path': 'description', 'model': 'voyage-4'},
        {'type': 'filter', 'path': 'category'}
    ]}))
---
# Query an autoEmbed index with raw text
results = coll.aggregate([
  {'$vectorSearch': {
     'index': 'auto_idx', 'path': 'description',
     'query': {'text': 'cheap vegan lunch near campus'},
     'numCandidates': 100, 'limit': 5,
     'filter': {'category': {'$eq': 'food'}}}},
  {'$project': {'description': 1, 'score': {'$meta': 'vectorSearchScore'}}}
])
---
# Manual-vector index (path B)
coll.create_search_index(SearchIndexModel(
    name='vec_idx', type='vectorSearch',
    definition={'fields': [
        {'type': 'vector', 'path': 'embedding', 'numDimensions': 1024, 'similarity': 'cosine'},
        {'type': 'filter', 'path': 'category'}
    ]}))
---
# Voyage Python client: embed docs + query, then rerank
import voyageai
vo = voyageai.Client()  # reads VOYAGE_API_KEY
docs = ['text one', 'text two']
d = vo.embed(docs, model='voyage-4-lite', input_type='document', output_dimension=1024).embeddings
q = vo.embed(['my question'], model='voyage-4-lite', input_type='query', output_dimension=1024).embeddings[0]
pipeline = [{'$vectorSearch': {'index': 'vec_idx', 'path': 'embedding', 'queryVector': q, 'numCandidates': 100, 'limit': 10}}]
# r = vo.rerank('my question', docs, model='rerank-2.5', top_k=3)  # rerank model name unverified
---
# MongoDB Embedding and Reranking API via curl (Atlas-issued model key)
curl https://ai.mongodb.com/v1/embeddings \
  -H "Authorization: Bearer $VOYAGE_API_KEY" -H 'Content-Type: application/json' \
  -d '{"input": ["hello world"], "model": "voyage-4"}'
Gotchas:
On an autoEmbed index, query with query.text, not queryVector. If the query text is longer than the model's context window, the $vectorSearch query fails.
You cannot mix autoEmbed and a raw 'vector' field on the same path. Filter fields are fine in the same index.
The model in the index (e.g. voyage-4) is used for both indexing and query embedding. Changing the model means rebuilding the index.
For manual vectors, numDimensions must exactly equal output_dimension (default 1024; voyage-4 and voyage-4-lite also accept 2048/512/256). Use input_type='document' when you index and input_type='query' when you search.
voyage-4-large, voyage-4 and voyage-4-lite share an embedding space (marketed as such), but the safe rule is to use the same model for documents and queries.
Key scope decides the host. Atlas-created keys go to ai.mongodb.com. Geography-scoped keys must use eu.ai.mongodb.com or us.ai.mongodb.com, and Atlas will not reroute them; scoped endpoints also have a 10% token uplift and lower rate limits. Voyage-dashboard keys go to api.voyageai.com.
The TypeScript Voyage client defaults to api.voyageai.com, so you must set its environment/baseURL to https://ai.mongodb.com/v1 to use Atlas keys. The docs contrast this with the Python client, which suggests Python handles Atlas keys differently.
The docs label the Embedding and Reranking API (ai.mongodb.com) as Preview and 'subject to change'. Automated Embedding is GA on Atlas. Self-managed mongot autoEmbed is still Preview.
Rate limits are per API key and measured in TPM and RPM. Going over returns HTTP 429, so batch and back off. Unpaid Voyage accounts are heavily throttled.
Indexes take time to build. Poll list_search_indexes() until status is READY before you demo.
voyage-code-4 needs an Atlas deployment; self-managed setups use voyage-code-3.
Sources: https://www.mongodb.com/products/updates/now-ga-automated-embedding-in-atlas-vector-search/ https://mongodb.com/docs/vector-search/crud-embeddings/automated-embedding/ https://www.mongodb.com/docs/vector-search/crud-embeddings/automated-embedding/models/ https://www.mongodb.com/docs/vector-search/indexes/vector-search-type.md https://www.mongodb.com/docs/search/self-managed/current/configuration/automated-embedding/ https://mongoosejs.com/docs/atlas-vector-search.html https://docs.voyageai.com/docs/api-key-and-installation https://docs.voyageai.com/docs/flexible-dimensions-and-quantization https://docs.voyageai.com/docs/rate-limits https://www.mongodb.com/docs/voyageai/api-and-clients/ https://www.mongodb.com/docs/api/doc/atlas-embedding-and-reranking-api https://www.mongodb.com/docs/api/doc/atlas-embedding-and-reranking-api/operation/operation-rerankdocuments https://www.mongodb.com/products/updates/now-in-public-preview-embedding-and-reranking-api-on-mongodb-atlas
Unverified: I could not open the source pages themselves: www.mongodb.com and docs.voyageai.com are outside this session's network allowlist, and they would need to be allowed to read the pages directly. Everything here comes from search-result summaries, which come from the official pages.

Not confirmed:
(1) The exact Voyage rate-limit numbers, for both paid and unpaid accounts. From memory: with no payment method, about 3 RPM and 10K TPM; on Tier 1 after adding a payment method, about 2000 RPM, with roughly 16M TPM for voyage-4-lite and 8M TPM for voyage-4. There is also a free-token allowance of around 200M tokens per model family. Check all of this on the Voyage dashboard.
(2) Whether the Python voyageai client automatically routes Atlas-issued keys to ai.mongodb.com, or needs a base_url setting.
(3) The current rerank model name: 'rerank-2.5' or 'rerank-2.5-lite' from memory; there may be a newer rerank-3.
(4) The optional autoEmbed fields numDimensions, similarity, quantization and indexingMethod. I only saw them in a Kubernetes or self-managed example, so I can't say whether Atlas accepts or needs them.
(5) Whether M0 has a lower cap on autoEmbed indexes or embedding tokens than paid tiers. One third-party site still called autoEmbed 'Preview'; the official GA announcement is dated 12 Aug 2026.
(6) Whether the mongodb.com docs paths now live under /docs/vector-search/ or /docs/atlas/atlas-vector-search/. Both appear in the results.
(7) The exact location of model API keys in the Atlas UI menu.

## Exact setup for (1) LangGraph with the MongoDB checkpointer for crash/resume, (2) ElevenLabs Python TTS/STT and the browser voice-agent option, (3) LangSmith tracing through environment variables. Researched 2026-11-14.
Steps:
LANGGRAPH + MONGODB: Use Python 3.11 or newer. langgraph-checkpoint-mongodb 0.5.1 (released Oct 8, 2026) requires Python >=3.11.
Install it: pip install -U langgraph langgraph-checkpoint-mongodb pymongo
Create a MongoDB Atlas cluster, or run a local mongod. Put the connection string in MONGODB_URI. Add your IP or 0.0.0.0/0 to the Atlas Network Access list for the hackathon.
Create one MongoClient per process and wrap it as MongoDBSaver(client, db_name=...). Or use the context manager MongoDBSaver.from_conn_string(MONGODB_URI, DB_NAME).
Compile the graph with builder.compile(checkpointer=checkpointer). Call it with config={'configurable': {'thread_id': '<stable id>'}}. Every super-step is saved to Mongo under that thread_id.
Crash/resume demo: kill the process mid-run, restart it, rebuild the same graph with the same checkpointer, and call it again with the same thread_id. Read state with graph.get_state(config). Re-invoke with None as the input to continue from the last checkpoint (see unverified).
ELEVENLABS: Install it with pip install elevenlabs (latest stable 2.78.0, Nov 12, 2026; a 3.0.0a1 pre-release also exists, so pin to 2.x). Set ELEVENLABS_API_KEY.
TTS: call client.text_to_speech.convert(text=..., voice_id=..., model_id=..., output_format='mp3_44100_128'). It returns an iterator of byte chunks: write them to a file, or play them with elevenlabs.play.play. For low latency use client.text_to_speech.stream(...).
STT (Scribe): call client.speech_to_text.convert(file=open('audio.mp3','rb'), model_id='scribe_v1') and add diarize=True for speaker labels. ElevenLabs docs say v2 Scribe models outclass scribe_v1, so try 'scribe_v2' first and fall back to 'scribe_v1'.
Voice-agent option: create an Agent in the ElevenLabs dashboard (Agents Platform / ElevenAgents) and copy its agent_id. For Python or desktop use, run elevenlabs.conversational_ai.conversation.Conversation with DefaultAudioInterface. For the browser, use the npm package @elevenlabs/react and its useConversation hook (the older @11labs packages are deprecated). For private agents, have your backend issue a signed URL so the API key never reaches the client. The Python SDK also has a 'Speech Engine' mode in which your server acts as a WebSocket endpoint (engine.serve(port=...)).
LANGSMITH: Install it with pip install -U langsmith.
Set LANGSMITH_TRACING=true and LANGSMITH_API_KEY=<key> (the key starts with ls_), plus optional LANGSMITH_PROJECT=<project-name>. Set LANGSMITH_ENDPOINT if your account is outside the default US region (e.g. EU). Org-scoped keys also need LANGSMITH_WORKSPACE_ID.
LangChain/LangGraph code is traced automatically once those environment variables are set; no code changes are needed. For plain Python functions such as the ElevenLabs calls or your own tools, add @traceable from langsmith. Nested traceable calls are linked into one trace automatically.
Load the environment variables before any imports run, e.g. with python-dotenv load_dotenv() at the top of main, so tracing is active from the start.
Snippets:
# --- LangGraph + MongoDB checkpointer (crash/resume) ---
import os
from typing import TypedDict
from pymongo import MongoClient
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.mongodb import MongoDBSaver

class State(TypedDict):
    step: int

def work(state: State):
    return {"step": state["step"] + 1}

client = MongoClient(os.environ["MONGODB_URI"])  # one client per process
checkpointer = MongoDBSaver(client, db_name="agent_state")

builder = StateGraph(State)
builder.add_node("work", work)
builder.add_edge(START, "work")
builder.add_edge("work", END)
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "job-42"}}
graph.invoke({"step": 0}, config)
print(graph.get_state(config).values)   # survives process restarts
# after a crash, same thread_id:  graph.invoke(None, config)  -> resumes from last checkpoint
---
# --- Context-manager form (from the PyPI README) ---
from langgraph.checkpoint.mongodb import MongoDBSaver
with MongoDBSaver.from_conn_string("mongodb://localhost:27017", "checkpoint_example") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    graph.invoke({"step": 0}, {"configurable": {"thread_id": "1"}})
# Async: README shows await checkpointer.aput/aget and `async for` over checkpointer.alist(...)
---
# --- ElevenLabs TTS + STT ---
import os
from elevenlabs import ElevenLabs
from elevenlabs.play import play

el = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

audio = el.text_to_speech.convert(
    text="The first move is what sets everything in motion.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_v3",            # or eleven_multilingual_v2
    output_format="mp3_44100_128",
)
with open("out.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
# play(audio)  # alternative (needs ffmpeg/mpv locally); don't consume the iterator twice

with open("audio.mp3", "rb") as f:
    tr = el.speech_to_text.convert(file=f, model_id="scribe_v1", diarize=True)  # try "scribe_v2"
print(tr.text)
---
# --- ElevenLabs realtime agent (Python, mic/speaker) ---
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

conversation = Conversation(
    client=el,
    agent_id=os.environ["ELEVENLABS_AGENT_ID"],
    requires_auth=True,
    audio_interface=DefaultAudioInterface(),
)
conversation.start_session()
# ... later
conversation.end_session()
---
// --- Browser voice agent (React) --- npm i @elevenlabs/react
import { useConversation } from '@elevenlabs/react';
const conversation = useConversation({ /* callbacks */ });
// public agent:  await conversation.startSession({ agentId: 'your-agent-id' })
// private agent: fetch signed URL from your backend, then startSession({ signedUrl })
// see unverified: exact method names differ between sources
---
# --- LangSmith tracing ---
# .env
# LANGSMITH_TRACING=true
# LANGSMITH_API_KEY=ls_...
# LANGSMITH_PROJECT=hackathon-agent
# LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com   # only if EU region (see unverified)

from dotenv import load_dotenv; load_dotenv()
from langsmith import traceable

@traceable(name="tts")
def speak(text: str) -> bytes:
    return b"".join(el.text_to_speech.convert(text=text, voice_id="JBFqnCBsd6RMkjVDRZzb", model_id="eleven_multilingual_v2", output_format="mp3_44100_128"))

@traceable(name="pipeline")
def pipeline(q: str):
    result = graph.invoke({"step": 0}, {"configurable": {"thread_id": "t1"}})  # LangGraph auto-traced, nests under pipeline
    return speak(str(result))
Gotchas:
langgraph-checkpoint-mongodb 0.5.x requires Python >=3.11, so a Python 3.10 environment fails to install it.
The Python MongoDBSaver takes a SYNC pymongo MongoClient. The TypeScript package (@langchain/langgraph-checkpoint-mongodb) is different: new MongoDBSaver({ client }) with an already-connected client. Don't mix the docs.
Resume only works if thread_id is stable and deterministic (e.g. a job or user id). A random uuid generated at each start means a fresh thread every time.
Known MongoDB issue INTPYTHON-728: custom keys in config['configurable'], other than thread_id, checkpoint_ns and checkpoint_id, are not persisted with recent LangGraph. Keep run metadata in the graph state instead.
Atlas: whitelist your IP (or 0.0.0.0/0 at the venue), and URL-encode special characters in the password inside MONGODB_URI.
Reuse one MongoClient per process. Don't create one per request.
ElevenLabs text_to_speech.convert returns a generator of bytes, not a bytes object. Join or iterate it once. elevenlabs.play needs ffmpeg/mpv installed locally.
Pin elevenlabs to 2.x: a 3.0.0a1 pre-release exists and could change the API surface.
Use @elevenlabs/react or @elevenlabs/client in the browser. The old @11labs/* packages are deprecated. Never ship ELEVENLABS_API_KEY to the browser: use a backend-issued signed URL for private agents.
Scribe v1 is described as outclassed by v2. Check which model id your account accepts and keep scribe_v1 as a fallback.
LangSmith: the old LANGCHAIN_TRACING_V2 / LANGCHAIN_API_KEY names still work, but use the LANGSMITH_* names. Non-US accounts must set LANGSMITH_ENDPOINT or they get auth failures. Keys start with ls_, so watch for stray spaces or quotes in .env. Org-scoped keys need LANGSMITH_WORKSPACE_ID.
Environment variables must be loaded before langsmith/langchain read them, so call load_dotenv() first.
Network note: docs.smith.langchain.com did not resolve from this session's environment (it is outside the allowed network domains). The current LangSmith docs are at docs.langchain.com/langsmith/.
Sources: https://pypi.org/project/langgraph-checkpoint-mongodb/ https://langchain-mongodb.readthedocs.io/en/stable/langgraph_checkpoint_mongodb/saver/langgraph.checkpoint.mongodb.saver.MongoDBSaver.html https://langchain-mongodb.readthedocs.io/en/stable/langgraph_checkpoint_mongodb/aio/langgraph.checkpoint.mongodb.aio.AsyncMongoDBSaver.html https://langchain-ai.github.io/langgraph/how-tos/persistence_mongodb https://learn.microsoft.com/et-ee/azure/documentdb/persist-agent-state https://jira.mongodb.org/browse/INTPYTHON-728 https://pypi.org/project/elevenlabs/ https://elevenlabs.io/docs/api-reference/speech-to-text/convert.md https://www.mintlify.com/elevenlabs/elevenlabs-python/api-reference/audio/speech-to-text https://elevenlabs.io/docs/llms-full.txt https://cdn.jsdelivr.net/npm/@elevenlabs/react@1.1.1/README.md https://docs.langchain.com/langsmith/observability-quickstart/index.html https://docs.langchain.com/langsmith/annotate-code/index.html https://docs.langchain.com/oss/python/langchain/observability.md https://docs.langchain.com/langsmith/trace-with-langgraph.md https://www.mintlify.com/langchain-ai/langsmith-sdk/installation
Unverified: These points were not confirmed in this session's sources:

- **AsyncMongoDBSaver:** The class appears in the readthedocs API listing at langgraph.checkpoint.mongodb.aio, but I did not see its constructor signature or a usage example.
- **Resuming with graph.invoke(None, config):** Standard LangGraph behaviour, but no source fetched here showed it.
- **graph.get_state:** Not shown in the sources fetched here.
- **The `scribe_v2` model id:** The docs only say v2 models outclass scribe_v1. The exact id string was not confirmed.
- **Browser hook method names:** Sources conflict. One says useConversation returns startConversation/stopConversation, another implies startSession/endSession and accepts signedUrl. Read the @elevenlabs/react README (cdn.jsdelivr.net link) before coding.
- **Signed-URL backend endpoint:** The server-side route that issues the signed URL was not confirmed.
- **Speech Engine (engine.serve):** I did not confirm its import path or arguments.
- **Saving TTS audio:** The PyPI page had no save example. Writing the chunks to a file is standard Python, not taken from the docs.
- **LANGSMITH_ENDPOINT value for the EU region:** The EU URL shown in the snippet is from memory. Copy the exact value from your LangSmith settings.
- **@traceable(name=...) code sample:** Not seen verbatim this session. The search summary confirmed the decorator and that nested calls are linked.
- **The current LangSmith install line:** Seen only in a search summary (`pip install -U langsmith openai`). docs.smith.langchain.com could not be fetched because it is outside this session's allowed network domains.