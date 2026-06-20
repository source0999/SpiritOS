# Hardline Classifier

Implemented: `source_proxy/decision/hardline_integration.py`

The classifier rejects GO-like labels for:

- preview-only output
- advisory-only output
- status-only output
- read-only-for-action Mac proof
- unconsumed output
- mock-only proof
- fixture-only proof
- blocked environment
- blocked human step
- needs-fix output

Focused proof:

`source_proxy/tests/test_hardline_integration.py`

Result:

`13 passed` in the first focused Python run, then `14 passed` after adding the specialist failed-lane regression test.
