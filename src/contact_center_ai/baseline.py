"""Transparent offline baseline for testing the analytics contract without an API key."""

from __future__ import annotations

import re

from .models import Analysis


TOPIC_TERMS: dict[str, tuple[str, ...]] = {
    "payment": ("payment", "autopay", "paid", "due date", "late fee", "payoff"),
    "billing": ("bill", "statement", "charged", "charge", "balance", "amount"),
    "account_access": ("log in", "login", "password", "locked out", "verification code"),
    "fraud": ("fraud", "not mine", "unauthorized", "identity theft", "stolen"),
    "vehicle_title": ("title", "registration", "lien release", "dmv"),
    "dealer_experience": ("dealer", "dealership", "salesperson", "delivery"),
    "cancellation": ("cancel", "close my account", "terminate", "return the vehicle"),
}

NEGATIVE_TERMS = (
    "angry",
    "frustrated",
    "upset",
    "terrible",
    "unacceptable",
    "still not",
    "never",
    "wrong",
    "complaint",
)
POSITIVE_TERMS = ("thank you", "thanks", "great", "helpful", "resolved", "perfect")
URGENCY_TERMS = ("urgent", "immediately", "today", "right now", "emergency", "asap")
ESCALATION_TERMS = ("supervisor", "manager", "lawyer", "regulator", "complaint", "attorney")
RESOLUTION_TERMS = ("resolved", "fixed", "completed", "all set", "that works", "thank you")
POLICY_TERMS = {
    "legal_threat": ("lawyer", "attorney", "sue"),
    "regulatory_complaint": ("regulator", "cfpb", "attorney general"),
    "financial_hardship": ("hardship", "lost my job", "cannot afford", "can't afford"),
}


def _phrase_count(text: str, phrases: tuple[str, ...]) -> int:
    return sum(len(re.findall(re.escape(phrase), text)) for phrase in phrases)


class BaselineAnalyzer:
    """Deterministic analyzer useful for CI, fallbacks, and LLM quality comparisons."""

    version = "rules-v1.0"

    def analyze(self, text: str) -> Analysis:
        lowered = text.lower()
        scores = {topic: _phrase_count(lowered, terms) for topic, terms in TOPIC_TERMS.items()}
        topic, top_score = max(scores.items(), key=lambda item: (item[1], item[0]))
        if top_score == 0:
            topic = "other"

        negative = _phrase_count(lowered, NEGATIVE_TERMS)
        positive = _phrase_count(lowered, POSITIVE_TERMS)
        if negative > positive:
            sentiment = "negative"
        elif positive > negative:
            sentiment = "positive"
        else:
            sentiment = "neutral"

        urgent = _phrase_count(lowered, URGENCY_TERMS) > 0
        escalation = _phrase_count(lowered, ESCALATION_TERMS) > 0
        resolved = _phrase_count(lowered, RESOLUTION_TERMS) > 0 and "not resolved" not in lowered
        flags = [
            flag
            for flag, terms in POLICY_TERMS.items()
            if _phrase_count(lowered, terms) > 0
        ]
        drivers = [term for term in TOPIC_TERMS.get(topic, ()) if term in lowered][:3]
        margin = top_score - sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else top_score
        confidence = 0.55 if top_score == 0 else min(0.96, 0.68 + 0.08 * top_score + 0.04 * margin)

        return Analysis(
            topic=topic,
            sentiment=sentiment,
            urgency="high" if urgent or escalation else "normal",
            resolved=resolved,
            escalation_risk=escalation or (negative >= 2 and not resolved),
            drivers=drivers,
            confidence=round(confidence, 3),
            analyzer_version=self.version,
            policy_flags=flags,
        )

