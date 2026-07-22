from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any

from source_proxy.approval.runtime_identity import resolve_authority_runtime_identity
from source_proxy.target_plugins.selection import (
    GENERIC_WORKSPACE_PLUGIN_ID,
    expected_target_plugin_id,
)


_RUNTIME_IDENTITY = resolve_authority_runtime_identity()
ROOT = str(_RUNTIME_IDENTITY.root)
REPOSITORY = _RUNTIME_IDENTITY.repository
CODING_EXECUTOR_LANE = "coder"


def coding_executor_consumer(lane_id: str) -> str:
    if lane_id != CODING_EXECUTOR_LANE:
        raise CampaignApprovalError("approval_lane_not_permitted")
    return f"coding-executor:{lane_id}"
SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "approval-authority.py"


class CampaignApprovalError(ValueError):
    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _target_plugin_binding(
    *, target: str, selected_prompt_id: str, identity: dict[str, Any] | None
) -> tuple[str, dict[str, Any]]:
    """Use a server-resolved adapter identity; never infer a fixture plugin from a path."""
    expected_plugin = expected_target_plugin_id(selected_prompt_id)
    if identity is None:
        if expected_plugin is not None:
            raise CampaignApprovalError("target_plugin_identity_missing")
        return "coding-shell", {}
    plugin = str(identity.get("plugin_id") or "").strip()
    if expected_plugin is None or plugin != expected_plugin:
        raise CampaignApprovalError("target_plugin_identity_mismatch")
    if str(identity.get("selected_prompt_id") or "") != selected_prompt_id:
        raise CampaignApprovalError("target_plugin_selected_prompt_mismatch")
    normalized_target = _normalize_scoped_path(target)
    if plugin == GENERIC_WORKSPACE_PLUGIN_ID:
        if normalized_target and not _path_matches_scope(
            normalized_target,
            identity.get("allowed_actions"),
        ):
            raise CampaignApprovalError("target_plugin_target_mismatch")
        _validate_generic_workspace_identity(identity)
    elif str(identity.get("fixture_root") or "") and not target.replace("\\", "/").startswith(str(identity["fixture_root"])):
        raise CampaignApprovalError("target_plugin_target_mismatch")
    if str(identity.get("source_head") or "") != current_head():
        raise CampaignApprovalError("target_plugin_source_head_mismatch")
    return plugin, dict(identity)


def _path_matches_scope(path: str, raw_scope: object) -> bool:
    if not isinstance(raw_scope, (list, tuple)):
        return False
    normalized = _normalize_scoped_path(path)
    if not normalized:
        return False
    for value in raw_scope:
        allowed = _normalize_scoped_path(str(value or ""), permit_glob=True)
        if not allowed:
            continue
        if allowed.endswith("/**"):
            prefix = allowed[:-3].rstrip("/")
            if normalized == prefix or normalized.startswith(prefix + "/"):
                return True
        elif allowed.endswith("/"):
            prefix = allowed.rstrip("/")
            if normalized == prefix or normalized.startswith(prefix + "/"):
                return True
        elif normalized == allowed:
            return True
    return False


def _normalize_scoped_path(value: str, *, permit_glob: bool = False) -> str:
    raw = str(value or "").replace("\\", "/").strip()
    while raw.startswith("./"):
        raw = raw[2:]
    if (
        not raw
        or raw.startswith("/")
        or "\x00" in raw
        or any(part in {"", ".", ".."} for part in PurePosixPath(raw).parts)
        or (not permit_glob and any(character in raw for character in "*?[]"))
    ):
        return ""
    return raw


