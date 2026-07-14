#!/usr/bin/env python3
"""Fail closed when Campaign 1 authority boundaries drift."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "source_proxy/tasks/long_running.py": (
        "consume_coding_execution_approval",
        "finalize_coding_execution_approval",
        "validate_coding_approval_evidence",
        "cancel_coding_execution_approval",
        "campaign_1_pending_approval",
    ),
    "source_proxy/cartographer/apply.py": ("forbidden_cartographer_mutation",),
    "source_proxy/cartographer/git_approvals.py": ("forbidden_cartographer_mutation",),
    "src/app/v1/actions/execute-approved/route.ts": (
        "operator-issued approval_id",
        "selected_prompt_id",
        "context_hash",
        "approval_operator_issuance_required",
    ),
    "source_proxy/api/long_running_tasks.py": (
        "LongRunningTaskOperatorApprovalRequest",
        "issue_coding_execution_approval",
        "record_coding_execution_approval",
        "verify_operator_approval_assertion",
        '@router.post("/long-running/{task_id}/operator-approval")',
        "approval_client_authority_removed",
    ),
    "source_proxy/approval/operator_session.py": ("verify_operator_approval_assertion", "operator_session_revoked"),
    "src/app/v1/operator/approval/route.ts": ("requireOperatorSession", "createOperatorApprovalAssertion", "operator_client_authority_binding_forbidden"),
    "src/components/coding/CodingAgentInterface.tsx": (
        "allowed_files: allowedFiles",
    ),
}
FORBIDDEN = {
    "src/app/v1/actions/execute-approved/route.ts": ("approvalIdForApprovedDiff({", "approved: true"),
    "source_proxy/api/long_running_tasks.py": ("async def long_running_task_approval(",),
    "source_proxy/cartographer/apply.py": ("approval_id_for_approved_diff(",),
    "src/lib/coding/agent-lab-baseline-server.ts": ("approvalIdForApprovedDiff",),
}


def main() -> int:
    failures: list[str] = []
    for relative, markers in REQUIRED.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        failures.extend(f"missing:{relative}:{marker}" for marker in markers if marker not in text)
    for relative, markers in FORBIDDEN.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        failures.extend(f"forbidden:{relative}:{marker}" for marker in markers if marker in text)
    if failures:
        print("CAMPAIGN_1_AUTHORITY_INVALID")
        print("\n".join(failures))
        return 1
    print("CAMPAIGN_1_AUTHORITY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
