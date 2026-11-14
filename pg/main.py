"""ProofGate API: one FastAPI process (gate + reviewer API + mock targets + rules + UI).

Follows the PRD Section 8 contract. Run: uvicorn pg.main:app --port 8080
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from pg import agent, gate, review, rules, target, voice
from pg.config import settings
from pg.db import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
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


def agent_only(x_service_identity: str | None, x_service_key: str | None):
    if x_service_identity != "triage-agent-v1" or x_service_key != settings.agent_service_key:
        raise HTTPException(401, "agent service identity required")


@app.exception_handler(review.NotFound)
async def nf(_, e):
    return JSONResponse({"error": str(e)}, status_code=404)


# ---------------- reviewer ----------------
@app.post("/api/sessions")
def sessions(body: dict):
    return clean(review.open_session(body["tenant_id"], body["reviewer_id"]))


@app.get("/api/queue")
def queue(x_tenant_id: str = Header(...), x_session_id: str | None = Header(None), status: str = "pending_review", limit: int = 50):
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
    return clean(review.approve(x_tenant_id, x_session_id, body["proposal_id"], body.get("attestation_text", ""), body,
                                    body.get("attestation_id")))


@app.post("/api/approvals/bulk")
def approvals_bulk(body: dict, x_tenant_id: str = Header(...), x_session_id: str = Header(...)):
    return review.approve_bulk(x_tenant_id, x_session_id, body["proposal_ids"], body.get("attestation_text", "Reviewed in batch."))


# ---------------- agent ----------------
@app.post("/api/gate/execute")
def gate_execute(body: dict, request: Request, x_tenant_id: str = Header(...), x_service_identity: str | None = Header(None),
                 x_service_key: str | None = Header(None)):
    agent_only(x_service_identity, x_service_key)
    pause = int(request.headers.get("X-Debug-Pause-Ms", "0") or 0)
    res = gate.execute(x_tenant_id, body["proposal_id"], body["approval_id"], body.get("agent_id", "triage-agent-v1"),
                       body.get("operator_id", "op-ops-1"), pause)
    return JSONResponse(clean(res), status_code=200 if res["decision"] == "ALLOW" else 409)


@app.post("/api/gate/confirm")
def gate_confirm(body: dict, x_tenant_id: str = Header(...), x_service_identity: str | None = Header(None),
                 x_service_key: str | None = Header(None)):
    agent_only(x_service_identity, x_service_key)
    return gate.confirm(x_tenant_id, body["denial_id"])


@app.post("/api/agent/run-once")
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


@app.post("/api/agent/pause")
def pause(body: dict, x_tenant_id: str = Header(...)):
    return gate.set_paused(x_tenant_id, bool(body.get("paused", True)))


# ---------------- supervisor ----------------
@app.get("/api/policies")
def policies(x_tenant_id: str = Header(...)):
    return clean(list(get_db().review_policies.find({"tenant_id": x_tenant_id}, {"_id": 0}).sort("version", -1)))


@app.post("/api/policies")
def new_policy(body: dict, x_tenant_id: str = Header(...)):
    return gate.new_policy_version(x_tenant_id, body.get("action_type", "claim_denial"), body.get("rules", {}),
                                   body.get("rationale", "updated"), body.get("created_by", "supervisor"))


@app.post("/api/suspensions")
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
