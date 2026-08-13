"""Optional Streamlit dashboard over generated analysis records."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


OUTPUT = Path("output/analyses.jsonl")

st.set_page_config(page_title="Voice of Customer", page_icon="🎧", layout="wide")
st.title("Voice of Customer Intelligence")
st.caption("Privacy-first conversation analytics · synthetic demonstration data")

if not OUTPUT.exists():
    st.error("Run `make analyze` before starting the dashboard.")
    st.stop()

records = [json.loads(line) for line in OUTPUT.read_text(encoding="utf-8").splitlines() if line]
rows = [
    {
        "call_id": record["call_id"],
        "started_at": record["started_at"],
        "channel": record["channel"],
        **record["analysis"],
        "redactions": sum(record["pii_redactions"].values()),
    }
    for record in records
]
frame = pd.DataFrame(rows)

metrics = st.columns(4)
metrics[0].metric("Conversations", f"{len(frame):,}")
metrics[1].metric("Negative sentiment", f"{(frame.sentiment == 'negative').mean():.1%}")
metrics[2].metric("Escalation risk", f"{frame.escalation_risk.mean():.1%}")
metrics[3].metric("PII values removed", f"{frame.redactions.sum():,}")

left, right = st.columns(2)
topic_counts = frame.topic.value_counts().rename_axis("topic").reset_index(name="calls")
left.plotly_chart(
    px.bar(topic_counts, x="calls", y="topic", orientation="h", title="Top contact drivers"),
    use_container_width=True,
)
sentiment = frame.groupby(["topic", "sentiment"]).size().reset_index(name="calls")
right.plotly_chart(
    px.bar(sentiment, x="topic", y="calls", color="sentiment", title="Sentiment by driver"),
    use_container_width=True,
)

st.subheader("High-priority review queue")
st.dataframe(
    frame.loc[frame.escalation_risk, ["call_id", "started_at", "topic", "sentiment", "policy_flags"]],
    use_container_width=True,
    hide_index=True,
)

