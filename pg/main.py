"""ProofGate API: one FastAPI process (gate + reviewer API + mock targets + rules + UI).

Follows the PRD Section 8 contract. Run: uvicorn pg.main:app --port 8080
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from pg import agent, config, gate, graph_agent, review, rules, target, voice
from pg.auth import console_only, same
from pg.config import settings
from pg.db import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    problems = config.key_problems(settings)
    if problems:
        raise RuntimeError("Refusing to start: " + "; ".join(problems))
    stops = []
    if settings.run_background:
        from pg import detector
        stops.append(detector.start_background())
    yield
    for s in stops:
        s.set()


app = FastAPI(title="ProofGate", lifespan=lifespan)
app.include_router(target.router)
app.include_router(voice.router)


def clean(x):
    return json.loads(json.dumps(x, default=str))


_same = same
MAX_BULK = 100


def _text(v, name: str, max_len: int, allow_empty: bool = False) -> str:
    """Request fields that reach a Mongo filter must be plain bounded strings: a dict like {"$ne": ""} is an operator."""
    if not isinstance(v, str) or (not v and not allow_empty) or len(v) > max_len:
        raise HTTPException(422, f"{name} must be a string of at most {max_len} characters")
    return v


def agent_only(x_service_identity: str | None, x_service_key: str | None):
    if x_service_identity != "triage-agent-v1" or not _same(x_service_key, settings.agent_service_key):
        raise HTTPException(401, "agent service identity required")


@app.exception_handler(review.BadRequest)
async def br(_, e):
    return JSONResponse({"error": str(e)}, status_code=400)


@app.exception_handler(gate.PolicyRejected)
async def pr(_, e):
    return JSONResponse({"error": str(e)}, status_code=400)


@app.exception_handler(review.NotFound)
async def nf(_, e):
    return JSONResponse({"error": str(e)}, status_code=404)


# ---------------- reviewer ----------------
@app.post("/api/sessions", dependencies=[Depends(console_only)])
def sessions(body: dict):
    return clean(review.open_session(body["tenant_id"], body["reviewer_id"]))


@app.get("/api/queue")
def queue(x_tenant_id: str = Header(...), x_session_id: str | None = Header(None), status: str = "pending_review", limit: int = Query(50, ge=1, le=100)):
    db = get_db()
    q = {"tenant_id": x_tenant_id, "status": status, "recommendation": "deny"}
    if x_session_id:
        s = db.reviewer_sessions.find_one({"tenant_id": x_tenant_id, "session_id": x_session_id})
        rv = db.reviewers.find_one({"tenant_id": x_tenant_id, "reviewer_id": s["reviewer_id"]}) if s else None
        if rv:
            q["case_id"] = {"$in": [c["case_id"] for c in db.cases.find({"tenant_id": x_tenant_id, "specialty": rv["specialty"]}, {"case_id": 1})]}
    out = []
    for p in db.proposals.find(q).sort("created_at", 1).limit(limit):
        case = db.cases.find_one({"tenant_id": x_tenant_id, "case_id": p["case_id"]})
        labels = {e["evidence_id"]: e["label"] for e in case["evidence"]}
        out.append({"proposal_id": p["proposal_id"], "case_id": p["case_id"], "action_type": p["action_type"],
                    "recommendation": p["recommendation"], "summary": case["summary"], "rationale": p["rationale"],
                    "codes": case["codes"], "billed_amount": case["billed_amount"],
                    "cited_evidence": [{"evidence_id": c["evidence_id"], "label": labels[c["evidence_id"]]} for c in p["cited_evidence"]],
                    "all_evidence": [{"evidence_id": e["evidence_id"], "label": e["label"]} for e in case["evidence"]],
                    "created_at": p["created_at"]})
    return clean(out)


@app.get("/api/cases/{case_id}/evidence/{evidence_id}")
def evidence(case_id: str, evidence_id: str, x_tenant_id: str = Header(...), x_session_id: str = Header(...)):
    return review.fetch_evidence(x_tenant_id, x_session_id, case_id, evidence_id)


@app.post("/api/views/{token}/heartbeat")
def hb(token: str, body: dict, x_tenant_id: str = Header(...)):
    return review.heartbeat(x_tenant_id, token, bool(body.get("visible")), int(body.get("interacted_within_ms", 10 ** 9)))


@app.post("/api/views/{token}/close")
def close_view(token: str, x_tenant_id: str = Header(...)):
    return review.close_view(x_tenant_id, token)


@app.post("/api/approvals", status_code=201)
def approvals(body: dict, x_tenant_id: str = Header(...), x_session_id: str = Header(...)):
    pid = _text(body.get("proposal_id"), "proposal_id", 100)  # a dict here would be a Mongo operator injection (S10)
    att = _text(body.get("attestation_text", ""), "attestation_text", 2000, allow_empty=True)
    aid = body.get("attestation_id")
    aid = _text(aid, "attestation_id", 100) if aid is not None else None
    if len(body) > 20:
        raise HTTPException(422, "too many fields")
    return clean(review.approve(x_tenant_id, x_session_id, pid, att, body, aid))


@app.post("/api/approvals/bulk")
def approvals_bulk(body: dict, x_tenant_id: str = Header(...), x_session_id: str = Header(...)):
    ids = body.get("proposal_ids")
    if not isinstance(ids, list) or not 1 <= len(ids) <= MAX_BULK:
        raise HTTPException(422, f"proposal_ids must be a list of 1 to {MAX_BULK} strings")
    ids = [_text(i, "proposal_ids[]", 100) for i in ids]
    att = _text(body.get("attestation_text", "Reviewed in batch."), "attestation_text", 2000, allow_empty=True)
    return review.approve_bulk(x_tenant_id, x_session_id, ids, att)


# ---------------- agent ----------------
@app.post("/api/gate/execute")
def gate_execute(body: dict, x_tenant_id: str = Header(...), x_service_identity: str | None = Header(None),
                 x_service_key: str | None = Header(None)):
    agent_only(x_service_identity, x_service_key)
    # No debug-pause over HTTP: eval/test_conflict.py passes debug_pause_ms to gate.execute in Python.
    res = gate.execute(x_tenant_id, body["proposal_id"], body["approval_id"], body.get("agent_id", "triage-agent-v1"),
                       body.get("operator_id", "op-ops-1"))
    return JSONResponse(clean(res), status_code=200 if res["decision"] == "ALLOW" else 409)


@app.post("/api/gate/confirm")
def gate_confirm(body: dict, x_tenant_id: str = Header(...), x_service_identity: str | None = Header(None),
                 x_service_key: str | None = Header(None)):
    agent_only(x_service_identity, x_service_key)
    return gate.confirm(x_tenant_id, body["denial_id"])


@app.post("/api/agent/run-once", dependencies=[Depends(console_only)])
def run_once(x_tenant_id: str = Header(...)):
    """Demo convenience: run the executor once over every approved deny proposal."""
    res = agent.executor_loop(x_tenant_id, once=True)
    executed = sum(1 for r in res if r.get("confirm", {}).get("status") == "CONFIRMED")
    reasons: dict[str, int] = {}
    for r in res:
        for c in r.get("reasons", []):
            reasons[c["rule"]] = reasons.get(c["rule"], 0) + 1
    db = get_db()
    db.agent_control.update_one({"_id": f"executor|{x_tenant_id}"},
                                {"$set": {"last_burst": {"submitted": len(res), "executed": executed, "top_reasons": reasons}}}, upsert=True)
    return clean({"submitted": len(res), "executed": executed, "refused": len(res) - executed, "top_reasons": reasons})


@app.post("/api/agent/triage-new", dependencies=[Depends(console_only)])
def triage_new(body: dict | None = None, x_tenant_id: str = Header(...)):
    """New claims arrive; the LangGraph triage agent (Atlas Vector Search + Voyage rerank) proposes. Humans and the gate decide."""
    n = int((body or {}).get("n", 3))
    return clean(graph_agent.triage_new_claims(x_tenant_id, n))


@app.post("/api/agent/pause", dependencies=[Depends(console_only)])
def pause(body: dict, x_tenant_id: str = Header(...)):
    return gate.set_paused(x_tenant_id, bool(body.get("paused", True)))


# ---------------- supervisor ----------------
@app.get("/api/policies")
def policies(x_tenant_id: str = Header(...)):
    return clean(list(get_db().review_policies.find({"tenant_id": x_tenant_id}, {"_id": 0}).sort("version", -1)))


@app.post("/api/policies", dependencies=[Depends(console_only)])
def new_policy(body: dict, x_tenant_id: str = Header(...)):
    return gate.new_policy_version(x_tenant_id, body.get("action_type", "claim_denial"), body.get("rules", {}),
                                   body.get("rationale", "updated"), body.get("created_by", "supervisor"))


@app.post("/api/suspensions", dependencies=[Depends(console_only)])
def halt(body: dict, x_tenant_id: str = Header(...)):
    return gate.suspend(x_tenant_id, body["reviewer_id"], "supervisor", body.get("reason", "SUPERVISOR_HALT"), {})


@app.get("/api/dashboard")
def dashboard(x_tenant_id: str = Header(...)):
    db = get_db()
    t = {"tenant_id": x_tenant_id}
    return clean({"executed": db.denials.count_documents(t | {"status": "CONFIRMED"}),
                  "reversed": db.denials.count_documents(t | {"status": "REVERSED"}),
                  "refused": db.gate_decisions.count_documents(t | {"decision": "REFUSE"}),
                  "pending": db.proposals.count_documents(t | {"status": "pending_review", "recommendation": "deny"}),
                  "suspended_reviewers": [s["reviewer_id"] for s in db.suspensions.find(t | {"active": True})],
                  "suspensions": list(db.suspensions.find(t, {"_id": 0}).sort("ts", -1).limit(10)),
                  "last_burst": (db.agent_control.find_one({"_id": f"executor|{x_tenant_id}"}) or {}).get("last_burst")})


@app.get("/api/examiner/cases/{case_id}")
def examiner(case_id: str, x_tenant_id: str = Header(...)):
    return clean(rules.examiner(x_tenant_id, case_id))


@app.get("/api/verify/chain/{session_id}")
def verify_chain(session_id: str, x_tenant_id: str = Header(...)):
    """Examiner check: is the review-event hash chain intact? Returns the first broken seq if not."""
    bad = rules.verify_session_chain(get_db(), x_tenant_id, session_id, first_bad_seq=True)
    return {"session_id": session_id, "intact": bad is True, "first_broken_seq": None if bad is True else bad}


@app.get("/rules")
def rules_route(tenant: str):
    return rules.run_rules(tenant)


@app.get("/api/explain/window")
def explain(x_tenant_id: str = Header(...), reviewer_id: str = "dr-stamper"):
    """S8: the G6 window query uses {tenant_id, reviewer_id, created_at}: IXSCAN, not COLLSCAN."""
    db = get_db()
    plan = db.command("explain", {"find": "approvals", "filter": {"tenant_id": x_tenant_id, "reviewer_id": reviewer_id,
                                                                  "created_at": {"$gte": datetime(1970, 1, 1, tzinfo=timezone.utc)}}},
                      verbosity="executionStats")
    ex = plan["executionStats"]
    return clean({"winningPlan": plan["queryPlanner"]["winningPlan"], "keysExamined": ex["totalKeysExamined"],
                  "docsExamined": ex["totalDocsExamined"], "nReturned": ex["nReturned"]})


@app.get("/api/ops")
def ops(x_tenant_id: str = Header(...), minutes: int = Query(15, ge=1, le=1440)):
    """Ops panel: gate latency percentiles, retries and detector lag from the Atlas time-series collection.
    One $group over the (ts, meta) bucketed index: O(points in window)."""
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    rows = list(db.telemetry.aggregate([
        {"$match": {"ts": {"$gte": since}, "meta.tenant_id": x_tenant_id}},
        {"$group": {"_id": "$meta.kind", "n": {"$sum": 1}, "avg": {"$avg": "$value"}, "max": {"$max": "$value"},
                    "p": {"$percentile": {"input": "$value", "p": [0.5, 0.95, 0.99], "method": "approximate"}}}}]))
    return clean({r["_id"]: {"n": r["n"], "avg": round(r["avg"], 2), "max": round(r["max"], 2),
                             "p50": r["p"][0], "p95": r["p"][1], "p99": r["p"][2]} for r in rows})


@app.get("/api/evidence/problem")
def problem_evidence():
    return json.loads((Path(__file__).resolve().parent.parent / "data" / "processed" / "problem_figures.json").read_text())


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
def health():
    get_db().command("ping")
    return {"ok": True}


app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "static", html=True), name="ui")
