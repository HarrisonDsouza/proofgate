"""`make e2e`: the honest path end to end over HTTP against the running API (make dev), then a supervisor halt.

1. dr-demo opens every cited evidence item, with real server-credited heartbeats (about 35 s in total).
2. Approve, then run the executor once: the denial must execute and be CONFIRMED by read-back from the claims system.
3. /rules: R1-R8 all pass.
4. Supervisor halts dr-demo: the executed denial is reopened by the compensation worker and confirmed by read-back.
5. /rules: R1-R8 still pass.

It writes to the tenant in the running API's database, so `make e2e` reseeds before and after.
"""
from __future__ import annotations

import math
import sys
import time

import httpx

from pg.config import settings

BASE = "http://localhost:8080"
T = "payer-acme"
REVIEWER = "dr-demo"
TOTAL_MS = 35_000
HB_EVERY_S = 5
ok = True


def check(cond: bool, label: str) -> bool:
    global ok
    print(("PASS " if cond else "FAIL ") + label)
    ok = ok and cond
    return cond


def main() -> int:
    c = httpx.Client(base_url=BASE, timeout=120, headers={"X-Tenant-Id": T, "X-Console-Key": settings.console_key})
    sess = c.post("/api/sessions", json={"tenant_id": T, "reviewer_id": REVIEWER}).raise_for_status().json()
    sid = sess["session_id"]
    c.headers["X-Session-Id"] = sid
    queue = c.get("/api/queue", params={"limit": 1}).raise_for_status().json()
    if not check(bool(queue), f"queue has a proposal for {REVIEWER}"):
        return 1
    p = queue[0]
    cited = [e["evidence_id"] for e in p["cited_evidence"]]
    per_item_ms = max(6_000, TOTAL_MS // len(cited))
    beats = math.ceil(per_item_ms / (HB_EVERY_S * 1000))
    print(f"case {p['case_id']}: opening {len(cited)} cited items, {beats} heartbeats x {HB_EVERY_S}s each")
    for eid in cited:
        tok = c.get(f"/api/cases/{p['case_id']}/evidence/{eid}").raise_for_status().json()["view_token"]
        for _ in range(beats):
            time.sleep(HB_EVERY_S)
            hb = c.post(f"/api/views/{tok}/heartbeat", json={"visible": True, "interacted_within_ms": 0}).json()
        print(f"  {eid}: server-credited active {hb['active_ms']} ms")
        c.post(f"/api/views/{tok}/close")

    a = c.post("/api/approvals", json={"proposal_id": p["proposal_id"],
                                       "attestation_text": "Checked the cited records against the codes and the policy clause."})
    check(a.status_code == 201, f"approval accepted ({a.status_code})")
    r = c.post("/api/agent/run-once").raise_for_status().json()
    check(r["executed"] >= 1, f"executor: executed {r['executed']} of {r['submitted']} {r.get('top_reasons') or ''}")
    ex = c.get(f"/api/examiner/cases/{p['case_id']}").raise_for_status().json()
    denial = ex.get("denial") or {}
    check(denial.get("status") == "CONFIRMED", f"denial {denial.get('denial_id')} is {denial.get('status')} (read back from the claims system)")
    rec = c.get(f"/target/claim/{p['case_id']}").json()
    check(rec.get("status") == "DENIED", f"claims system record is {rec.get('status')}")
    rules = c.get("/rules", params={"tenant": T}).json()
    check(all(v["pass"] for v in rules.values()), "rules R1-R8 all pass after the honest denial")
    if "--no-halt" in sys.argv:
        print(f"{'ALL PASS' if ok else 'SOME CHECKS FAILED'}: {p['case_id']} left executed for the examiner (no halt)")
        return 0 if ok else 1

    h = c.post("/api/suspensions", json={"reviewer_id": REVIEWER, "reason": "SUPERVISOR_HALT"}).raise_for_status().json()
    check(h.get("compensations_created", 0) >= 1, f"halt: {h.get('grants_revoked')} grants revoked, "
                                                    f"{h.get('compensations_created')} denials to reopen")
    status = None
    for _ in range(30):
        time.sleep(1)
        comp = c.get(f"/api/examiner/cases/{p['case_id']}").json().get("compensation")
        status = (comp or {}).get("status") if isinstance(comp, dict) else comp
        if status == "confirmed":
            break
    check(status == "confirmed", f"compensation {status} (worker reopened the claim, read back)")
    rec = c.get(f"/target/claim/{p['case_id']}").json()
    check(rec.get("status") == "OPEN", f"claims system record is {rec.get('status')} after the halt")
    rules = c.get("/rules", params={"tenant": T}).json()
    bad = [k for k, v in rules.items() if not v["pass"]]
    check(not bad, f"rules R1-R8 all pass after the halt {bad or ''}")
    print("ALL PASS" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
