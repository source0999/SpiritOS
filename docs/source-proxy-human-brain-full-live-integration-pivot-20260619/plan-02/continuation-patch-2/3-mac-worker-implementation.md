# Mac Worker Implementation

Dell-side implementation patched:

- `scripts/mac-worker/spirit_mac_worker.py`
- `source_proxy/tests/test_mac_worker_script.py`
- `source_proxy/tests/test_hardline_integration.py`

Implemented behavior:

- Supports `mac_isolated_write_proof`.
- Requires `trace_id`.
- Requires `invocation_event_id`.
- Requires `task_id`.
- Requires `consumer_subsystem`.
- Restricts proof directory to the Mac temp root.
- Rejects unsafe `proof_dir` and `proof_path`.
- Writes one disposable proof file.
- Reads and verifies file contents.
- Computes checksum/content marker.
- Cleans up proof file and removes proof directory when possible.
- Returns structured success/failure result.

Focused test result:

`PASS: 20 passed`

Live Mac status:

Not synced. See `2-mac-worker-diff-and-safety.md`.
