"""Turn scripts/voiceover_script.txt into media/voiceover.mp3 with ElevenLabs text-to-speech.

Usage:  python scripts/voiceover.py [--dry-run]

The key and voice id come from .env (ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID); nothing is printed.
Guards: the script must say "synthetic data" and may only contain the numbers measured in real runs today
(0 of 50, 403, R1 to R8). --dry-run checks the script and spends no credits.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "voiceover_script.txt"
OUT = ROOT / "media" / "voiceover.mp3"
MODEL = "eleven_v4"
FORMAT = "mp3_44100_128"
DEFAULT_VOICE = "c6SfcYrb2t09NHXiT80T"  # Jarnathan, chosen by Neil
ALLOWED_NUMBERS = {"0", "50", "403", "1", "8"}  # "0 of 50", "403", "R1 to R8"


def check(paragraphs: list[str]) -> list[str]:
    text = " ".join(paragraphs)
    problems = []
    if "synthetic data" not in text.lower():
        problems.append('the script must say "synthetic data"')
    bad = sorted({n for n in re.findall(r"\d+", text) if n not in ALLOWED_NUMBERS})
    if bad:
        problems.append(f"numbers not from today's runs: {', '.join(bad)}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="validate the script only; no API call")
    args = ap.parse_args()

    paragraphs = [p.strip() for p in SCRIPT.read_text().split("\n\n") if p.strip()]
    problems = check(paragraphs)
    words = sum(len(p.split()) for p in paragraphs)
    print(f"{len(paragraphs)} paragraphs, {words} words (about {round(words / 2.5)} s at a calm pace)")
    if problems:
        print("script check failed: " + "; ".join(problems))
        return 1
    print("script check ok")
    if args.dry_run:
        return 0

    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    if not os.environ.get("ELEVENLABS_API_KEY"):
        print("ELEVENLABS_API_KEY is not set in .env")
        return 1
    from elevenlabs import VoiceSettings
    from elevenlabs.client import ElevenLabs

    client = ElevenLabs()
    voice = os.environ.get("ELEVENLABS_VOICE_ID") or DEFAULT_VOICE
    chunks = []
    for i, p in enumerate(paragraphs):
        audio = client.text_to_speech.convert(
            voice, text=p, model_id=MODEL, output_format=FORMAT,
            voice_settings=VoiceSettings(stability=0.7, similarity_boost=0.75, style=0.1),
            previous_text=paragraphs[i - 1] if i else None,
            next_text=paragraphs[i + 1] if i + 1 < len(paragraphs) else None,
        )
        chunks.append(b"".join(audio))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(b"".join(chunks))
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
