from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_GIT_TIMEOUT_SECONDS = 10

_CODING_PREFIXES = ("src/app/coding/", "src/components/coding/")
_MAP_PREFIXES = ("src/app/map/",)
_PACKAGE_CONFIG_ENV_PREFIXES = ("config/",)
_PACKAGE_CONFIG_ENV_FILES = ("package.json", "next.config.ts")
_SOURCE_PROXY_RUNTIME_PREFIXES = ("source_proxy/",)
_SOURCE_PROXY_RUNTIME_EXCLUDED_PREFIXES = ("source_proxy/tests/",)
_TRUTH_PACKET_SCHEMA_VERSION = "cartographer.truth-packet.v0.1"
_TRUTH_PACKET_ID = "cartographer-truth-packet-v0.1"
_TRUTH_PACKET_STALE_AFTER_SECONDS = 300


@dataclass(frozen=True)
class GitCommandFailure:
    command: list[str]
    returncode: int
    stderr: str


def collect_live_repo_state(repo_root: str | Path = ".") -> dict[str, Any]:
    """Collect read-only repository state for Cartographer safety display."""
    root = Path(repo_root)
    collected_at = _utc_now()

    branch_result = _run_git(root, ["git", "branch", "--show-current"])
    head_result = _run_git(root, ["git", "rev-parse", "HEAD"])
    status_result = _run_git(
        root,
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
    )

    failures = [
        _failure_for(result)
        for result in (branch_result, head_result, status_result)
        if result.returncode != 0
    ]
    if failures:
        reasons = [
            f"git command failed closed: {' '.join(failure.command)}"
            for failure in failures
        ]
        payload = {
            "current_branch": None,
            "current_head": None,
            "tracked_dirty_files": [],
            "untracked_files": [],
            "protected_lane_matches": [],
            "coding_files_dirty": False,
            "map_files_dirty": False,
            "package_config_env_files_dirty": False,
            "source_proxy_runtime_files_dirty": False,
            "unknown_unclassified_dirty_files": [],
            "recommended_safety_state": "blocked",
            "blocker_reasons": reasons,
            "collected_at": collected_at,
            "no_mutation_guarantee": _no_mutation_guarantee(),
            "git_available": False,
            "git_errors": [
                {
                    "command": failure.command,
                    "returncode": failure.returncode,
                    "stderr": failure.stderr,
                }
                for failure in failures
            ],
        }
        return _with_truth_packet(payload)

    parsed = _parse_porcelain_status(status_result.stdout)
    tracked_dirty_files = parsed["tracked_dirty_files"]
    untracked_files = parsed["untracked_files"]
    dirty_files = tracked_dirty_files + untracked_files
    classification = _classify_dirty_files(dirty_files)
    safety = _recommend_safety_state(classification, dirty_files)

    payload = {
        "current_branch": branch_result.stdout.strip() or None,
        "current_head": head_result.stdout.strip() or None,
        "tracked_dirty_files": tracked_dirty_files,
        "untracked_files": untracked_files,
        "protected_lane_matches": classification["protected_lane_matches"],
        "coding_files_dirty": classification["coding_files_dirty"],
        "map_files_dirty": classification["map_files_dirty"],
        "package_config_env_files_dirty": classification[
            "package_config_env_files_dirty"
        ],
        "source_proxy_runtime_files_dirty": classification[
            "source_proxy_runtime_files_dirty"
        ],
        "unknown_unclassified_dirty_files": classification[
            "unknown_unclassified_dirty_files"
        ],
        "recommended_safety_state": safety["state"],
        "blocker_reasons": safety["blocker_reasons"],
        "collected_at": collected_at,
        "no_mutation_guarantee": _no_mutation_guarantee(),
        "git_available": True,
        "git_errors": [],
    }
    return _with_truth_packet(payload)


