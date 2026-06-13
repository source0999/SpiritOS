# Baseline Check

Run date: 2026-06-12

Scope: Source Proxy remaining levels 3 through 8, hard manual GO gates.

## Current Repository State

`git status --branch --short --untracked-files=normal`:

```text
## master
 M source_proxy/api/decision.py
 M source_proxy/decision/human_messy_homepage.py
 M source_proxy/decision/task_spec_intake.py
 M source_proxy/decision/tool_action_loop.py
 M source_proxy/tests/test_coding_regression_pack.py
?? docs/evidence/source-proxy-expectation-scoring-advanced-diagnostics-20260612/
?? docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/
?? docs/evidence/source-proxy-level-2-scoring-reporting-hardening-20260612/
?? docs/evidence/source-proxy-multi-model-brain-foundation-20260612/
?? docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/
?? docs/evidence/source-proxy-v0.2-artifact-repair-plan/
?? docs/evidence/source-proxy-v0.2-proof-diagnostic-rerun-20260612/
?? docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/
?? docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/
?? docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/
?? docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/
?? source_proxy/decision/artifact_behavior_contract.py
?? source_proxy/decision/artifact_final_verdict.py
?? source_proxy/decision/artifact_handoff_packet.py
?? source_proxy/decision/artifact_preview_resolution.py
?? source_proxy/decision/artifact_repair_contract.py
?? source_proxy/decision/artifact_repair_loop.py
?? source_proxy/decision/artifact_retest_result.py
?? source_proxy/decision/cartographer_routing.py
?? source_proxy/decision/expectation_reporting.py
?? source_proxy/decision/expectation_scoring.py
?? source_proxy/decision/model_lanes.py
?? source_proxy/decision/verifier_lane.py
?? source_proxy/tests/test_artifact_behavior_contract.py
?? source_proxy/tests/test_artifact_final_verdict.py
?? source_proxy/tests/test_artifact_handoff_packet.py
?? source_proxy/tests/test_artifact_preview_resolution.py
?? source_proxy/tests/test_artifact_repair_contract.py
?? source_proxy/tests/test_artifact_repair_loop.py
?? source_proxy/tests/test_artifact_retest_result.py
?? source_proxy/tests/test_cartographer_routing.py
?? source_proxy/tests/test_expectation_reporting.py
?? source_proxy/tests/test_expectation_scoring.py
?? source_proxy/tests/test_model_lane_observability.py
?? source_proxy/tests/test_model_lane_preview_api.py
?? source_proxy/tests/test_model_lanes.py
?? source_proxy/tests/test_task_spec_intake_unseen_artifacts.py
?? source_proxy/tests/test_verifier_lane.py
```

`git diff --stat`:

```text
 source_proxy/api/decision.py                      | 10 ++++
 source_proxy/decision/human_messy_homepage.py     | 61 +++++++++++++++++++++++
 source_proxy/decision/task_spec_intake.py         | 14 +++++-
 source_proxy/decision/tool_action_loop.py         |  1 +
 source_proxy/tests/test_coding_regression_pack.py | 54 ++++++++++++++++++++
 5 files changed, 138 insertions(+), 2 deletions(-)
```

Git warned that several tracked files would have LF replaced by CRLF the next time Git touches them. No line-ending normalization was performed.

`git worktree list`:

```text
//10.0.0.186/SpiritOS de9e59db [master]
```

## Evidence Root Inventory

Requested evidence root was missing before this packet:

```text
MISSING: docs/evidence/source-proxy-remaining-levels-daily-driver-readiness-20260612
```

Relevant existing Source Proxy evidence roots include:

```text
source-proxy-general-intelligence-diagnostic-20260612
source-proxy-level-2-scoring-reporting-hardening-20260612
source-proxy-tool-action-runtime-v1
source-proxy-context-orchestration-master-plan
source-proxy-v0.2-artifact-repair-plan
```

## Level 2 Anchor

Existing Level 2 packet reviewed:

```text
docs/evidence/source-proxy-level-2-scoring-reporting-hardening-20260612/final-summary.md
```

Observed Level 2 claims:

- Initial verdict counts: `{'WEAK_PASS': 10}`
- Verified verdict counts: `{'PASS': 10}`
- Initial live scores remain separate from verified behavior-backed scores.
- The packet explicitly says not to proceed to live verifier sidecars, autonomy, or benchmark expansion from Level 2 alone.

## Relevant Files Located

Relevant route, scorer, model-lane, verifier, and Cartographer files are present under:

```text
source_proxy/api/decision.py
source_proxy/decision/human_messy_homepage.py
source_proxy/decision/task_spec_intake.py
source_proxy/decision/tool_action_loop.py
source_proxy/decision/tool_actions.py
source_proxy/decision/tool_action_executor.py
source_proxy/decision/expectation_scoring.py
source_proxy/decision/expectation_reporting.py
source_proxy/decision/model_lanes.py
source_proxy/decision/verifier_lane.py
source_proxy/decision/cartographer_routing.py
source_proxy/cartographer/
source_proxy/tests/
```

## Dirty State Conclusion

The repo is already dirty before Level 3. Level 3 must preserve the existing dirty work and must not silently mutate unrelated files. Any Level 3 execution should use tightly bounded test tasks, capture before/after diffs, and prove clean revert behavior without staging, committing, stashing, resetting, checkout, or clean.
