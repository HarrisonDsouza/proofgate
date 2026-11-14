from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    db_name: str = os.getenv("DB_NAME", "proofgate")
    agent_service_key: str = os.getenv("AGENT_SERVICE_KEY", "")
    # Operator console key: required on /api/sessions and every control route (policies, suspensions, pause, run-once).
    console_key: str = os.getenv("CONSOLE_KEY", "")
    debug_hooks: bool = os.getenv("DEMO_DEBUG_HOOKS", "false").lower() == "true"
    run_background: bool = os.getenv("RUN_BACKGROUND", "1") == "1"  # detector + compensation worker threads
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")
    llm_model: str = os.getenv("LLM_MODEL", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")


settings = Settings()

PUBLIC_DEFAULT_KEYS = {"", "dev-agent-key-change-me", "change-me"}
MIN_KEY_LEN = 24


def key_problems(s: Settings) -> list[str]:
    """Keys the API refuses to start with: empty, a value published in the repo, or too short."""
    out = []
    for name, val in (("AGENT_SERVICE_KEY", s.agent_service_key), ("CONSOLE_KEY", s.console_key)):
        if val in PUBLIC_DEFAULT_KEYS or len(val) < MIN_KEY_LEN:
            out.append(f"{name} must be a private random value of at least {MIN_KEY_LEN} characters "
                       f"(generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))')")
    return out

AGENT_ID = "triage-agent-v1"
OPERATOR_ID = "op-ops-1"
