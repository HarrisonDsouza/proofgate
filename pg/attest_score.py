"""Deterministic scoring of a spoken (or typed) attestation against the case it claims to cover.

Voice is EVIDENCE, never a gate rule (CLAUDE.md rule 7: the model proposes, code decides). This module
turns a transcript into numbers a human or the detector can use; nothing here can allow or refuse a denial.

Signals (all pure functions, O(T + E) time and O(V) space for T transcript tokens, E evidence tokens, V vocab):
  - specificity: share of the case's *distinctive* terms (codes, evidence labels, rare words) that the
    reviewer actually said, IDF-weighted so "the patient" counts for nothing and "M17.11" counts a lot.
  - boilerplate: Jaccard overlap with the reviewer's own previous attestations (a reviewer who says the
    same sentence for every case is stamping with their voice).
  - pace: spoken words per second against what the audio length allows (an impossible rate means TTS
    playback or a pasted transcript, not a person reading evidence).
"""
from __future__ import annotations

import math
import re
from collections import Counter

_TOK = re.compile(r"[a-z0-9][a-z0-9.\-]*[a-z0-9]|[a-z0-9]")
STOP = frozenset("a an the and or of to in on for with is was are were be been by at as it this that these those i we "
                 "have has had reviewed review denial deny denied claim claims case patient evidence item items "
                 "checked looked confirm confirmed".split())


def tokens(text: str) -> list[str]:
    return [t for t in _TOK.findall((text or "").lower().replace("_", " ")) if t not in STOP]


def case_terms(case: dict, cited_ids: set[str] | None = None) -> Counter:
    """Terms the reviewer could only know by reading this case: codes, evidence labels, evidence text."""
    bag: Counter = Counter()
    for c in (case.get("codes", {}).get("icd10", []) + case.get("codes", {}).get("hcpcs", [])):
        bag[c.lower()] += 3  # a code is the strongest proof of case contact
    for e in case.get("evidence", []):
        if cited_ids is not None and e["evidence_id"] not in cited_ids:
            continue
        for t in tokens(e.get("label", "")):
            bag[t] += 2
        for t in tokens(e.get("content", "")):
            bag[t] += 1
    return bag


def specificity(transcript: str, case: dict, corpus_df: dict[str, int] | None = None, n_docs: int = 1,
                cited_ids: set[str] | None = None) -> dict:
    """IDF-weighted recall of the case's distinctive terms in the transcript, in [0, 1].

    corpus_df/n_docs (document frequency over all cases in the tenant) make common words weigh little.
    Without a corpus every term gets weight 1 (still deterministic, just less discriminating)."""
    said = set(tokens(transcript))
    terms = case_terms(case, cited_ids)
    if not terms:
        return {"specificity": 0.0, "matched": [], "n_terms": 0}
    df = corpus_df or {}

    def w(t: str) -> float:
        return terms[t] * math.log(1 + (n_docs + 1) / (df.get(t, 0) + 1))

    total = sum(w(t) for t in terms)
    hits = [t for t in terms if t in said]
    got = sum(w(t) for t in hits)
    # cap: nobody can be expected to say every word of the evidence; saturate at 15% of the weight
    score = min(1.0, (got / total) / 0.15) if total else 0.0
    top = sorted(hits, key=w, reverse=True)[:6]
    return {"specificity": round(score, 3), "matched": top, "n_terms": len(terms)}


def jaccard(a: str, b: str) -> float:
    sa, sb = set(tokens(a)), set(tokens(b))
    return len(sa & sb) / len(sa | sb) if sa | sb else 0.0


def boilerplate(transcript: str, previous: list[str]) -> float:
    """Max Jaccard overlap with the reviewer's last attestations: 1.0 = word-for-word the same sentence."""
    return round(max((jaccard(transcript, p) for p in previous), default=0.0), 3)


def pace(transcript: str, audio_seconds: float | None) -> dict:
    n = len(transcript.split())
    if not audio_seconds or audio_seconds <= 0:
        return {"words": n, "audio_seconds": audio_seconds, "wps": None, "plausible": None}
    wps = n / audio_seconds
    return {"words": n, "audio_seconds": round(audio_seconds, 2), "wps": round(wps, 2), "plausible": 0.3 <= wps <= 5.0}


def score(transcript: str, case: dict, previous: list[str], audio_seconds: float | None,
          corpus_df: dict[str, int] | None = None, n_docs: int = 1, cited_ids: set[str] | None = None) -> dict:
    s = specificity(transcript, case, corpus_df, n_docs, cited_ids)
    b = boilerplate(transcript, previous)
    p = pace(transcript, audio_seconds)
    # one number the examiner page shows; the parts stay stored so nobody has to trust the blend
    blend = round(max(0.0, s["specificity"] * (1 - b) * (0.5 if p["plausible"] is False else 1.0)), 3)
    return {**s, "boilerplate": b, "pace": p, "attestation_score": blend}
