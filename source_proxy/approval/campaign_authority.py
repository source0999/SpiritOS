from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = "/home/source/SpiritOS-campaign-1-20260712"
REPOSITORY = "SpiritOS"
SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "approval-authority.py"


class CampaignApprovalError(ValueError):
    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def coding_target_plugin(target: str) -> str:
    normalized = target.replace("\\", "/").strip()
    if normalized.startswith("tests/ui-agent-trials/fixtures/dummy-product-site/"):
        return "dummy-product-site"
    return "coding-shell"


def coding_content_hash(*, task_id: str, action: str, approved_diff: str, target: str, selected_prompt_id: str, context_hash: str) -> str:
    return hashlib.sha256(canonical_json({
        "approved_diff": approved_diff,
        "context_hash": context_hash,
        "selected_prompt_id": selected_prompt_id,
        "target": target,
        "task_id": task_id,
    }).encode("utf-8")).hexdigest()


def current_head() -> str:
    return subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"], text=True).strip()


def _call(command: str, payload: dict[str, Any]) -> dict[str, Any]:
    completed = subprocess.run(["python3", str(SCRIPT), command], input=json.dumps(payload), text=True, capture_output=True, check=False)
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise CampaignApprovalError("approval_issuer_unavailable") from error
    if completed.returncode != 0:
        raise CampaignApprovalError(str(response.get("reason") or "approval_issuer_unavailable"))
    return response


def consume_coding_execution_approval(*, approval_id: str, task_id: str, action: str, approved_diff: str, target: str, selected_prompt_id: str, context_hash: str) -> dict[str, Any]:
    approval = _call("lookup", {"approval_id": approval_id})
    if approval.get("consumer") != "coding-executor":
        raise CampaignApprovalError("approval_consumer_mismatch")
    if approval.get("operation") != "coding_execution":
        raise CampaignApprovalError("approval_operation_not_permitted")
    if approval.get("context") != context_hash:
        raise CampaignApprovalError("approval_context_mismatch")
    plugin = coding_target_plugin(target)
    content_hash = coding_content_hash(task_id=task_id, action=action, approved_diff=approved_diff, target=target, selected_prompt_id=selected_prompt_id, context_hash=context_hash)
    binding = {
        "approval_id": approval_id,
        "consumer": "coding-executor",
        "operation": "coding_execution",
        "repository": REPOSITORY,
        "worktree": ROOT,
        "root": ROOT,
        "target": target,
        "plugin": plugin,
        "preview": approval.get("preview"),
        "content_hash": content_hash,
        "context": context_hash,
        "source_head": current_head(),
        "generation": str(approval.get("generation") or ""),
    }
    _call("consume", binding)
    return {"approval_id": approval_id, "generation": int(approval["generation"]), "plugin": plugin, "binding": binding}


def persist_coding_execution_preview(*, task_id: str, action: str, approved_diff: str, target: str, selected_prompt_id: str, context_hash: str) -> dict[str, Any]:
    content_hash = coding_content_hash(task_id=task_id, action=action, approved_diff=approved_diff, target=target, selected_prompt_id=selected_prompt_id, context_hash=context_hash)
    return _call("persist-preview", {
        "repository": REPOSITORY, "worktree": ROOT, "root": ROOT,
        "target": target, "plugin": coding_target_plugin(target),
        "content_hash": content_hash, "context": context_hash, "source_head": current_head(),
    })


def issue_coding_execution_approval(*, preview_id: str, expected_generation: int | None = None) -> dict[str, Any]:
    if expected_generation is None:
        expected_generation = int(_call("lookup-preview", {"preview_id": preview_id})["generation"])
    issued = _call("issue", {
        "preview_id": preview_id,
        "expected_generation": str(expected_generation),
        "consumer": "coding-executor",
        "operation": "coding_execution",
        "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
    })
    return {
        "approval_id": str(issued["approval_id"]),
        "generation": int(issued["generation"]),
        "state": str(issued["state"]),
    }


def resolve_coding_execution_preview(*, preview_id: str, expected_generation: int) -> dict[str, Any]:
    preview = _call("lookup-preview", {"preview_id": preview_id})
    if str(preview.get("generation")) != str(expected_generation):
        raise CampaignApprovalError("approval_generation_mismatch")
    if preview.get("state") != "previewed":
        raise CampaignApprovalError("approval_not_approved")
    if preview.get("repository") != REPOSITORY or preview.get("worktree") != ROOT or preview.get("root") != ROOT:
        raise CampaignApprovalError("approval_worktree_mismatch")
    if preview.get("source_head") != current_head():
        raise CampaignApprovalError("approval_source_mismatch")
    return preview


def reject_coding_execution_preview(*, preview_id: str, expected_generation: int) -> dict[str, Any]:
    resolve_coding_execution_preview(preview_id=preview_id, expected_generation=expected_generation)
    return _call("transition-preview", {"preview_id": preview_id, "expected_generation": str(expected_generation), "state": "rejected"})


def cancel_coding_execution_approval(*, approval_id: str) -> dict[str, Any]:
    approval = _call("lookup", {"approval_id": approval_id})
    state = str(approval.get("state") or "")
    if state == "approved":
        _call("transition", {"approval_id": approval_id, "state": "cancelled"})
        state = "cancelled"
    return {"approval_id": approval_id, "generation": int(approval["generation"]), "state": state}


def finalize_coding_execution_approval(approval: dict[str, Any], *, result_id: str, evidence: dict[str, Any], status: str) -> dict[str, Any]:
    binding = dict(approval["binding"])
    binding.update({"result_id": result_id, "evidence": canonical_json(evidence), "status": status, "source_head": current_head()})
    return _call("finalize", binding)