def _validate_generic_workspace_identity(identity: dict[str, Any]) -> None:
    try:
        from source_proxy.benchmarks.campaign_3_5_fixture_authority import (
            Campaign35FixtureAuthorityError,
            load_campaign_3_5_fixture_authority,
        )

        fixture_authority = load_campaign_3_5_fixture_authority()
    except Campaign35FixtureAuthorityError as error:
        raise CampaignApprovalError(error.reason_code) from error
    raw_root = str(identity.get("workspace_root") or "").strip()
    authoritative_root = fixture_authority.workspace_root.resolve()
    root = Path(raw_root)
    if (
        not raw_root
        or not root.is_absolute()
        or root.resolve() != root
        or root != authoritative_root
        or not authoritative_root.is_dir()
    ):
        raise CampaignApprovalError("target_plugin_workspace_authority_mismatch")
    expected_static = {
        "schema_version": "spiritos-target-plugin/v1",
        "plugin_id": GENERIC_WORKSPACE_PLUGIN_ID,
        "repository_id": "campaign-3.5-fixture",
        "worktree_id": fixture_authority.manifest_sha256[:24],
        "branch": _RUNTIME_IDENTITY.branch,
        "state_namespace": fixture_authority.manifest_sha256[:24],
        "fixture_root": ".",
        "selected_prompt_id": "generic-architect-coder-packet",
        "selected_context_id": "server-scoped-architect-context",
        "execution_profile": "generic-architect-coder-packet-v1",
        "allowed_actions": list(fixture_authority.writable_paths or fixture_authority.allowed_paths),
        "readable_actions": list(fixture_authority.readable_paths or fixture_authority.allowed_paths),
        "result_identity": f"generic-workspace:{fixture_authority.manifest_sha256[:12]}",
        "approval_id": None,
        "approval_generation": None,
        "evidence_pointer": None,
        "failure_reason": None,
        "acknowledgement_status": "pending",
    }
    if any(identity.get(key) != value for key, value in expected_static.items()):
        raise CampaignApprovalError("target_plugin_identity_authority_mismatch")
    try:
        target_head = subprocess.check_output(
            ["git", "-C", str(authoritative_root), "rev-parse", "HEAD"],
            text=True,
            timeout=15,
        ).strip()
    except (OSError, subprocess.SubprocessError) as error:
        raise CampaignApprovalError("target_plugin_target_source_unavailable") from error
    if str(identity.get("target_source_head") or "") != target_head:
        raise CampaignApprovalError("target_plugin_target_source_head_mismatch")
    state_sha256 = fixture_authority.current_state_sha256
    state_paths = fixture_authority.current_state_paths
    if str(identity.get("target_workspace_state_sha256") or "") != state_sha256:
        raise CampaignApprovalError("target_plugin_workspace_state_mismatch")
    raw_paths = identity.get("target_workspace_state_paths")
    if not isinstance(raw_paths, (list, tuple)) or tuple(raw_paths) != state_paths:
        raise CampaignApprovalError("target_plugin_workspace_state_paths_mismatch")


def _validate_target_plugin_diff_scope(
    approved_diff: str,
    *,
    plugin: str,
    identity: dict[str, Any],
) -> None:
    if plugin != GENERIC_WORKSPACE_PLUGIN_ID:
        return
    root = Path(str(identity.get("workspace_root") or "")).resolve()
    try:
        from source_proxy.verification.diff import (
            DiffVerificationError,
            git_diff_changed_paths,
        )

        changed = git_diff_changed_paths(approved_diff, workspace_root=root)
    except (DiffVerificationError, OSError, subprocess.SubprocessError) as error:
        raise CampaignApprovalError("target_plugin_diff_paths_invalid") from error
    if not changed:
        raise CampaignApprovalError("target_plugin_diff_paths_missing")
    for path in changed:
        if not _path_matches_scope(path, identity.get("allowed_actions")):
            raise CampaignApprovalError("target_plugin_diff_scope_violation")
        candidate = root
        for part in Path(path).parts:
            candidate = candidate / part
            if candidate.is_symlink():
                raise CampaignApprovalError("target_plugin_diff_path_symlink")
        try:
            candidate.resolve().relative_to(root)
        except ValueError as error:
            raise CampaignApprovalError("target_plugin_diff_path_escape") from error


