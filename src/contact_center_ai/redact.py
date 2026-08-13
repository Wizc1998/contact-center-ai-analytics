"""Deterministic PII redaction applied before any model boundary."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RedactionResult:
    text: str
    counts: dict[str, int]


PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("EMAIL", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("SSN", re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")),
    (
        "PHONE",
        re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?!\d)"),
    ),
    ("PAYMENT_CARD", re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")),
    ("ACCOUNT", re.compile(r"\b(?:account|acct)\s*(?:number|no\.?|#)?\s*[:#-]?\s*[A-Z0-9]{6,20}\b", re.I)),
)


def redact_pii(text: str) -> RedactionResult:
    counts: dict[str, int] = {}
    redacted = text
    for label, pattern in PATTERNS:
        redacted, count = pattern.subn(f"[{label}]", redacted)
        if count:
            counts[label] = count
    return RedactionResult(redacted, counts)

