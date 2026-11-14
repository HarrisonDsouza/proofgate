"""Triage agent as a LangGraph graph, built only from the hackathon's sponsor resources.

    load_case -> retrieve_clauses -> rerank -> decide -> validate -> write_proposal

- retrieve_clauses: Voyage embeddings + Atlas Vector Search ($vectorSearch on policy_clauses, filtered by tenant).
- rerank: Voyage rerank-2.5 orders the retrieved clauses against this claim's evidence and picks the governing one.
- decide: Voyage rerank used as a zero-shot judge. It scores the claim's evidence against "the clause's condition is
  met" and "is not met". The agent proposes deny only when "not met" wins by a clear margin. Otherwise it proposes
  pay, so a weak signal never turns into a denial. It also picks which documents the reviewer must read.
- validate: code, not the model, fixes what is recorded: cited ids must exist, hashes come from the case, the clause
  must be a real clause of this tenant.
- write_proposal: the agent's action. It writes the case, the target record and a pending proposal into Atlas.

State is checkpointed in Atlas by langgraph-checkpoint-mongodb (one thread per case), so a crash resumes mid-case.
The agent never sees grants and never calls the target system: a human reviewer and the gate still decide.
Without VOYAGE_API_KEY the graph runs the deterministic rule instead and labels the proposal `rules-v1`.
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from pg import agent
from pg.config import OPERATOR_ID, settings
from pg.db import get_db
from pg.observability import LLM_CALLS, traceable

log = logging.getLogger("pg.graph_agent")
VECTOR_INDEX = "policy_clause_vec"
DIMS = 1024
DENY_MARGIN = 0.05  # "not met" must beat "met" by this much in rerank relevance before the agent proposes a denial
CHECKPOINTS = ("agent_checkpoints", "agent_checkpoint_writes")


class TriageState(TypedDict, total=False):
    tenant: str
    case: dict
    clauses: list[dict]  # retrieved candidates
    ranked: list[dict]  # [{clause_id, text, score}]
    decision: dict  # raw agent judgment before code validation
    proposal: dict  # validated fields
    proposer: str
    fallback_reason: str | None
    trace: list[str]


def _voyage():
    import voyageai

    return voyageai.Client(api_key=settings.voyage_api_key, max_retries=1, timeout=15)


def _evidence_text(case: dict) -> str:
    return "\n".join(f"{e['label']}: {e['content']}" for e in case["evidence"])


def _condition(clause_text: str) -> str:
    # "MP-004: Orthotics requires a prior authorization ... (Made-up policy for the demo.)" -> the condition part
    body = clause_text.split(":", 1)[-1].split("(Made-up")[0].strip().rstrip(".")
    return body


# ---------- Atlas Vector Search ----------

def ensure_vector_index(db, tenant: str, vo=None) -> dict:
    """Embed this tenant's clauses with Voyage (once) and make sure the Atlas Vector Search index exists."""
    from pymongo.operations import SearchIndexModel

    vo = vo or _voyage()
    missing = list(db.policy_clauses.find({"tenant_id": tenant, "embedding": {"$exists": False}}, {"_id": 1, "text": 1}))
    if missing:
        vecs = vo.embed([m["text"] for m in missing], model=settings.voyage_embed_model, input_type="document",
                        output_dimension=DIMS).embeddings
        for m, v in zip(missing, vecs, strict=True):
            db.policy_clauses.update_one({"_id": m["_id"]}, {"$set": {"embedding": v, "embedding_model": settings.voyage_embed_model}})
    names = {ix["name"] for ix in db.policy_clauses.list_search_indexes()}
    if VECTOR_INDEX not in names:
        db.policy_clauses.create_search_index(SearchIndexModel(
            name=VECTOR_INDEX, type="vectorSearch",
            definition={"fields": [{"type": "vector", "path": "embedding", "numDimensions": DIMS, "similarity": "cosine"},
                                   {"type": "filter", "path": "tenant_id"}]}))
    return {"embedded": len(missing), "index": VECTOR_INDEX}


def vector_search(db, tenant: str, qvec: list[float], k: int = 8) -> list[dict]:
    return list(db.policy_clauses.aggregate([
        {"$vectorSearch": {"index": VECTOR_INDEX, "path": "embedding", "queryVector": qvec, "numCandidates": 100,
                           "limit": k, "filter": {"tenant_id": tenant}}},
        {"$project": {"_id": 0, "clause_id": 1, "text": 1, "score": {"$meta": "vectorSearchScore"}}},
    ]))


# ---------- graph nodes ----------

def load_case(state: TriageState) -> TriageState:
    return {"trace": [f"load_case {state['case']['case_id']}"], "fallback_reason": None,
            "proposer": f"graph:voyage/{settings.voyage_rerank_model}" if settings.voyage_api_key else "rules-v1"}


