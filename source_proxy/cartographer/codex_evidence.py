from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from source_proxy.cartographer.component_mapper import RISK_ORDER, map_paths
from source_proxy.cartographer.models import CodexEvidenceRecord
from source_proxy.safety.paths import is_secret_shaped_path


DEFAULT_CODEX_EVIDENCE_DIRS: tuple[Path, ...] = (
    Path("/tmp/spiritos-source-proxy-codex/artifacts"),
    Path("/tmp/spiritos-codex-10.10.2-evidence"),
    Path("/tmp/spiritos-codex-10.10.3-evidence"),
)


def list_codex_evidence_records(evidence_dirs: list[Path] | None = None) -> list[CodexEvidenceRecord]:
    records: list[CodexEvidenceRecord] = []
    for artifact_path in _artifact_paths(evidence_dirs):
        payload = _read_json_object(artifact_path)
        if payload is None:
            continue
        record = _record_from_payload(payload, artifact_path)
        if record is not None:
            records.append(record)
    return sorted(records, key=lambda record: (record.task_id, record.artifact_path))


def build_codex_evidence_rollup(evidence_dirs: list[Path] | None = None) -> dict[str, Any]:
    records = list_codex_evidence_records(evidence_dirs)
    changed_files = sorted({path for record in records for path in record.changed_files})
    components = sorted({component for record in records for component in record.components})
    risk_labels = sorted({record.risk for record in records})
    return {
        "status": "observing",
        "source": "codex_evidence",
        "records": records,
        "evidence_count": len(records),
        "latest_task_ids": [record.task_id for record in records[-5:]],
        "changed_files": changed_files,
        "components": components,
        "risk_labels": risk_labels,
        "proposal_pending_review": any(record.proposal_pending_review for record in records),
        "commit_proposal_needed": any(record.commit_proposal_needed for record in records),
        "approval_authority": any(record.approval_authority for record in records),
        "apply_authority": any(record.apply_authority for record in records),
        "commit_authority": any(record.commit_authority for record in records),
        "push_authority": any(record.push_authority for record in records),
        "actions_taken": False,
    }


def _artifact_paths(evidence_dirs: list[Path] | None) -> list[Path]:
    roots = evidence_dirs or _configured_evidence_dirs()
    paths: list[Path] = []
    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        paths.extend(path for path in root.glob("*.json") if path.is_file())
    return sorted(paths)


def _configured_evidence_dirs() -> list[Path]:
    configured = os.environ.get("SPIRIT_CODEX_EVIDENCE_PATHS", "").strip()
    if not configured:
        return list(DEFAULT_CODEX_EVIDENCE_DIRS)
    return [Path(item).expanduser() for item in configured.split(os.pathsep) if item.strip()]


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _record_from_payload(payload: dict[str, Any], artifact_path: Path) -> CodexEvidenceRecord | None:
    if payload.get("artifact_version") != "codex_evidence.v1":
        return None
    task_id = str(payload.get("task_id") or "").strip()
    if not task_id:
        return None
    changed_files = _safe_changed_files(payload)
    components, unmapped = map_paths(changed_files)
    component_ids = [component.component_id for component in components]
    if unmapped:
        component_ids.extend(f"unmapped:{item.reason}" for item in unmapped)
    risk = _max_risk([*(component.risk for component in components), *(item.risk for item in unmapped)])
    recommendation = str(payload.get("recommendation") or "unknown")
    safety_verdict = str(payload.get("safety_verdict") or "unknown")
    return CodexEvidenceRecord(
        task_id=task_id,
        artifact_path=str(artifact_path),
        safety_verdict=safety_verdict,
        recommendation=recommendation,
        changed_files=changed_files,
        components=component_ids,
        risk=risk,
        tests_run=_tests_run(payload),
        proposal_pending_review=recommendation == "ready_for_review",
        commit_proposal_needed=safety_verdict == "passed" and recommendation == "ready_for_review",
        approval_authority=bool(payload.get("approval_authority")),
        apply_authority=bool(payload.get("apply_authority")),
        commit_authority=bool(payload.get("commit_authority")),
        push_authority=bool(payload.get("push_authority")),
        action_taken=False,
    )


def _safe_changed_files(payload: dict[str, Any]) -> list[str]:
    raw_paths = payload.get("changed_files_after") or payload.get("changed_files_before") or []
    if not isinstance(raw_paths, list):
        return []
    safe: list[str] = []
    for raw_path in raw_paths:
        path = str(raw_path).strip()
        if not path:
            continue
        safe.append("[redacted-protected-path]" if is_secret_shaped_path(path) else path)
    return list(dict.fromkeys(safe))


def _tests_run(payload: dict[str, Any]) -> str:
    event_count = payload.get("json_event_count")
    if isinstance(event_count, int):
        return f"{event_count} JSON events captured"
    return "not reported"


def _max_risk(risks: list[str]) -> str:
    if not risks:
        return "unknown"
    return max(risks, key=lambda risk: RISK_ORDER.get(risk, RISK_ORDER["unknown"]))
