#!/usr/bin/env python3
"""Fail closed when Campaign 1 authority boundaries drift."""

import ast
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
    "src/lib/coding/design-approval-authority.ts": ("resolveDesignWritebackPreview", "expected_generation", "approval_generation_mismatch"),
    "src/app/v1/operator/design-approval/route.ts": ("requireOperatorSession", "resolveDesignWritebackPreview", "operator_client_authority_binding_forbidden"),
    "src/lib/coding/agent-lab-baseline-server.ts": ("operator_issuance_required_for_agent_lab_cleanup",),
    "src/components/coding/CodingAgentInterface.tsx": (
        "allowed_files: allowedFiles",
    ),
    "source_proxy/cartographer/proposal_transfer.py": (
        '"authority": "proposal_only"',
        '"approval_issuer_authority": False',
        '"git_authority": False',
        '"queue_authority": False',
        '"write_authority": False',
    ),
}
FORBIDDEN = {
    "src/app/v1/actions/execute-approved/route.ts": ("approvalIdForApprovedDiff({", "approved: true"),
    "source_proxy/api/long_running_tasks.py": ("async def long_running_task_approval(", "    approved: bool"),
    "source_proxy/cartographer/apply.py": ("approval_id_for_approved_diff(",),
    "src/lib/coding/agent-lab-baseline-server.ts": ("approvalIdForApprovedDiff",),
    "source_proxy/api/cartographer.py": (
        '@router.get("/safe-write")',
        '@router.post("/safe-write")',
        '@router.get("/verification/run")',
        '@router.post("/verification/run")',
        "from source_proxy.cartographer.safe_write import",
        "from source_proxy.cartographer.verification_runner import",
        "approve_git_queue_item",
        "apply_cartographer_clutter_proposal",
        "run_cartographer_docs_autopilot_apply",
        "run_cartographer_level_2_docs_apply",
        "write_cartographer_starter_blueprints",
    ),
}


def cartographer_registration_failures() -> list[str]:
    path = ROOT / "source_proxy/api/cartographer.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    registrations: set[tuple[str, str]] = set()
    failures: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            if decorator.func.attr not in {"get", "post", "put", "delete", "patch"} or not decorator.args:
                continue
            argument = decorator.args[0]
            if not isinstance(argument, ast.Constant) or not isinstance(argument.value, str):
                continue
            registration = (decorator.func.attr.upper(), argument.value)
            if registration in registrations:
                failures.append(f"duplicate_cartographer_registration:{registration[0]}:{registration[1]}")
            registrations.add(registration)
    return failures


def main() -> int:
    failures: list[str] = []
    for relative, markers in REQUIRED.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        failures.extend(f"missing:{relative}:{marker}" for marker in markers if marker not in text)
    for relative, markers in FORBIDDEN.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        failures.extend(f"forbidden:{relative}:{marker}" for marker in markers if marker in text)
    failures.extend(cartographer_registration_failures())
    if failures:
        print("CAMPAIGN_1_AUTHORITY_INVALID")
        print("\n".join(failures))
        return 1
    print("CAMPAIGN_1_AUTHORITY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
