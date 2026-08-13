.PHONY: analyze evaluate test dashboard clean

analyze:
	PYTHONPATH=src python -m contact_center_ai.cli analyze data/sample_calls.jsonl --output-dir output

evaluate:
	PYTHONPATH=src python -m contact_center_ai.cli evaluate data/evaluation_set.jsonl

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

dashboard:
	streamlit run app.py

clean:
	rm -rf output

