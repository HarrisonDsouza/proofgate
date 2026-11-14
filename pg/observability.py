"""Observability: structured logs, Prometheus metrics, Atlas time-series, LangSmith.

Three layers, one correlation id:
- `request_id` (also the decisionId) appears in the JSON log line, the Atlas
  decision document, the metrics time-series point and the LangSmith run metadata.
- Prometheus text at GET /metrics for the infra view.
- An Atlas time-series collection `telemetry` that the page's Ops panel reads,
  so the judges see live latency and outcomes stored in MongoDB itself.
"""
from __future__ import annotations

import json
import logging
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable

from prometheus_client import Counter, Histogram

DECISIONS = Counter("proofgate_decisions_total", "Operate decisions", ["outcome", "requester_type"])
OPERATE_LATENCY = Histogram(
    "proofgate_operate_seconds", "Operate transaction latency",
    buckets=(0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2),
)
TXN_RETRIES = Counter("proofgate_txn_retries_total", "Transaction retries on write conflict")
CLOSER_EVENTS = Counter("proofgate_closer_events_total", "Permit change-stream events", ["result"])
LLM_CALLS = Counter("proofgate_llm_calls_total", "LLM calls", ["purpose", "ok"])
STT_CALLS = Counter("proofgate_stt_calls_total", "Speech-to-text calls", ["ok"])


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        payload.update(getattr(record, "extra_fields", {}))
        return json.dumps(payload, default=str)


def get_logger(name: str = "proofgate") -> logging.Logger:
    log = logging.getLogger(name)
    if not log.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(JsonFormatter())
        log.addHandler(h)
        log.setLevel(logging.INFO)
    return log


def log_event(msg: str, **fields: Any) -> None:
    get_logger().info(msg, extra={"extra_fields": fields})


@contextmanager
def timed():
    t0 = time.perf_counter()
    box = {"ms": 0.0}
    try:
        yield box
    finally:
        box["ms"] = (time.perf_counter() - t0) * 1000


def record_telemetry(db, kind: str, value: float, **meta: Any) -> None:
    """Write one point to the Atlas time-series collection. Never raises."""
    try:
        db.telemetry.insert_one({"ts": datetime.now(timezone.utc), "meta": {"kind": kind, **meta}, "value": value})
    except Exception as e:  # observability must never break the safety path
        log_event("telemetry_write_failed", error=str(e))


def traceable(name: str) -> Callable:
    """LangSmith @traceable if installed and configured, else a no-op."""
    try:
        from langsmith import traceable as _t  # type: ignore
        return _t(name=name)
    except Exception:  # pragma: no cover
        return lambda f: f