@traceable("agent.retrieve_clauses")
def retrieve_clauses(state: TriageState) -> TriageState:
    if not settings.voyage_api_key:
        return {"fallback_reason": "no VOYAGE_API_KEY", "trace": state["trace"] + ["retrieve: skipped (no key)"]}
    db, case, tenant = get_db(), state["case"], state["tenant"]
    q = f"{case['summary']}\n{_evidence_text(case)}"
    qvec = _voyage().embed([q], model=settings.voyage_embed_model, input_type="query", output_dimension=DIMS).embeddings[0]
    hits = vector_search(db, tenant, qvec)
    how = "$vectorSearch"
    if not hits:  # index still building right after creation: rerank every clause of the tenant instead
        hits = list(db.policy_clauses.find({"tenant_id": tenant}, {"_id": 0, "clause_id": 1, "text": 1}))
        how = "all clauses (vector index not ready)"
    return {"clauses": hits, "trace": state["trace"] + [f"retrieve: {len(hits)} clauses via {how}"]}


@traceable("agent.rerank")
def rerank(state: TriageState) -> TriageState:
    if state.get("fallback_reason"):
        return {}
    clauses = state["clauses"]
    r = _voyage().rerank(_evidence_text(state["case"]), [c["text"] for c in clauses], model=settings.voyage_rerank_model)
    ranked = [{"clause_id": clauses[x.index]["clause_id"], "text": clauses[x.index]["text"], "score": round(x.relevance_score, 4)}
              for x in r.results]
    return {"ranked": ranked, "trace": state["trace"] + [f"rerank: top {ranked[0]['clause_id']} ({ranked[0]['score']})"]}


@traceable("agent.decide")
def decide(state: TriageState) -> TriageState:
    case = state["case"]
    if state.get("fallback_reason"):
        return {"decision": {"rule": agent.triage(case, list(get_db().policy_clauses.find(
            {"tenant_id": state["tenant"]}, {"_id": 0, "clause_id": 1, "text": 1})))},
                "trace": state["trace"] + ["decide: deterministic rule (fallback)"]}
    top = state["ranked"][0]
    cond = _condition(top["text"])
    met = f"The policy condition is satisfied: the documentation shows the claim {cond}, and it is on file."
    unmet = f"The policy condition is not satisfied: the documentation shows nothing on file for what the policy {cond}."
    vo = _voyage()
    judged = vo.rerank(_evidence_text(case), [met, unmet], model=settings.voyage_rerank_model).results
    s = {("met" if x.index == 0 else "unmet"): x.relevance_score for x in judged}
    rec = "deny" if s["unmet"] - s["met"] >= DENY_MARGIN else "pay"
    # which documents should the reviewer read? the ones most relevant to the governing clause
    ev = case["evidence"]
    order = vo.rerank(top["text"], [f"{e['label']}: {e['content']}" for e in ev], model=settings.voyage_rerank_model).results
    cited = [ev[x.index]["evidence_id"] for x in order[:2]]
    why = (f"{top['clause_id']} {cond}; the evidence scores as not meeting it (unmet {s['unmet']:.2f} vs met {s['met']:.2f})."
           if rec == "deny" else
           f"{top['clause_id']} {cond}; the evidence does not clearly fail it (unmet {s['unmet']:.2f} vs met {s['met']:.2f}), so no denial.")
    return {"decision": {"recommendation": rec, "cited_evidence_ids": cited, "clause_id": top["clause_id"], "rationale": why,
                         "scores": s},
            "trace": state["trace"] + [f"decide: {rec} (unmet {s['unmet']:.3f} / met {s['met']:.3f}), cite {cited}"]}


def validate(state: TriageState) -> TriageState:
    """Code decides what is recorded. Model output that fails a check is replaced by the rule, and labelled."""
    case, d = state["case"], state["decision"]
    if "rule" in d:
        return {"proposal": d["rule"], "proposer": "rules-v1", "trace": state["trace"] + ["validate: rule output"]}
    ev = {e["evidence_id"]: e for e in case["evidence"]}
    known = {c["clause_id"] for c in get_db().policy_clauses.find({"tenant_id": state["tenant"]}, {"clause_id": 1})}
    problems = [p for p, bad in (("cited evidence not in case", not d["cited_evidence_ids"] or any(i not in ev for i in d["cited_evidence_ids"])),
                                 ("unknown clause", d["clause_id"] not in known),
                                 ("bad recommendation", d["recommendation"] not in ("deny", "pay"))) if bad]
    if problems:
        rule = agent.triage(case, list(get_db().policy_clauses.find({"tenant_id": state["tenant"]}, {"_id": 0})))
        return {"proposal": rule, "proposer": "rules-v1", "fallback_reason": "; ".join(problems),
                "trace": state["trace"] + [f"validate: rejected ({'; '.join(problems)})"]}
    return {"proposal": {"recommendation": d["recommendation"], "rationale": d["rationale"][:600],
                         "cited_evidence": [{"evidence_id": i, "hash": ev[i]["hash"]} for i in dict.fromkeys(d["cited_evidence_ids"])],
                         "cited_clauses": [d["clause_id"]], "agent_scores": d.get("scores")},
            "trace": state["trace"] + ["validate: ok"]}


