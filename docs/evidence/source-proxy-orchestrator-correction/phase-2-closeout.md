# Source Proxy Orchestrator Correction Phase 2 Closeout

## Status

Phase 2 local/mocked Product verification executed.

No runtime changes, test changes, provider/model calls, benchmark prompts, real app trial mutations, staging, commits, pushes, branches, worktrees, stashes, resets, checkouts, or cleans were performed.

## Files Created

* `docs/evidence/source-proxy-orchestrator-correction/phase-2-product-verification-summary.md`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-product-vs-pure-comparison.md`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-no-cheat-assertion-summary.md`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-local-mocked-summary.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/product-homepage-receipt.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/product-homepage-score.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/product-homepage-transcript.txt`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/product-homepage.diff`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/pure-homepage-receipt.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/pure-homepage-score.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/pure-homepage-transcript.txt`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/pure-homepage.diff`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/markdown-artifact-receipt.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/markdown-artifact-score.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/markdown-artifact-transcript.txt`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/markdown-artifact.diff`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-blocked-case-receipts/json-wrong-extension-receipt.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-blocked-case-receipts/json-wrong-extension-score.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-blocked-case-receipts/json-wrong-extension-transcript.txt`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-blocked-case-receipts/json-wrong-extension.diff`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-closeout.md`

## Verification Commands And Results

Focused Product/Pure/local mocked regression:

```bash
source .venv/bin/activate
command -v python
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "task_spec_intake or tool_action or human_messy_homepage or messy_homepage or pure or artifact or protected or fake"
```

Result:

```text
/home/source/SpiritOS/.venv/bin/python
35 passed, 69 deselected in 12.82s
```

No-cheat/protected focused regression:

```bash
source .venv/bin/activate
command -v python
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "protected or fake or wrong_file or backend_authored or tool_action"
```

Result:

```text
/home/source/SpiritOS/.venv/bin/python
26 passed, 78 deselected in 10.09s
```

Smoke script inspection:

```bash
source .venv/bin/activate
python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --help
```

Result:

```text
usage: run-source-proxy-human-messy-homepage-smoke.py [-h] [--run] [--serve]
                                                      [--host HOST]
                                                      [--port PORT]
                                                      [--prompt PROMPT]
                                                      [--model-id MODEL_ID]
                                                      [--mode {product,pure}]
```

Decision:

* No smoke `--run` was executed because the script help does not expose a mocked fixture/model-call option.

Mocked receipt generation:

* Product homepage, Pure homepage, Product Markdown artifact, and JSON wrong-extension blocked receipts were generated through injected local `model_call` lambdas.
* No provider/model calls were made.
* All sample writes were under `docs/evidence/source-proxy-orchestrator-correction/`.

Diff check:

```bash
git diff --check
```

Result:

```text

```

The command exited 0 with no output.

Git status:

```bash
git status --branch --short --untracked-files=normal
```

Result:

```text
## master
 M docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/latest-run.json
 M docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/preview-url.txt
 M scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py
 M source_proxy/decision/human_messy_homepage.py
 M source_proxy/decision/task_spec_intake.py
 M source_proxy/decision/tool_action_executor.py
 M source_proxy/decision/tool_action_loop.py
 M source_proxy/tests/test_coding_regression_pack.py
?? docs/evidence/source-proxy-orchestrator-correction/
?? docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/pure-mode-phase-1/
?? docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/runs/20260611-223358/
```

## Verification Findings

GO:

* Product route receipts show generic artifact resolver metadata.
* Product homepage is no longer just a hidden exact-target bridge; `proxy_exact_target_suggested` is empty and `model_authored_targets` records `index.html`.
* Non-homepage Markdown artifact uses `markdown_document` artifact class and completes at the receipt/executor layer with model-authored `release-checklist.md`.
* Pure mode remains distinct as `pure_diagnostic`, with model path choice and benchmark eligibility.
* Wrong-extension JSON artifact is blocked with `target_not_allowed` and no files touched.
* No-cheat/protected regression slice passed.
* `git diff --check` is clean.

NO-GO / residual limitation:

* The legacy `human_messy_homepage` score still uses homepage-specific success criteria. It labels the completed Markdown artifact `NO-GO` because `openable_homepage_missing`, even though the receipt proves generic Product orchestration and model-authored content.
* Do not use the homepage smoke score as a universal Product artifact success label until a later approved scoring/evidence patch generalizes it.

## GO/NO-GO

GO for local/mocked Phase 2 verification of Product orchestration, Pure diagnostic separation, receipt provenance, and no-cheat protections.

NO-GO for live provider/model verification, benchmark execution, real app mutation, or scoring changes without a separate explicit approval.

## Blockers

No blocker for local/mocked Product orchestration verification.

Residual blocker for broader live/product rollout proof:

* Generic non-homepage artifact scoring needs a future approved scoring/evidence change or must rely on receipt-level success rather than the homepage smoke score.

## Next Title Only

Source Proxy Orchestrator Correction Phase 2 Scoring Generalization Approval
