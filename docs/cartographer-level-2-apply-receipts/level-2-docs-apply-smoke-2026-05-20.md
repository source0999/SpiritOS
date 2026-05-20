# Cartographer Level 2 Apply Receipt

```json
{
  "actions_taken": true,
  "apply_requires_human_approval": true,
  "approval_actor": "Britton",
  "approval_id": "approval-level-2-docs-apply-smoke-2026-05-20",
  "approval_timestamp": "2026-05-20T02:40:00Z",
  "approval_validated": true,
  "audit_receipt_written": true,
  "blocker_reasons": [],
  "branch_allowed": false,
  "branch_created": false,
  "cartographer_self_approval": false,
  "cleanup_allowed": false,
  "commit_allowed": false,
  "commit_created": false,
  "committed": false,
  "created_at": "2026-05-20T02:34:50Z",
  "delete_allowed": false,
  "diff_check_after": {
    "ok": true,
    "summary": "git diff --check passed"
  },
  "diff_check_before": {
    "ok": true,
    "summary": "patch check passed"
  },
  "dirty_status_after": [
    "_blueprints/proposals/approved/level-2-docs-apply-smoke-2026-05-20.json",
    "docs/cartographer-level-2-apply-smoke.md"
  ],
  "dirty_status_before": [
    "_blueprints/proposals/approved/level-2-docs-apply-smoke-2026-05-20.json"
  ],
  "files_allowed": [
    "docs/cartographer-level-2-apply-smoke.md"
  ],
  "files_blocked": [],
  "files_requested": [
    "docs/cartographer-level-2-apply-smoke.md"
  ],
  "files_written": [
    "docs/cartographer-level-2-apply-smoke.md",
    "docs/cartographer-level-2-apply-receipts/level-2-docs-apply-smoke-2026-05-20.md"
  ],
  "forbidden_paths_detected": [],
  "git_head_after": "73b3daf6b72391a83513a60782a30db693f5869e",
  "git_head_before": "73b3daf6b72391a83513a60782a30db693f5869e",
  "head_changed": false,
  "level": 2,
  "manual_check_commands": [
    "git diff --check -- docs/cartographer-level-2-apply-smoke.md docs/cartographer-level-2-apply-receipts/level-2-docs-apply-smoke-2026-05-20.md"
  ],
  "mode": "approved_docs_apply",
  "proposal_id": "level-2-docs-apply-smoke-2026-05-20",
  "push_allowed": false,
  "push_created": false,
  "pushed": false,
  "receipt_path": "docs/cartographer-level-2-apply-receipts/level-2-docs-apply-smoke-2026-05-20.md",
  "result": "applied",
  "rollback_command": "git restore docs/cartographer-level-2-apply-smoke.md docs/cartographer-level-2-apply-receipts/level-2-docs-apply-smoke-2026-05-20.md",
  "schema_version": "cartographer.level_2.apply_receipt.v1",
  "self_promotion_allowed": false,
  "source_code_allowed": false,
  "status": "applied",
  "write_actions_enabled": true
}
```
