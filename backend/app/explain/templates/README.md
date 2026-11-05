# Answer templates

Approved text the service falls back to, and the only text it uses when no AI model is configured.
One YAML file per language. Arabic has none until its text is approved and reviewed, so Arabic
speakers get English with a note saying so.

**Rules:** `{fact}` is filled by code from the risk engine. A template never holds a number of its own.
`tests/unit/test_templates.py` runs every template through the same validators as AI output. Draft,
awaiting clinical review.