def build_cartographer_truth_packet(live_state: dict[str, Any]) -> dict[str, Any]:
    """Build the display-only truth packet from already collected live facts."""
    generated_at = _utc_now()
    collected_at = _string_or_none(live_state.get("collected_at"))
    generated_at_timestamp = _parse_utc_timestamp(generated_at)
    collected_at_timestamp = _parse_utc_timestamp(collected_at)
    age_seconds = _age_seconds(
        generated_at=generated_at_timestamp,
        collected_at=collected_at_timestamp,
    )
    recency_unknown_fields = _recency_unknown_fields(
        generated_at=generated_at,
        generated_at_timestamp=generated_at_timestamp,
        collected_at=collected_at,
        collected_at_timestamp=collected_at_timestamp,
        age_seconds=age_seconds,
    )
    stale_fields = _stale_fields(age_seconds)
    git_available_value = _bool_or_none(live_state.get("git_available"))
    git_available = git_available_value is True
    current_branch = _string_or_none(live_state.get("current_branch"))
    current_head = _string_or_none(live_state.get("current_head"))
    tracked_dirty_files, tracked_dirty_files_valid = _string_list_with_validity(
        live_state.get("tracked_dirty_files")
    )
    untracked_files, untracked_files_valid = _string_list_with_validity(
        live_state.get("untracked_files")
    )
    protected_lane_matches, protected_lane_matches_valid = (
        _record_list_with_validity(live_state.get("protected_lane_matches"))
    )
    unknown_unclassified_dirty_files, unknown_unclassified_dirty_files_valid = (
        _string_list_with_validity(
            live_state.get("unknown_unclassified_dirty_files")
        )
    )
    blocker_reasons, blocker_reasons_valid = _string_list_with_validity(
        live_state.get("blocker_reasons")
    )
    recommended_safety_state_value = _string_or_none(
        live_state.get("recommended_safety_state")
    )
    recommended_safety_state_valid = recommended_safety_state_value in {
        "blocked",
        "caution",
        "clear",
    }
    recommended_safety_state = _recommended_state(recommended_safety_state_value)
    git_errors, git_errors_valid = _record_list_with_validity(
        live_state.get("git_errors")
    )
    no_mutation_guarantee, no_mutation_guarantee_valid = (
        _safe_no_mutation_guarantee(live_state.get("no_mutation_guarantee"))
    )
    coding_files_dirty, coding_files_dirty_valid = _bool_with_validity(
        live_state.get("coding_files_dirty")
    )
    map_files_dirty, map_files_dirty_valid = _bool_with_validity(
        live_state.get("map_files_dirty")
    )
    package_config_env_files_dirty, package_config_env_files_dirty_valid = (
        _bool_with_validity(live_state.get("package_config_env_files_dirty"))
    )
    source_proxy_runtime_files_dirty, source_proxy_runtime_files_dirty_valid = (
        _bool_with_validity(live_state.get("source_proxy_runtime_files_dirty"))
    )
    unknown_fields = _unknown_fields(
        git_available=git_available,
        git_available_known=git_available_value is not None,
        current_branch=current_branch,
        current_head=current_head,
        tracked_dirty_files_valid=tracked_dirty_files_valid,
        untracked_files_valid=untracked_files_valid,
        protected_lane_matches_valid=protected_lane_matches_valid,
        unknown_unclassified_dirty_files_valid=unknown_unclassified_dirty_files_valid,
        blocker_reasons_valid=blocker_reasons_valid,
        recommended_safety_state_valid=recommended_safety_state_valid,
        git_errors_valid=git_errors_valid,
        no_mutation_guarantee_valid=no_mutation_guarantee_valid,
        coding_files_dirty_valid=coding_files_dirty_valid,
        map_files_dirty_valid=map_files_dirty_valid,
        package_config_env_files_dirty_valid=package_config_env_files_dirty_valid,
        source_proxy_runtime_files_dirty_valid=source_proxy_runtime_files_dirty_valid,
        recency_unknown_fields=recency_unknown_fields,
    )
    verified_fields = _verified_fields(
        git_available=git_available,
        git_available_known=git_available_value is not None,
        current_branch=current_branch,
        current_head=current_head,
        tracked_dirty_files_valid=tracked_dirty_files_valid,
        untracked_files_valid=untracked_files_valid,
        protected_lane_matches_valid=protected_lane_matches_valid,
        no_mutation_guarantee_valid=no_mutation_guarantee_valid,
    )
    status = _packet_status(
        git_available=git_available,
        recommended_safety_state=recommended_safety_state,
        unknown_fields=unknown_fields,
        stale_fields=stale_fields,
    )
    confidence, confidence_reason = _confidence(
        git_available=git_available,
        unknown_fields=unknown_fields,
        stale_fields=stale_fields,
    )
    facts = {
        "current_branch": current_branch,
        "current_head": current_head,
        "git_available": git_available,
        "git_errors": git_errors,
        "tracked_dirty_count": len(tracked_dirty_files),
        "untracked_dirty_count": len(untracked_files),
        "total_dirty_count": len(tracked_dirty_files) + len(untracked_files),
        "protected_lane_count": len(protected_lane_matches),
        "coding_files_dirty": coding_files_dirty,
        "map_files_dirty": map_files_dirty,
        "package_config_env_files_dirty": package_config_env_files_dirty,
        "source_proxy_runtime_files_dirty": source_proxy_runtime_files_dirty,
        "unknown_unclassified_dirty_count": len(unknown_unclassified_dirty_files),
        "no_mutation_guarantee": no_mutation_guarantee,
    }

    return {
        "schema_version": _TRUTH_PACKET_SCHEMA_VERSION,
        "packet_kind": "cartographer_truth_packet",
        "packet_id": _TRUTH_PACKET_ID,
        "generated_at": generated_at,
        "collected_at": collected_at,
        "status": status,
        "decision_default": "no_go",
        "advisory_only": True,
        "facts": facts,
        "recommendations": {
            "recommended_safety_state": recommended_safety_state,
            "blocker_reasons": blocker_reasons,
            "safe_next_action": _truth_safe_next_action(
                status=status,
                blocker_reasons=blocker_reasons,
                total_dirty_count=facts["total_dirty_count"],
            ),
            "confidence": confidence,
            "confidence_reason": confidence_reason,
            "no_go_reason": _no_go_reason(
                status,
                blocker_reasons,
                unknown_fields,
                stale_fields,
            ),
        },
        "state_flags": {
            "verified": (
                bool(verified_fields) and not unknown_fields and not stale_fields
            ),
            "blocked": status in {"no_go", "blocked", "stale"},
            "stale": bool(stale_fields),
            "unknown": bool(unknown_fields),
            "caution": status == "caution",
            "clear": status == "clear",
            "no_go": True,
            "advisory_only": True,
        },
        "sources": _truth_sources(
            collected_at=collected_at,
            git_available=git_available,
            current_branch=current_branch,
            current_head=current_head,
            status_source_valid=(
                tracked_dirty_files_valid
                and untracked_files_valid
                and protected_lane_matches_valid
                and git_errors_valid
            ),
            stale=bool(stale_fields),
        ),
        "evidence_links": _truth_evidence_links(
            status=status,
            current_branch=current_branch,
            current_head=current_head,
            total_dirty_count=facts["total_dirty_count"],
            protected_lane_count=facts["protected_lane_count"],
            blocker_reasons=blocker_reasons,
            stale_fields=stale_fields,
            unknown_fields=unknown_fields,
        ),
        "recency": {
            "generated_at": generated_at,
            "collected_at": collected_at,
            "stale_after_seconds": _TRUTH_PACKET_STALE_AFTER_SECONDS,
            "age_seconds": age_seconds,
            "generated_at_valid": generated_at_timestamp is not None,
            "collected_at_valid": collected_at_timestamp is not None,
            "stale": bool(stale_fields),
        },
        "verified_fields": verified_fields,
        "unknown_fields": unknown_fields,
        "stale_fields": stale_fields,
        "blocked_reason_codes": [_reason_code(reason) for reason in blocker_reasons],
        "authority": _truth_authority_defaults(),
    }


