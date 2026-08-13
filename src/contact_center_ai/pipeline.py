"""Batch transcript pipeline with privacy boundary and operational metrics."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .baseline import BaselineAnalyzer
from .models import Analyzer, Transcript
from .redact import redact_pii


REQUIRED_INPUT_FIELDS = {"call_id", "started_at", "channel", "text"}


def _parse_transcript(payload: dict[str, Any]) -> Transcript:
    missing = REQUIRED_INPUT_FIELDS - payload.keys()
    if missing:
        raise ValueError(f"Missing fields: {', '.join(sorted(missing))}")
    return Transcript(**{key: payload[key] for key in REQUIRED_INPUT_FIELDS})


def analyze_file(
    input_path: Path,
    output_dir: Path,
    analyzer: Analyzer | None = None,
) -> tuple[Path, dict[str, object]]:
    analyzer = analyzer or BaselineAnalyzer()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "analyses.jsonl"
    topics: Counter[str] = Counter()
    sentiments: Counter[str] = Counter()
    redactions: Counter[str] = Counter()
    escalations = 0
    processed = 0

    with input_path.open(encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as sink:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                transcript = _parse_transcript(json.loads(line))
            except (json.JSONDecodeError, TypeError, ValueError) as error:
                raise ValueError(f"Invalid input at line {line_number}: {error}") from error

            redaction = redact_pii(transcript.text)
            analysis = analyzer.analyze(redaction.text)
            trace_id = hashlib.sha256(
                f"{transcript.call_id}:{analyzer.__class__.__name__}".encode()
            ).hexdigest()[:16]
            record = {
                "trace_id": trace_id,
                "call_id": transcript.call_id,
                "started_at": transcript.started_at,
                "channel": transcript.channel,
                "redacted_text": redaction.text,
                "pii_redactions": redaction.counts,
                "analysis": analysis.to_dict(),
            }
            sink.write(json.dumps(record) + "\n")
            processed += 1
            topics[analysis.topic] += 1
            sentiments[analysis.sentiment] += 1
            redactions.update(redaction.counts)
            escalations += int(analysis.escalation_risk)

    summary: dict[str, object] = {
        "processed": processed,
        "topic_distribution": dict(topics.most_common()),
        "sentiment_distribution": dict(sentiments.most_common()),
        "pii_redactions": dict(redactions.most_common()),
        "escalation_rate": round(escalations / processed, 4) if processed else 0.0,
        "analyzer": analyzer.__class__.__name__,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return output_path, summary
