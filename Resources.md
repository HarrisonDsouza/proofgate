

TORONTO

![][image1]

AGENTS IN CONTEXT  
A MONGODB HACKATHON

RESOURCE GUIDE

NOV 14  
The Quay

# PROBLEM STATEMENTS

This hackathon focuses on agents in context: agents that hold context across sessions, adapt their own guardrails and operate reliably under real workloads. Every project must be built in one of the three statements below, with MongoDB Atlas as your data, memory and state layer.

## STATEMENT ONE: AGENTS YOU CAN AUDIT

An agent that can't explain what it did, and who allowed it, never leaves the sandbox. Build an agent using MongoDB Atlas as the identity, policy and audit layer (collections, schema validation, change streams) that takes real actions across systems, where every action is tied to an identity, checked against policy before it runs, and recorded so a reviewer can reconstruct it afterward.

* How do you decide what an agent may do and enforce it before the action, not after?  
* How do you record what the agent did, why, and under whose authority?  
* How do you stop or roll back an agent mid-run?

## STATEMENT TWO: MEMORY YOU CAN GOVERN

What an agent remembers is data someone has to answer for. Build an agent using MongoDB Atlas and Vector Search to persist and retrieve memory, so that memory changes what it does on the next run, with rules for who can read each memory, how long it lives, and how it gets corrected or forgotten.

* How do you keep one client's or team's memory from leaking into another's?  
* How does the agent fix or drop a memory that turns out wrong or expired?  
* How do you prove a memory changed the agent's behavior and didn't just fill the prompt?

## STATEMENT THREE: FINISH THE JOB

Real work spans many systems and takes hours, and the systems won't hold still. Build an agent that completes a long multi-step task across several systems, using MongoDB Atlas to persist verified task state and Vector Search to retrieve relevant past experience, so it survives crashes and system changes and knows what actually happened.

* How does it tell an action that took effect from one that was only sent?  
* How does it resume after a crash without replaying its whole history?  
* How does it adapt when a system's layout, fields or workflow changes underneath it?

BUILD IN A DAY. DEMO ON STAGE IN TORONTO.

HACKATHON DAY — NOV 14

| ● 9:00 AMDoors open & team formation | ● 10:45 AMHacking begins | ● 5:00 PM Submissions due | ● 5:15 PMFirst round judging | ● 7:00 PMFinal round judging | ● 8:15 PMWinners announced  |
| :---: | :---: | :---: | :---: | :---: | :---: |

# HACKATHON REQUIREMENTS

* **Finalist requirement:** You **must** build your project using the MongoDB Atlas Hackathon Sandbox (sent to email).

* **No prior projects:** All work must be original.

* **Demo access:** Check that your repository is public and your demo link is accessible.

* **Team size:** Up to 4 members.

* **Demo & attendance:** Hacking runs until 5:00 PM on Nov 14; all demos are live and in-person. First round judging runs 5:15 PM – 6:45 PM; the top 6 teams present at 7:00 PM; winners are announced at 8:15 PM.

## MONGODB ATLAS SANDBOX

* You should have received an email with a link to join the MongoDB Atlas Sandbox for the hackathon.

* You must create your project \+ cluster through this link. Keep an eye out for this email\!

* **In order to be eligible to be a finalist, your hackathon project must be built in this sandbox.**

## CEREBRAL VALLEY PLATFORM

* **All projects must be submitted through the Cerebral Valley Platform.**

* **You will submit:** a link to your public GitHub repository, a 1-minute demo video showing the code & functionality your team built today, and a concise project description detailing what you built.

* **Reminders:** verify that your video has video & audio playback, and double check that all team members have been added to your submission.

## PRIZES

| 1st  MongoDB: \$7,000 USD LangSmith: \$3,000 Credits ElevenLabs: 3 months Pro Tier |  | 2nd  MongoDB: \$5,000 USD LangSmith: \$2,000 Credits  |  | 3rd  MongoDB: \$3,000 USD LangSmith: \$1,000 Credits  |
| :---: | :---- | ----- | :---- | ----- |

**Best Project Built with ElevenLabs:** 3 months of ElevenLabs Scale Tier.

# MONGODB RESOURCES

## RECOMMENDED STARTING POINT

Configure the following before you start building. Together, they give your AI coding assistant the context, connectivity, and prompting guidance it needs to work effectively with MongoDB. 