def coding_content_hash(
    *,
    task_id: str,
    action: str,
    approved_diff: str,
    target: str,
    selected_prompt_id: str,
    context_hash: str,
    target_plugin_identity: dict[str, Any] | None = None,
    proposal_binding: dict[str, Any] | None = None,
) -> str:
    return hashlib.sha256(canonical_json({
        "action": action,
        "approved_diff": approved_diff,
        "context_hash": context_hash,
        "proposal_binding": dict(proposal_binding or {}),
        "selected_prompt_id": selected_prompt_id,
        "target": target,
        "target_plugin_identity": dict(target_plugin_identity or {}),
        "task_id": task_id,
    }).encode("utf-8")).hexdigest()


def current_head() -> str:
    return subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"], text=True).strip()


def _call(command: str, payload: dict[str, Any]) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["SPIRITOS_APPROVAL_ROOT"] = ROOT
    completed = subprocess.run(
        ["python3", str(SCRIPT), command],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise CampaignApprovalError("approval_issuer_unavailable") from error
    if completed.returncode != 0:
        raise CampaignApprovalError(str(response.get("reason") or "approval_issuer_unavailable"))
    return response


def validate_coding_execution_approval(*, approval_id: str, task_id: str, action: str, approved_diff: str, target: str, selected_prompt_id: str, context_hash: str, lane_id: str = CODING_EXECUTOR_LANE, target_plugin_identity: dict[str, Any] | None = None, proposal_binding: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate an exact approval binding without entering the consuming state."""
    approval = _call("lookup", {"approval_id": approval_id})
    consumer = coding_executor_consumer(lane_id)
    if approval.get("consumer") != consumer:
        raise CampaignApprovalError("approval_consumer_mismatch")
    if approval.get("operation") != "coding_execution":
        raise CampaignApprovalError("approval_operation_not_permitted")
    if approval.get("context") != context_hash:
        raise CampaignApprovalError("approval_context_mismatch")
    plugin, identity = _target_plugin_binding(target=target, selected_prompt_id=selected_prompt_id, identity=target_plugin_identity)
    _validate_target_plugin_diff_scope(approved_diff, plugin=plugin, identity=identity)
    content_hash = coding_content_hash(task_id=task_id, action=action, approved_diff=approved_diff, target=target, selected_prompt_id=selected_prompt_id, context_hash=context_hash, target_plugin_identity=identity, proposal_binding=proposal_binding)
    binding = {
        "approval_id": approval_id,
        "consumer": consumer,
        "lane_id": lane_id,
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
        "target_plugin_identity": canonical_json(identity),
        "proposal_binding": canonical_json(dict(proposal_binding or {})),
    }
    return {"approval_id": approval_id, "generation": int(approval["generation"]), "plugin": plugin, "target_plugin_identity": identity, "proposal_binding": dict(proposal_binding or {}), "binding": binding}


def enter_coding_execution_consuming(approval: dict[str, Any]) -> dict[str, Any]:
    """Atomically enter consuming only after every non-mutating preflight passes."""
    binding = approval.get("binding")
    if not isinstance(binding, dict):
        raise CampaignApprovalError("approval_binding_missing")
    transition = _call("consume", binding)
    return {**approval, "state": str(transition.get("state") or "consuming")}


def lookup_coding_execution_approval(approval: dict[str, Any]) -> dict[str, Any]:
    """Return the exact authoritative record for a locally persisted approval.

    This lookup is intentionally binding-aware.  A caller recovering after a
    crash must not treat an approval id alone as evidence that the durable
    authority record belongs to the same execution.
    """

    binding = approval.get("binding")
    if not isinstance(binding, dict):
        raise CampaignApprovalError("approval_binding_missing")
    approval_id = str(approval.get("approval_id") or "")
    if not approval_id:
        raise CampaignApprovalError("approval_id_missing")
    if str(binding.get("approval_id") or "") != approval_id:
        raise CampaignApprovalError("approval_authority_receipt_mismatch")
    if str(binding.get("generation") or "") != str(
        approval.get("generation") or ""
    ):
        raise CampaignApprovalError("approval_generation_mismatch")
    authoritative = _call("lookup", {"approval_id": approval_id})
    if str(authoritative.get("id") or "") != approval_id:
        raise CampaignApprovalError("approval_authority_receipt_mismatch")
    if str(authoritative.get("generation") or "") != str(
        approval.get("generation") or ""
    ):
        raise CampaignApprovalError("approval_generation_mismatch")
    binding_fields = {
        "consumer": "approval_consumer_mismatch",
        "operation": "approval_operation_not_permitted",
        "repository": "approval_repository_mismatch",
        "worktree": "approval_worktree_mismatch",
        "root": "approval_root_mismatch",
        "target": "approval_target_mismatch",
        "plugin": "approval_plugin_mismatch",
        "preview": "approval_preview_mismatch",
        "content_hash": "approval_content_hash_mismatch",
        "context": "approval_context_mismatch",
        "source_head": "approval_source_mismatch",
    }
    for field, reason_code in binding_fields.items():
        if str(authoritative.get(field) or "") != str(binding.get(field) or ""):
            raise CampaignApprovalError(reason_code)
    state = authoritative.get("state")
    if not isinstance(state, str) or not state:
        raise CampaignApprovalError("approval_authority_receipt_mismatch")
    return dict(authoritative)


def consume_coding_execution_approval(*, approval_id: str, task_id: str, action: str, approved_diff: str, target: str, selected_prompt_id: str, context_hash: str, lane_id: str = CODING_EXECUTOR_LANE, target_plugin_identity: dict[str, Any] | None = None, proposal_binding: dict[str, Any] | None = None) -> dict[str, Any]:
    approval = validate_coding_execution_approval(
        approval_id=approval_id,
        task_id=task_id,
        action=action,
        approved_diff=approved_diff,
        target=target,
        selected_prompt_id=selected_prompt_id,
        context_hash=context_hash,
        lane_id=lane_id,
        target_plugin_identity=target_plugin_identity,
        proposal_binding=proposal_binding,
    )
    return enter_coding_execution_consuming(approval)


def persist_coding_execution_preview(*, task_id: str, action: str, approved_diff: str, target: str, selected_prompt_id: str, context_hash: str, target_plugin_identity: dict[str, Any] | None = None, proposal_binding: dict[str, Any] | None = None) -> dict[str, Any]:
    plugin, identity = _target_plugin_binding(target=target, selected_prompt_id=selected_prompt_id, identity=target_plugin_identity)
    _validate_target_plugin_diff_scope(approved_diff, plugin=plugin, identity=identity)
    content_hash = coding_content_hash(task_id=task_id, action=action, approved_diff=approved_diff, target=target, selected_prompt_id=selected_prompt_id, context_hash=context_hash, target_plugin_identity=identity, proposal_binding=proposal_binding)
    return _call("persist-preview", {
        "repository": REPOSITORY, "worktree": ROOT, "root": ROOT,
        "target": target, "plugin": plugin,
        "content_hash": content_hash, "context": context_hash, "source_head": current_head(),
        "target_plugin_identity": canonical_json(identity),
    })


def issue_coding_execution_approval(*, preview_id: str, expected_generation: int | None = None, lane_id: str = CODING_EXECUTOR_LANE) -> dict[str, Any]:
    if expected_generation is None:
        expected_generation = int(_call("lookup-preview", {"preview_id": preview_id})["generation"])
    issued = _call("issue", {
        "preview_id": preview_id,
        "expected_generation": str(expected_generation),
        "consumer": coding_executor_consumer(lane_id),
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
    receipt = _call("finalize", binding)
    expected_state = "consumed" if status == "succeeded" else "invalidated"
    if (
        str(receipt.get("approval_id") or "")
        != str(approval.get("approval_id") or "")
        or str(receipt.get("generation") or "")
        != str(approval.get("generation") or "")
        or receipt.get("state") != expected_state
        or receipt.get("result_id") != result_id
        or not isinstance(receipt.get("idempotent"), bool)
    ):
        raise CampaignApprovalError("approval_finalization_receipt_mismatch")
    return dict(receipt)
