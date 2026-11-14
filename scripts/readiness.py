"""One-command integration check. Prints OK / MISSING / FAIL per integration and never prints a secret.

    python scripts/readiness.py            (loads .env; costs at most one tiny Voyage embedding)

Checks: Atlas ping, collections and indexes, the Voyage key and the Atlas Vector Search index (queryable, clauses
embedded), the ElevenLabs key, LangSmith, the console and agent keys, and the packages the integrations import.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
rows: list[tuple[str, str, str]] = []


def row(name: str, status: str, note: str = "") -> None:
    rows.append((name, status, note))


def has(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def atlas() -> None:
    from pg.db import get_db
    from pg.graph_agent import VECTOR_INDEX
    db = get_db()
    db.command("ping")
    db_name = db.name
    row("Atlas connection", "OK", f"database {db_name}" + ("  (WARNING: the team demo database)" if db_name == "proofgate" else ""))
    row("Collections", "OK" if db.cases.estimated_document_count() else "FAIL",
        f"{db.cases.estimated_document_count()} cases, {db.policy_clauses.estimated_document_count()} clauses" if db.cases.estimated_document_count() else "empty: run make setup seed")
    ix = [x for x in db.policy_clauses.list_search_indexes() if x["name"] == VECTOR_INDEX]
    if not ix:
        row("Atlas Vector Search index", "MISSING", "created on the first triage run once VOYAGE_API_KEY is set")
    else:
        embedded = db.policy_clauses.count_documents({"embedding": {"$exists": True}})
        row("Atlas Vector Search index", "OK" if ix[0].get("queryable") else "FAIL",
            f"{ix[0].get('status')}, {embedded}/{db.policy_clauses.estimated_document_count()} clauses embedded")


def voyage() -> None:
    if not has("VOYAGE_API_KEY"):
        return row("Voyage AI key", "MISSING", "dashboard.voyageai.com -> API Keys")
    try:
        import voyageai
        voyageai.Client().embed(["ping"], model=os.environ.get("VOYAGE_EMBED_MODEL", "voyage-3.5"), input_type="query")
        row("Voyage AI key", "OK", "embedding call succeeded")
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        row("Voyage AI key", "FAIL", "rate limited: add a payment method at dashboard.voyageai.com" if "RateLimit" in type(e).__name__ or "payment method" in msg
            else f"{type(e).__name__}")


def elevenlabs() -> None:
    if not has("ELEVENLABS_API_KEY"):
        return row("ElevenLabs key", "MISSING", "elevenlabs.io -> API Keys")
    import httpx
    r = httpx.get("https://api.elevenlabs.io/v1/models", headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}, timeout=15)
    if r.status_code == 200:
        names = {m.get("model_id") for m in r.json()}
        row("ElevenLabs key", "OK", "valid; " + ("eleven_flash_v2_5 available" if "eleven_flash_v2_5" in names else "check the TTS model id"))
    elif r.status_code in (401, 403):
        detail = (r.json().get("detail") or {}) if r.headers.get("content-type", "").startswith("application/json") else {}
        status = detail.get("status", "") if isinstance(detail, dict) else ""
        row("ElevenLabs key", "OK" if status == "missing_permissions" else "FAIL",
            "key is valid but restricted (needs Text to Speech and Speech to Text)" if status == "missing_permissions" else f"rejected: HTTP {r.status_code} {status}")
    else:
        row("ElevenLabs key", "FAIL", f"HTTP {r.status_code}")


def langsmith() -> None:
    on = os.environ.get("LANGSMITH_TRACING", "").lower() in ("1", "true", "yes")
    if not has("LANGSMITH_API_KEY"):
        return row("LangSmith", "MISSING", "key + LANGSMITH_TRACING=true (Neil's setup)")
    row("LangSmith", "OK" if on else "FAIL", f"project {os.environ.get('LANGSMITH_PROJECT', 'proofgate')}" if on else "key set but LANGSMITH_TRACING is not true")


def server_keys() -> None:
    from pg.config import key_problems, settings
    p = key_problems(settings)
    row("Console and agent keys", "OK" if not p else "FAIL", "private, long enough" if not p else "; ".join(x.split(" (")[0] for x in p))


def packages() -> None:
    bad = []
    for m in ("voyageai", "langgraph", "langgraph.checkpoint.mongodb", "langsmith", "httpx"):
        try:
            importlib.import_module(m)
        except ImportError:
            bad.append(m)
    row("Python packages", "OK" if not bad else "FAIL", "all import" if not bad else "missing: " + ", ".join(bad))
    try:
        importlib.import_module("elevenlabs")
        row("elevenlabs package (voiceover script)", "OK", "installed")
    except ImportError:
        row("elevenlabs package (voiceover script)", "MISSING", 'only for scripts/voiceover.py: pip install "elevenlabs<3"')


def main() -> int:
    for step in (server_keys, packages, atlas, voyage, elevenlabs, langsmith):
        try:
            step()
        except Exception as e:  # noqa: BLE001 - a failing check must not hide the others
            row(step.__name__, "FAIL", type(e).__name__)
    w = max(len(r[0]) for r in rows)
    for name, status, note in rows:
        print(f"{status:<8}{name:<{w + 2}}{note}")
    return 1 if any(s == "FAIL" for _, s, _ in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
