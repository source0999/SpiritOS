# Gate 2-J.6 Evidence Mapping

status: `GREEN`

`source_proxy/jcode/evidence.py` maps JCode NDJSON only when the raw stream is
valid JSON per line, sequence-contiguous, terminally sealed with
`run.completed`, and contains every reserved execution-result field. It hashes
the raw bytes before mapping. Any gap, malformed record, missing terminal
sentinel, or missing result field is `EVIDENCE_INCOMPLETE`.

The mapper explicitly reports that executor claims are not terminal truth and
lists the independently required Proxy checks: diff, protected-path policy,
tests, reviewer, verifier, anti-cheat, and terminal truth.

| Check | Result |
|---|---|
| Focused command | `python -m pytest -q source_proxy/tests/test_jcode_evidence.py source_proxy/tests/test_jcode_identity.py source_proxy/tests/test_jcode_supervision.py source_proxy/tests/test_jcode_network_bridge.py` |
| Result | `12 passed in 2.01s` |
| Provider/model/task invoked | no |

Gate 2-J.6 is complete. Gate 2-J.7 clean reproduction may begin.