def _with_truth_packet(payload: dict[str, Any]) -> dict[str, Any]:
    payload["truth_packet"] = build_cartographer_truth_packet(payload)
    return payload


def _packet_status(
    *,
    git_available: bool,
    recommended_safety_state: str,
    unknown_fields: list[str],
    stale_fields: list[str],
) -> str:
    if not git_available or unknown_fields:
        return "no_go"
    if stale_fields:
        return "stale"
    if recommended_safety_state in {"blocked", "caution", "clear"}:
        return recommended_safety_state
    return "no_go"


def _truth_safe_next_action(
    *,
    status: str,
    blocker_reasons: list[str],
    total_dirty_count: int,
) -> str:
    if status == "stale":
        return "Stop and refresh live repository facts before trusting this packet for any future authority gate."
    if status in {"no_go", "blocked"}:
        if blocker_reasons:
            return "Stop and resolve blocker reasons before trusting this packet for any future authority gate."
        return "Stop and manually inspect unknown live-state fields before any future authority gate."
    if status == "caution":
        return "Review dirty tree facts manually and keep Cartographer display-only."
    if total_dirty_count > 0:
        return "Review dirty tree facts manually before any later scoped plan."
    return "Facts are clear for display-only review; action authority remains NO-GO."


def _no_go_reason(
    status: str,
    blocker_reasons: list[str],
    unknown_fields: list[str],
    stale_fields: list[str],
) -> str:
    if unknown_fields:
        return "critical_fields_unknown"
    if stale_fields:
        return "stale_fields_present"
    if blocker_reasons:
        return "blocked_reasons_present"
    if status == "clear":
        return "authority_not_granted"
    if status == "caution":
        return "human_review_required"
    if status == "stale":
        return "stale_fields_present"
    return "no_go_default"


