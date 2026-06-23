# F02 Evidence Summary

Updated: 2026-06-22T02:43:43+00:00

## Isolation
- cleanup worktree: `/home/source/SpiritOS-cleanup-20260621`
- cleanup branch: `cleanup/full-repo-20260621`
- starting HEAD: `b483cc5c7b769b45f6c3be4a25dca9dde4ccad4e`

## Contract freeze
- command: `sha256sum F02/acceptance-contract.json F02/holdout-manifest.json`
- acceptance hash: `1f9ccaeaa823e3a019b517feda24416f312ef1af05fbbe24a89b9d944a1b4052`
- holdout hash: `fc86ba510f92dbaa256ede9d6f27b3f697deb097da04dbeaf065147691563aeb`
- JSON parse: PASS for both artifacts.
- contract changed after freeze: no.

## Baseline before source edits
- `git status --branch --short --untracked-files=normal`: branch
  `cleanup/full-repo-20260621`; only F02 `status.json` modified for freeze record.
- path existence:
  - `source_proxy/verification`: present.
  - `source_proxy/verification/anticheat`: absent before F2 implementation.
  - `source_proxy/tests`: present.
  - `source_proxy/diagnostics/status_codes.py`: present from F1.
- `python3 -m pytest source_proxy/tests/test_status_codes.py -q`: BLOCKED_ENV,
  `/usr/bin/python3: No module named pytest`.
- shared-venv baseline: PASS, `15 passed`.

## Implementation evidence
- New package: `source_proxy/verification/anticheat/`.
- Detector registry catches all 15 frozen negative-corpus patterns.
- Positive grounded evidence control passes.
- Copied legacy parity surface matches new registry on shared corpus.
- Set A runner imports registry additively; no Set A execution occurred.
- Existing `source_proxy/verification/contracts.py`, `deterministic.py`, `diff.py`,
  and `__init__.py` were not modified.

## Test evidence
- `/home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_anticheat_registry.py -q`: PASS, `6 passed`.
- `/home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_status_codes.py -q`: PASS, `15 passed`.
- F1/F2 focused suite: PASS, `115 passed, 2 skipped`.
- Optional verification-contract subset: one environment failure, Node cannot
  resolve `typescript` from temp dir; not counted as F2 failure.
- `timeout 300 /home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest source_proxy/tests -q`: TIMEOUT, exit 124, not counted as PASS.
- `bash docs/spiritos-full-repo-cleanup-20260621/F02/operator-check.sh`: PASS.
- `git diff --check`: PASS.

## Anti-cheat / safety
- canned outputs flagged: yes.
- static sources labeled live flagged: yes.
- status ping behavior proof flagged: yes.
- repo context as internet flagged: yes.
- fixture/mock as live flagged: yes.
- fallback primary success flagged: yes.
- renderer substance flagged: yes.
- manual PASS/JSON flip flagged: yes.
- unavailable provider success flagged: yes.
- summary/raw contradiction flagged: yes.
- benchmark-specific runtime branch flagged: yes.
- test-only production branch flagged: yes.
- `fake_go_detected` changed: no.
- protected paths changed: no.
- API/cloud call: no.
- push/merge: no.