def write_proposal(state: TriageState) -> TriageState:
    db, case, tenant = get_db(), dict(state["case"]), state["tenant"]
    now = datetime.now(timezone.utc)
    pid = case["case_id"].replace("CLM", "P")
    if not db.proposals.find_one({"tenant_id": tenant, "proposal_id": pid}, {"_id": 1}):  # idempotent on resume
        db.cases.insert_one(case)
        db.target_records.insert_one({"tenant_id": tenant, "kind": "claim", "record_id": case["case_id"], "status": "PENDING",
                                      "history": [], "reopened_for": []})
        db.proposals.insert_one({"tenant_id": tenant, "proposal_id": pid, "case_id": case["case_id"], "action_type": "claim_denial",
                                 "agent_id": "triage-agent-v1", "model_version": state["proposer"], "proposer": state["proposer"],
                                 "fallback_reason": state.get("fallback_reason"), "agent_trace": state["trace"],
                                 "operator_id": OPERATOR_ID, **state["proposal"], "status": "pending_review",
                                 "requeue_reasons": [], "created_at": now})
    return {"trace": state["trace"] + [f"write_proposal {pid}"]}


def build_graph(checkpointer: Any = None):
    g = StateGraph(TriageState)
    for name, fn in (("load_case", load_case), ("retrieve_clauses", retrieve_clauses), ("rerank", rerank),
                     ("decide", decide), ("validate", validate), ("write_proposal", write_proposal)):
        g.add_node(name, fn)
    g.add_edge(START, "load_case")
    g.add_edge("load_case", "retrieve_clauses")
    g.add_edge("retrieve_clauses", "rerank")
    g.add_edge("rerank", "decide")
    g.add_edge("decide", "validate")
    g.add_edge("validate", "write_proposal")
    g.add_edge("write_proposal", END)
    return g.compile(checkpointer=checkpointer)


def _checkpointer():
    from langgraph.checkpoint.mongodb import MongoDBSaver

    db = get_db()
    return MongoDBSaver(db.client, db_name=db.name, checkpoint_collection_name=CHECKPOINTS[0],
                        writes_collection_name=CHECKPOINTS[1])


def run_case(tenant: str, case: dict, graph=None) -> TriageState:
    graph = graph or build_graph(_checkpointer())
    cfg = {"configurable": {"thread_id": f"{tenant}|{case['case_id']}"}}
    try:
        out = graph.invoke({"tenant": tenant, "case": case}, cfg)
        LLM_CALLS.labels("triage_graph", str(out.get("proposer", "")).startswith("graph:")).inc()
        return out
    except Exception as e:  # a failing model call must not lose the claim: the rule proposes, labelled as such
        log.warning("graph triage failed, rule fallback: %s", type(e).__name__)
        LLM_CALLS.labels("triage_graph", "False").inc()
        clauses = list(get_db().policy_clauses.find({"tenant_id": tenant}, {"_id": 0}))
        state: TriageState = {"tenant": tenant, "case": case, "proposal": agent.triage(case, clauses), "proposer": "rules-v1",
                              "fallback_reason": f"{type(e).__name__}: {str(e)[:120]}", "trace": [f"graph error: {type(e).__name__}"]}
        write_proposal(state)
        return state


def triage_new_claims(tenant: str, n: int = 3, seed: int | None = None) -> dict:
    """Simulate n newly arriving claims and have the graph agent triage each. The seed and the eval stay on the rule."""
    from seed.generate import make_case

    db = get_db()
    setup = ensure_vector_index(db, tenant) if settings.voyage_api_key else {"skipped": "no VOYAGE_API_KEY"}
    existing = db.cases.count_documents({"tenant_id": tenant})
    rng = random.Random(seed if seed is not None else existing * 7919 + 1)
    now = datetime.now(timezone.utc)
    graph = build_graph(_checkpointer())
    out = []
    for k in range(max(1, min(n, 5))):
        c = make_case(rng, tenant, existing + k + 1, "orthopedics", now)
        c["case_id"] = c["case_id"].replace("CLM-", "CLM-N")  # new arrivals never collide with seeded ids
        s = run_case(tenant, c, graph)
        p = s["proposal"]
        out.append({"case_id": c["case_id"], "recommendation": p["recommendation"], "proposer": s["proposer"],
                    "cited": [e["evidence_id"] for e in p["cited_evidence"]], "clause": p["cited_clauses"],
                    "rationale": p["rationale"], "fallback_reason": s.get("fallback_reason"), "trace": s.get("trace", [])})
    return {"agent": "langgraph", "voyage_key_set": bool(settings.voyage_api_key), "vector_index": setup, "claims": out}
