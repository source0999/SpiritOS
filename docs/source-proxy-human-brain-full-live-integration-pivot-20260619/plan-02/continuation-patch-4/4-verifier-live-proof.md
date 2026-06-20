# Browser / Functional Verifier Live Proof

Goal: verifier GO cannot be advisory, preview-only, packet-only, or UNVERIFIED.

Implementation:

- Added `run_live_functional_verifier` in `source_proxy/decision/verifier_lane.py`.
- The verifier checks a real disposable Patch 4 HTML target under the external evidence directory.
- It returns `VERIFIED` or `FAILED_NEEDS_FIX`.
- It always reports `advisory_only=false`, `preview_only=false`, and `unverified=false` for the live path.

Live proof:

- task: task_9b6323805e3e
- status: INTEGRATED_LIVE
- live_invocation: true
- verification_result: VERIFIED
- advisory_only: false
- preview_only: false
- unverified: false
- downstream_consumed: true
- trace_id: trace_2e80e5b5e5dc4304
- invocation_event_id: invocation_9378704e31ae47d3
- consumer_event_id: consumer_07ebf8bfe29b46fe
- target_path: /home/source/spiritos-evidence/plan-02-continuation-patch-4/task-a-verifier-target-task_9b6323805e3e.html

Failure behavior:

- Missing target, missing required text, missing interactive marker, advisory/preview verifier output, or UNVERIFIED result prevents specialist GO.