* [**MongoDB Agent Skills**](https://www.mongodb.com/docs/agent-skills/) — A set of instructions that can be installed into an AI coding assistant (such as Claude, Cursor, or GitHub Copilot) to provide it with MongoDB best practices for connecting to a database, structuring data, writing queries, and implementing search.

* [**MongoDB MCP Server**](https://www.mongodb.com/docs/mcp-server/get-started/) — Enables an AI coding assistant to connect directly to a live MongoDB database to inspect data, run queries, retrieve counts, and manage Atlas resources.

* [**Natural Language to MongoDB Queries**](https://www.mongodb.com/docs/manual/natural-language-to-mongodb/) — Guidance on how to prompt an AI assistant effectively, including what details to provide about the desired task, data structure, and output format.

*Recommended sequence: install Agent Skills, connect the MCP Server, and reference the prompting guide throughout development.*

## DEVELOPER TOOLS

* **Atlas Managed MCP Server** — A hosted MCP server that connects AI agents and automated workflows to Atlas using Atlas service accounts instead of end-user credentials. No local MCP infrastructure to run, and you can connect from any harness.

* **Frontier Marketplace Connectors** — Native Atlas access inside ChatGPT and Codex, Claude, Gemini, Grok Build, Devin, and Cursor. Query data, inspect schemas and manage indexes without leaving your AI tool.

## DATA AND SEARCH

* [**Sample Movie Dataset**](https://www.mongodb.com/docs/atlas/sample-data/sample-mflix) — A ready-to-use dataset that can be loaded in minutes and is preconfigured for AI-powered search.

* [**Data Modeling in MongoDB**](https://www.mongodb.com/docs/manual/data-modeling/#data-modeling) — Best practices for structuring data for efficient use by applications and AI agents.

* [**Vector Search**](https://www.mongodb.com/products/platform/atlas-vector-search) — Enables search based on semantic meaning rather than exact keyword matches, forming the basis for long-term, retrievable agent memory.

* [**Atlas Search**](https://www.mongodb.com/docs/atlas/atlas-search/) — Provides fast, typo-tolerant keyword search capabilities.

* [**Automated Embeddings**](https://www.mongodb.com/company/blog/product-release-announcements/unlocking-ai-search-introducing-automated-embedding-in-mongodb-vector-search) — Generates and maintains vector embeddings within the database, removing the need for a separate embedding pipeline.

* [**Embedding and Reranking API**](https://www.mongodb.com/docs/api/doc/atlas-embedding-and-reranking-api/) — A single endpoint for embedding and reranking operations, accessible from any application or technology stack.

## MEMORY AND AGENTS

* [**Building an Agent with Memory and Function Calling**](https://www.mongodb.com/docs/vector-search/about/ai-agents/) — An example of an agent that retains context and executes functions to act on data.

* [**Adding Memory to a Chat Application (Python)**](https://www.mongodb.com/docs/atlas/ai-integrations/langchain/memory-semantic-cache/) — Demonstrates how to maintain context across a conversation using LangChain and MongoDB Atlas.

* [**Adding Memory to a Chat Application (JavaScript)**](https://www.mongodb.com/docs/atlas/ai-integrations/langchain-js/) — The same approach implemented in JavaScript.

## STATE

* [**Build an AI Agent with LangGraph and MongoDB Atlas**](https://www.mongodb.com/docs/atlas/ai-integrations/langgraph/build-agents/) — A practical example using thread-specific checkpoints and conversation persistence.

* [**State & Persistence: The Problem of Agent Reliability**](https://www.mongodb.com/company/blog/technical/state-persistence-the-problem-of-agent-reliability) — A deeper look at checkpoints, suspend/resume, crash recovery, and where state ends and memory begins.

## CONTEXT

* [**Build AI Agents with MongoDB**](https://www.mongodb.com/docs/vector-search/about/ai-agents/) — Agents that use MongoDB for retrieval alongside APIs and external tools.

* [**GraphRAG with MongoDB and LangChain**](https://www.mongodb.com/docs/atlas/ai-integrations/langchain/graph-rag/) — Ingest external documents and retrieve relationship-aware context.

## STARTER CODE

* [**GenAI Showcase**](https://github.com/mongodb-developer/GenAI-Showcase/tree/main) — A comprehensive library of example applications spanning multiple AI frameworks and programming languages.

* [**MongoDB and Python Quickstart**](https://github.com/mongodb-developer/mongodb-atlas-python-quickstart/blob/main/quickstart-1-getting-started-atlas-python.ipynb) — An introductory guide for building with MongoDB Atlas and Python.

* [**MERN Starter Application**](https://github.com/mongodb-developer/mern-stack-example) — A starter project using MongoDB, Express, React, and Node.js.

## AFTER THE HACKATHON

* [**MongoDB for Startups**](https://www.mongodb.com/startups) — Get Atlas credits, Voyage AI tokens, technical expertise, and dedicated support on the world’s leading AI-ready data platform.

**Not sure where to begin?** Complete the three items under Recommended starting point, then consult the GenAI Showcase for relevant examples.

# PARTNER RESOURCES

Credits and tools from our partners. Most credits are only available to checked-in participants, so make sure you’re registered on the Cerebral Valley Platform and checked in on the day.

## ELEVENLABS

AI voice platform covering speech, agents, dubbing and sound effects. One month of the Creator plan free for every participant (131k credits).

* **Access:** Join the [ElevenLabs Discord](https://discord.com/invite/VnBvbbcdEC), open the \#coupon-codes channel and click “Start Redemption”. Select this event and fill out the form with the email you registered with on the Cerebral Valley platform, and the bot will send your unique coupon code. Only available if you have checked in to the event by 11 AM.

* **Feedback:** After the event, please fill out the hacker feedback form linked in the ElevenLabs Hacker Guide.

[**ElevenLabs Hacker Guide**](https://docs.google.com/document/d/1mCh5MtOzBw0aJpurQVUmIVFfPMAHW3MjNemE-LNiMto/edit?tab=t.0)   ·   [**Redemption video tutorial**](https://youtu.be/S143_JtCtV8)

## LANGCHAIN

\$50 in LangSmith credits plus Deployments access, along with docs and starter templates for building agents.

* **Access:** Redeem through the form below within 10 days of the hackathon, entering the hackathon name as the event. You’ll need to add a card to LangSmith to display the credits; it won’t be charged.

[**Redeem credits**](https://airtable.com/appzjKToipPcn2dKI/pagTsO0Ld3edczsrV/form)   ·   [**LangChain hacker resources**](https://app.notion.com/p/Hackathon-Resources-from-LangChain-34f808527b1780c8a82bd0b8f0c322a2)   ·   [**LangGraph docs**](https://docs.langchain.com/oss/python/langgraph/overview)   ·   [**Deep Agents quickstart**](https://docs.langchain.com/oss/python/deepagents/quickstart)

## VOYAGE AI

[Voyage AI](https://www.voyageai.com/) builds state-of-the-art embedding models and rerankers for accurate, efficient search over unstructured data — leading the field in retrieval quality, model size, vector dimensions, and latency. Every participant gets 200 million free tokens to use for the event, which should cover most projects without incurring any cost.

### **Get Set Up**

* [**Create a Voyage AI Account**](https://dashboard.voyageai.com/) — Sign up with just an email address.  
* [**Generate an API Key**](https://dashboard.voyageai.com/organization/api-keys) — From Organization \> API Keys, create a new secret key and save it immediately; it won't be shown again.  
* [**Add a Payment Method**](https://dashboard.voyageai.com/organization/billing) — Unlocks standard Tier 1 rate limits. No charge is required, and you won't be billed as long as you stay within your free token allowance. See the [rate limits page](https://docs.voyageai.com/docs/rate-limits) for details.

### **Build with the API**

* [**API Key & Python Client Setup**](https://docs.voyageai.com/docs/api-key-and-installation) — Install the client with pip install voyageai and authenticate.  
* [**Quickstart Tutorial**](https://docs.voyageai.com/docs/quickstart-tutorial) — A step-by-step guide to building a simple RAG chatbot with Voyage embeddings, covering embedding text, vector search, and reranking.  
* [**Pricing & Free Credits**](https://docs.voyageai.com/docs/pricing) — Details on token costs and how the free allowance applies.

### **Track Usage & Get Support**

* [**Usage Dashboard**](https://dashboard.voyageai.com/organization/usage) — Monitor tokens used and remaining free credits in real time.  
* **Need more tokens?** 200M is generous, but if you're approaching the limit, ask the event host or any member of the Voyage AI team for a top-up — you won't run out during the event.  
* **Have questions?** The Voyage AI team is on-site throughout the event. Don't hesitate to ask.

[image1]: <data:image/png;base64,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>