def _confidence(
    *,
    git_available: bool,
    unknown_fields: list[str],
    stale_fields: list[str],
) -> tuple[str, str]:
    if not git_available:
        return "low", "git collector unavailable; packet fails closed"
    if unknown_fields:
        return "low", f"critical fields unknown: {', '.join(unknown_fields)}"
    if stale_fields:
        return "low", f"stale fields present: {', '.join(stale_fields)}"
    return "high", "git branch, HEAD, and status facts were read successfully"


def _truth_sources(
    *,
    collected_at: str | None,
    git_available: bool,
    current_branch: str | None,
    current_head: str | None,
    status_source_valid: bool,
    stale: bool,
) -> list[dict[str, Any]]:
    branch_status = _source_status(
        git_available=git_available,
        value_known=current_branch is not None,
        value_valid=True,
        stale=stale,
    )
    head_status = _source_status(
        git_available=git_available,
        value_known=current_head is not None,
        value_valid=True,
        stale=stale,
    )
    status_status = _source_status(
        git_available=git_available,
        value_known=git_available,
        value_valid=status_source_valid,
        stale=stale,
    )
    return [
        {
            "name": "git.branch.current",
            "observed_at": collected_at,
            "status": branch_status,
            "verified": branch_status == "verified",
            "stale": branch_status == "stale",
            "unknown": branch_status in {"malformed", "unavailable", "unknown"},
            "detail": "Read with git branch --show-current.",
        },
        {
            "name": "git.head.current",
            "observed_at": collected_at,
            "status": head_status,
            "verified": head_status == "verified",
            "stale": head_status == "stale",
            "unknown": head_status in {"malformed", "unavailable", "unknown"},
            "detail": "Read with git rev-parse HEAD.",
        },
        {
            "name": "git.status.porcelain",
            "observed_at": collected_at,
            "status": status_status,
            "verified": status_status == "verified",
            "stale": status_status == "stale",
            "unknown": status_status in {"malformed", "unavailable", "unknown"},
            "detail": "Read with git status --porcelain=v1 -z --untracked-files=all.",
        },
    ]


def _truth_evidence_links(
    *,
    status: str,
    current_branch: str | None,
    current_head: str | None,
    total_dirty_count: int,
    protected_lane_count: int,
    blocker_reasons: list[str],
    stale_fields: list[str],
    unknown_fields: list[str],
) -> list[dict[str, Any]]:
    branch_label = current_branch or "unknown branch"
    short_head = current_head[:12] if current_head else "unknown head"
    return [
        {
            "label": "Live repo truth packet",
            "kind": "live_fact",
            "href": "/map/raw",
            "summary": (
                f"{status} on {branch_label} at {short_head}; "
                f"{total_dirty_count} dirty file(s), {protected_lane_count} protected warning(s)."
            ),
            "authority_granted": False,
            "review_only": True,
        },
        {
            "label": "Current blockers",
            "kind": "blocker_summary",
            "href": "/map/raw#authority-boundary",
            "summary": (
                "; ".join(blocker_reasons[:3])
                if blocker_reasons
                else "No blocker reasons reported; NO-GO still remains the decision default."
            ),
            "authority_granted": False,
            "review_only": True,
        },
        {
            "label": "Unknown or stale fields",
            "kind": "freshness_summary",
            "href": "/map/raw#live-read-only-packet",
            "summary": _freshness_summary(
                stale_fields=stale_fields,
                unknown_fields=unknown_fields,
            ),
            "authority_granted": False,
            "review_only": True,
        },
    ]


