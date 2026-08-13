"""Typed data contracts for transcript analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Transcript:
    call_id: str
    started_at: str
    channel: str
    text: str


@dataclass
class Analysis:
    topic: str
    sentiment: str
    urgency: str
    resolved: bool
    escalation_risk: bool
    drivers: list[str]
    confidence: float
    analyzer_version: str
    policy_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Analyzer(Protocol):
    """Stable contract implemented by the offline baseline or an injected LLM."""

    def analyze(self, text: str) -> Analysis:
        ...

