# Gate A Terminal Verification

Status: complete.

Commands required for this Gate A pack:

```powershell
python -m json.tool docs/evidence/source-proxy-level-3-semantic-generalization-gate-a-20260613/mini-context-pack.json
python -c "import xml.etree.ElementTree as ET; ET.parse('docs/evidence/source-proxy-level-3-semantic-generalization-gate-a-20260613/mini-context-pack.xml')"
test -s docs/evidence/source-proxy-level-3-semantic-generalization-gate-a-20260613/index.md
test -s docs/evidence/source-proxy-level-3-semantic-generalization-gate-a-20260613/decision-boundary-map.md
test -s docs/evidence/source-proxy-level-3-semantic-generalization-gate-a-20260613/semantic-routing-test-plan.md
test -s docs/evidence/source-proxy-level-3-semantic-generalization-gate-a-20260613/behavior-repair-diagnosis.md
git diff --check -- docs/evidence/source-proxy-level-3-semantic-generalization-gate-a-20260613
git status --branch --short --untracked-files=normal
```

## Results

- `python -m json.tool docs/evidence/source-proxy-level-3-semantic-generalization-gate-a-20260613/mini-context-pack.json`: PASS.
- `python -c "import xml.etree.ElementTree as ET; ET.parse('docs/evidence/source-proxy-level-3-semantic-generalization-gate-a-20260613/mini-context-pack.xml')"`: PASS.
- POSIX `test -s ...`: not available from this PowerShell/Windows mapped-drive session. `Get-Command test` returned no command, and `bash -lc` failed because `/bin/bash` was not available for `Z:\`.
- Equivalent PowerShell file length checks: PASS.
  - `index.md`: 1653 bytes.
  - `decision-boundary-map.md`: 10102 bytes.
  - `semantic-routing-test-plan.md`: 8491 bytes.
  - `behavior-repair-diagnosis.md`: 7898 bytes.
- `git diff --check -- docs/evidence/source-proxy-level-3-semantic-generalization-gate-a-20260613`: PASS.
- `git status --branch --short --untracked-files=normal`: ran. The repo had pre-existing dirty Source Proxy/runtime/evidence files, and this Gate A evidence folder appears as untracked.

No browser holdout, model generation, repair loop, Level 4, sidecar, verifier lane, cloud fallback, or new prompt batch was run.