def _freshness_summary(
    *,
    stale_fields: list[str],
    unknown_fields: list[str],
) -> str:
    if unknown_fields:
        return f"Unknown fields keep the packet NO-GO: {', '.join(unknown_fields[:4])}."
    if stale_fields:
        return f"Stale fields keep the packet NO-GO: {', '.join(stale_fields[:4])}."
    return "No unknown or stale fields reported; evidence remains review-only."


def _verified_fields(
    *,
    git_available: bool,
    git_available_known: bool,
    current_branch: str | None,
    current_head: str | None,
    tracked_dirty_files_valid: bool,
    untracked_files_valid: bool,
    protected_lane_matches_valid: bool,
    no_mutation_guarantee_valid: bool,
) -> list[str]:
    if not git_available or not git_available_known:
        return []

    fields = ["facts.git_available"]
    if tracked_dirty_files_valid:
        fields.append("facts.tracked_dirty_count")
    if untracked_files_valid:
        fields.append("facts.untracked_dirty_count")
    if tracked_dirty_files_valid and untracked_files_valid:
        fields.append("facts.total_dirty_count")
    if protected_lane_matches_valid:
        fields.append("facts.protected_lane_count")
    if no_mutation_guarantee_valid:
        fields.append("facts.no_mutation_guarantee")
    if current_branch is not None:
        fields.append("facts.current_branch")
    if current_head is not None:
        fields.append("facts.current_head")
    return fields


def _unknown_fields(
    *,
    git_available: bool,
    git_available_known: bool,
    current_branch: str | None,
    current_head: str | None,
    tracked_dirty_files_valid: bool,
    untracked_files_valid: bool,
    protected_lane_matches_valid: bool,
    unknown_unclassified_dirty_files_valid: bool,
    blocker_reasons_valid: bool,
    recommended_safety_state_valid: bool,
    git_errors_valid: bool,
    no_mutation_guarantee_valid: bool,
    coding_files_dirty_valid: bool,
    map_files_dirty_valid: bool,
    package_config_env_files_dirty_valid: bool,
    source_proxy_runtime_files_dirty_valid: bool,
    recency_unknown_fields: list[str],
) -> list[str]:
    fields: list[str] = []
    seen: set[str] = set()
    for field in recency_unknown_fields:
        _append_unique(fields, seen, field)
    if not git_available_known:
        _append_unique(fields, seen, "facts.git_available")
    if not git_available:
        for field in (
            "facts.current_branch",
            "facts.current_head",
            "facts.tracked_dirty_count",
            "facts.untracked_dirty_count",
            "facts.protected_lane_count",
        ):
            _append_unique(fields, seen, field)

    if current_branch is None:
        _append_unique(fields, seen, "facts.current_branch")
    if current_head is None:
        _append_unique(fields, seen, "facts.current_head")
    if not tracked_dirty_files_valid:
        _append_unique(fields, seen, "facts.tracked_dirty_count")
    if not untracked_files_valid:
        _append_unique(fields, seen, "facts.untracked_dirty_count")
    if not tracked_dirty_files_valid or not untracked_files_valid:
        _append_unique(fields, seen, "facts.total_dirty_count")
    if not protected_lane_matches_valid:
        _append_unique(fields, seen, "facts.protected_lane_count")
    if not unknown_unclassified_dirty_files_valid:
        _append_unique(fields, seen, "facts.unknown_unclassified_dirty_count")
    if not blocker_reasons_valid:
        _append_unique(fields, seen, "recommendations.blocker_reasons")
    if not recommended_safety_state_valid:
        _append_unique(fields, seen, "recommendations.recommended_safety_state")
    if not git_errors_valid:
        _append_unique(fields, seen, "facts.git_errors")
    if not no_mutation_guarantee_valid:
        _append_unique(fields, seen, "facts.no_mutation_guarantee")
    if not coding_files_dirty_valid:
        _append_unique(fields, seen, "facts.coding_files_dirty")
    if not map_files_dirty_valid:
        _append_unique(fields, seen, "facts.map_files_dirty")
    if not package_config_env_files_dirty_valid:
        _append_unique(fields, seen, "facts.package_config_env_files_dirty")
    if not source_proxy_runtime_files_dirty_valid:
        _append_unique(fields, seen, "facts.source_proxy_runtime_files_dirty")
    return fields


