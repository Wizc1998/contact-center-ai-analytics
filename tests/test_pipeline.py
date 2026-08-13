from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from contact_center_ai.baseline import BaselineAnalyzer
from contact_center_ai.evaluation import evaluate_topics
from contact_center_ai.pipeline import analyze_file
from contact_center_ai.redact import redact_pii


class RedactionTest(unittest.TestCase):
    def test_sensitive_values_are_removed_before_analysis(self) -> None:
        source = (
            "Email me at alex@example.test or call 214-555-0199. "
            "SSN 123-45-6789 and card 4111 1111 1111 1111."
        )
        result = redact_pii(source)
        self.assertNotIn("alex@example.test", result.text)
        self.assertNotIn("214-555-0199", result.text)
        self.assertNotIn("123-45-6789", result.text)
        self.assertNotIn("4111", result.text)
        self.assertEqual(result.counts, {"EMAIL": 1, "SSN": 1, "PHONE": 1, "PAYMENT_CARD": 1})


class AnalyzerTest(unittest.TestCase):
    def test_baseline_returns_operational_fields(self) -> None:
        result = BaselineAnalyzer().analyze(
            "I am frustrated. This payment is still not posted. I need a supervisor today."
        )
        self.assertEqual(result.topic, "payment")
        self.assertEqual(result.sentiment, "negative")
        self.assertEqual(result.urgency, "high")
        self.assertTrue(result.escalation_risk)
        self.assertFalse(result.resolved)

    def test_batch_pipeline_emits_redacted_records_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "calls.jsonl"
            row = {
                "call_id": "CALL-1",
                "started_at": "2026-07-15T10:00:00Z",
                "channel": "phone",
                "text": "My payment is wrong. Email me at alex@example.test.",
            }
            source.write_text(json.dumps(row) + "\n", encoding="utf-8")
            output, summary = analyze_file(source, root / "output")
            emitted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(summary["processed"], 1)
            self.assertEqual(summary["pii_redactions"], {"EMAIL": 1})
            self.assertNotIn("alex@example.test", emitted["redacted_text"])
            self.assertEqual(emitted["analysis"]["topic"], "payment")

    def test_evaluation_is_reproducible(self) -> None:
        evaluation_path = Path(__file__).parents[1] / "data" / "evaluation_set.jsonl"
        report = evaluate_topics(evaluation_path)
        self.assertEqual(report["records"], 14)
        self.assertGreaterEqual(report["accuracy"], 0.85)
        self.assertGreaterEqual(report["macro_f1"], 0.85)


if __name__ == "__main__":
    unittest.main()

