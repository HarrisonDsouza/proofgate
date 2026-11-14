from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    db_name: str = os.getenv("DB_NAME", "proofgate")
    agent_service_key: str = os.getenv("AGENT_SERVICE_KEY", "dev-agent-key-change-me")
    debug_hooks: bool = os.getenv("DEMO_DEBUG_HOOKS", "false").lower() == "true"
    run_background: bool = os.getenv("RUN_BACKGROUND", "1") == "1"  # detector + compensation worker threads
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")
    llm_model: str = os.getenv("LLM_MODEL", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")


settings = Settings()

AGENT_ID = "triage-agent-v1"
OPERATOR_ID = "op-ops-1"