def _truth_authority_defaults() -> dict[str, bool]:
    return {
        "authority_granted": False,
        "write_actions_enabled": False,
        "write_authority_granted": False,
        "command_authority_granted": False,
        "workflow_authority_granted": False,
        "queue_authority_granted": False,
        "git_authority_granted": False,
        "approval_token_consumption_enabled": False,
        "worker_execution_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "can_mutate": False,
    }


def _recommended_state(value: str | None) -> str:
    if value in {"blocked", "caution", "clear"}:
        return value
    return "blocked"


def _source_status(
    *,
    git_available: bool,
    value_known: bool,
    value_valid: bool,
    stale: bool,
) -> str:
    if not git_available:
        return "unavailable"
    if not value_valid:
        return "malformed"
    if not value_known:
        return "unknown"
    if stale:
        return "stale"
    return "verified"


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _string_list_with_validity(value: Any) -> tuple[list[str], bool]:
    if not isinstance(value, list):
        return [], False
    return [item for item in value if isinstance(item, str)], all(
        isinstance(item, str) for item in value
    )


def _record_list_with_validity(value: Any) -> tuple[list[dict[str, Any]], bool]:
    if not isinstance(value, list):
        return [], False
    return [item for item in value if isinstance(item, dict)], all(
        isinstance(item, dict) for item in value
    )


def _bool_or_none(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _bool_with_validity(value: Any) -> tuple[bool, bool]:
    if isinstance(value, bool):
        return value, True
    return False, False


def _safe_no_mutation_guarantee(value: Any) -> tuple[dict[str, Any], bool]:
    guarantee = _no_mutation_guarantee()
    if not isinstance(value, dict):
        return guarantee, False

    for key, expected in guarantee.items():
        supplied = value.get(key)
        if isinstance(expected, bool) and supplied is not False:
            return guarantee, False

    supplied_git_commands = value.get("git_commands")
    if not isinstance(supplied_git_commands, list):
        return guarantee, False

    return value, True


def _parse_utc_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _age_seconds(
    *,
    generated_at: datetime | None,
    collected_at: datetime | None,
) -> int | None:
    if generated_at is None or collected_at is None:
        return None
    age = int((generated_at - collected_at).total_seconds())
    return age if age >= 0 else None


def _recency_unknown_fields(
    *,
    generated_at: str,
    generated_at_timestamp: datetime | None,
    collected_at: str | None,
    collected_at_timestamp: datetime | None,
    age_seconds: int | None,
) -> list[str]:
    fields: list[str] = []
    if not generated_at or generated_at_timestamp is None:
        fields.append("recency.generated_at")
    if collected_at is None or collected_at_timestamp is None:
        fields.append("recency.collected_at")
    if (
        generated_at_timestamp is not None
        and collected_at_timestamp is not None
        and age_seconds is None
    ):
        fields.append("recency.collected_at")
    return fields


def _stale_fields(age_seconds: int | None) -> list[str]:
    if age_seconds is None or age_seconds <= _TRUTH_PACKET_STALE_AFTER_SECONDS:
        return []
    return [
        "recency.collected_at",
        "sources.git.branch.current",
        "sources.git.head.current",
        "sources.git.status.porcelain",
    ]


def _reason_code(value: str) -> str:
    normalized = "".join(
        character.lower() if character.isalnum() else "_"
        for character in value.strip()
    )
    parts = [part for part in normalized.split("_") if part]
    return "_".join(parts) or "unknown_reason"


def _run_git(root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            command,
            returncode=124,
            stdout="",
            stderr="git_command_timeout",
        )
    except OSError as error:
        return subprocess.CompletedProcess(
            command,
            returncode=127,
            stdout="",
            stderr=str(error),
        )


def _failure_for(result: subprocess.CompletedProcess[str]) -> GitCommandFailure:
    return GitCommandFailure(
        command=[str(part) for part in result.args],
        returncode=result.returncode,
        stderr=result.stderr.strip(),
    )


def _parse_porcelain_status(output: str) -> dict[str, list[str]]:
    tracked_dirty_files: list[str] = []
    untracked_files: list[str] = []
    seen_tracked: set[str] = set()
    seen_untracked: set[str] = set()
    records = output.split("\x00")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if len(record) < 4:
            continue

        status = record[:2]
        path = _normalize_path(record[3:])
        if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
            index += 1
        if not path:
            continue

        if status == "??":
            _append_unique(untracked_files, seen_untracked, path)
        else:
            _append_unique(tracked_dirty_files, seen_tracked, path)

    return {
        "tracked_dirty_files": tracked_dirty_files,
        "untracked_files": untracked_files,
    }


def _classify_dirty_files(dirty_files: list[str]) -> dict[str, Any]:
    matches: list[dict[str, str]] = []
    unknown: list[str] = []
    coding_dirty = False
    map_dirty = False
    package_config_env_dirty = False
    source_proxy_runtime_dirty = False

    for path in dirty_files:
        categories = _categories_for(path)
        if not categories:
            unknown.append(path)
            continue

        for category in categories:
            matches.append({"path": path, "lane": category})
            if category == "coding":
                coding_dirty = True
            elif category == "map":
                map_dirty = True
            elif category == "package_config_env":
                package_config_env_dirty = True
            elif category == "source_proxy_runtime":
                source_proxy_runtime_dirty = True

    return {
        "protected_lane_matches": matches,
        "coding_files_dirty": coding_dirty,
        "map_files_dirty": map_dirty,
        "package_config_env_files_dirty": package_config_env_dirty,
        "source_proxy_runtime_files_dirty": source_proxy_runtime_dirty,
        "unknown_unclassified_dirty_files": unknown,
    }


def _categories_for(path: str) -> list[str]:
    categories: list[str] = []
    if _has_prefix(path, _CODING_PREFIXES):
        categories.append("coding")
    if _has_prefix(path, _MAP_PREFIXES):
        categories.append("map")
    if path in _PACKAGE_CONFIG_ENV_FILES or path.startswith(".env"):
        categories.append("package_config_env")
    if _has_prefix(path, _PACKAGE_CONFIG_ENV_PREFIXES):
        categories.append("package_config_env")
    if _is_source_proxy_runtime(path):
        categories.append("source_proxy_runtime")
    return categories


def _recommend_safety_state(
    classification: dict[str, Any],
    dirty_files: list[str],
) -> dict[str, Any]:
    blocker_reasons: list[str] = []
    if classification["coding_files_dirty"]:
        blocker_reasons.append("/coding files are dirty")
    if classification["package_config_env_files_dirty"]:
        blocker_reasons.append("package, config, or env files are dirty")
    if classification["source_proxy_runtime_files_dirty"]:
        blocker_reasons.append("source_proxy runtime files are dirty")

    if blocker_reasons:
        return {"state": "blocked", "blocker_reasons": blocker_reasons}

    if dirty_files:
        return {"state": "caution", "blocker_reasons": []}

    return {"state": "clear", "blocker_reasons": []}


def _is_source_proxy_runtime(path: str) -> bool:
    if not _has_prefix(path, _SOURCE_PROXY_RUNTIME_PREFIXES):
        return False
    return not _has_prefix(path, _SOURCE_PROXY_RUNTIME_EXCLUDED_PREFIXES)


def _has_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def _normalize_path(path: str) -> str:
    return path.strip().replace("\\", "/")


def _append_unique(values: list[str], seen: set[str], value: str) -> None:
    if value not in seen:
        seen.add(value)
        values.append(value)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _no_mutation_guarantee() -> dict[str, Any]:
    return {
        "mutates_files": False,
        "stages_files": False,
        "commits": False,
        "pushes": False,
        "creates_branches": False,
        "creates_worktrees": False,
        "stashes": False,
        "cleans": False,
        "resets": False,
        "checkouts": False,
        "runs_package_installs": False,
        "executes_arbitrary_shell_strings": False,
        "git_commands": [
            ["git", "branch", "--show-current"],
            ["git", "rev-parse", "HEAD"],
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        ],
    }
