from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from source_proxy.cartographer.models import BlueprintRecord
from source_proxy.cartographer.project_discovery import discover_projects

_INDEX_ROW_RE = re.compile(r"^\|\s*`([^`]+\.md)`\s*\|\s*([^|]+?)\s*\|", re.MULTILINE)
_FRONTMATTER_RE = re.compile(r"^---\r?\n(?P<body>.*?)\r?\n---(?:\r?\n|$)", re.DOTALL)
_DRIFT_STATUSES = {"active", "planned", "runbook"}
_STABLE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ALLOWED_DOC_TYPES = {
    "current_state",
    "component_blueprint",
    "component_roadmap",
    "runbook",
    "phase_receipt",
    "visual_sandbox",
    "proposal_queue",
    "schema",
    "index",
}
_ALLOWED_WRITE_POLICIES = {
    "proposal_only_until_dashboard_approved",
    "historical_read_only",
    "sandbox_proposal_only",
}


def list_blueprints() -> list[BlueprintRecord]:
    records: list[BlueprintRecord] = []
    seen: set[tuple[str, str]] = set()

    for project in discover_projects():
        blueprint_dir = Path(project.root) / "_blueprints"
        if not blueprint_dir.exists() or not blueprint_dir.is_dir():
            continue

        indexed = _indexed_blueprint_paths(blueprint_dir)
        if not indexed:
            indexed = {
                _blueprint_relative_path(blueprint_dir, path): None
                for path in _blueprint_markdown_files(blueprint_dir)
            }

        for rel_path, classification in sorted(indexed.items()):
            path = blueprint_dir / rel_path
            if not path.exists() or not path.is_file():
                records.append(
                    _missing_blueprint_record(
                        project_id=project.project_id,
                        rel_path=rel_path,
                        classification=classification,
                    )
                )
                continue

            record = _record_from_file(
                project_id=project.project_id,
                blueprint_dir=blueprint_dir,
                path=path,
                classification=classification,
            )
            key = (record.project_id, record.blueprint_id)
            if key in seen:
                record = BlueprintRecord(
                    **{
                        **record.__dict__,
                        "warnings": [
                            *record.warnings,
                            "duplicate_blueprint_id_in_project",
                        ],
                    }
                )
            seen.add(key)
            records.append(record)

    return records


def load_blueprints() -> list[BlueprintRecord]:
    return list_blueprints()


def count_blueprint_documents() -> int:
    return len(list_blueprints())


def _indexed_blueprint_paths(blueprint_dir: Path) -> dict[str, str | None]:
    index_path = blueprint_dir / "INDEX.md"
    if not index_path.exists():
        return {}

    try:
        index_text = index_path.read_text(encoding="utf-8")
    except OSError:
        return {}

    indexed: dict[str, str | None] = {}
    for match in _INDEX_ROW_RE.finditer(index_text):
        rel_path = match.group(1).replace("\\", "/")
        if rel_path == "INDEX.md":
            continue
        indexed[rel_path] = match.group(2).strip()
    return indexed


def _blueprint_markdown_files(blueprint_dir: Path) -> list[Path]:
    try:
        return [
            path
            for path in blueprint_dir.rglob("*.md")
            if path.is_file() and path.name != "INDEX.md"
        ]
    except OSError:
        return []


def _record_from_file(
    *,
    project_id: str,
    blueprint_dir: Path,
    path: Path,
    classification: str | None,
) -> BlueprintRecord:
    rel_path = _blueprint_relative_path(blueprint_dir, path)
    warnings: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return _missing_blueprint_record(
            project_id=project_id,
            rel_path=rel_path,
            classification=classification,
            warning="blueprint_file_unreadable",
        )

    frontmatter = _parse_frontmatter(text)
    if not frontmatter:
        warnings.append("missing_frontmatter")

    blueprint_id = str(frontmatter.get("blueprint_id") or _fallback_blueprint_id(rel_path))
    if frontmatter.get("blueprint_id") is None:
        warnings.append("missing_blueprint_id")
    elif not _STABLE_ID_RE.match(blueprint_id):
        warnings.append("unstable_blueprint_id")

    doc_type = str(frontmatter.get("doc_type") or "unknown")
    if doc_type != "unknown" and doc_type not in _ALLOWED_DOC_TYPES:
        warnings.append("invalid_doc_type")

    status = str(frontmatter.get("status") or "unknown")
    source_of_truth = _parse_bool(frontmatter.get("source_of_truth"))
    if source_of_truth is None:
        source_of_truth = False
        warnings.append("invalid_source_of_truth")

    code_paths = _as_string_list(frontmatter.get("code_paths"))
    related_blueprints = _as_string_list(frontmatter.get("related_blueprints"))
    write_policy = str(frontmatter.get("write_policy") or "proposal_only_until_dashboard_approved")
    last_verified = (
        str(frontmatter["last_verified"])
        if frontmatter.get("last_verified") is not None
        else None
    )
    if status == "active" and not code_paths:
        warnings.append("active_blueprint_missing_code_paths")
    if source_of_truth and not last_verified:
        warnings.append("source_of_truth_missing_last_verified")
    if write_policy not in _ALLOWED_WRITE_POLICIES:
        warnings.append("invalid_write_policy")

    return BlueprintRecord(
        blueprint_id=blueprint_id,
        title=str(frontmatter.get("title") or path.stem.replace("_", " ").title()),
        project_id=project_id,
        path=rel_path,
        component=str(frontmatter.get("component") or "unknown"),
        doc_type=doc_type,
        status=status,
        source_of_truth=source_of_truth,
        code_paths=code_paths,
        related_blueprints=related_blueprints,
        write_policy=write_policy,
        last_verified=last_verified,
        index_classification=classification,
        used_for_drift=_used_for_drift(status, source_of_truth),
        warnings=warnings,
    )


def _missing_blueprint_record(
    *,
    project_id: str,
    rel_path: str,
    classification: str | None,
    warning: str = "indexed_blueprint_missing",
) -> BlueprintRecord:
    return BlueprintRecord(
        blueprint_id=_fallback_blueprint_id(rel_path),
        title=Path(rel_path).stem.replace("_", " ").title(),
        project_id=project_id,
        path=rel_path,
        component="unknown",
        doc_type="unknown",
        status="missing",
        source_of_truth=False,
        index_classification=classification,
        used_for_drift=False,
        warnings=[warning],
    )


def _parse_frontmatter(text: str) -> dict[str, Any]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}

    frontmatter: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in match.group("body").splitlines():
        line = raw_line.rstrip()
        key_match = re.match(r"^([A-Za-z0-9_]+):(?:\s*(.*))?$", line)
        if key_match:
            key = key_match.group(1)
            raw_value = key_match.group(2) or ""
            frontmatter[key] = _parse_scalar(raw_value)
            current_key = key
            continue

        list_match = re.match(r"^\s*-\s*(.+?)\s*$", line)
        if list_match and current_key:
            value = _parse_scalar(list_match.group(1))
            existing = frontmatter.get(current_key)
            if not isinstance(existing, list):
                frontmatter[current_key] = []
            frontmatter[current_key].append(value)

    return frontmatter


def _parse_scalar(value: str) -> Any:
    stripped = value.strip()
    if stripped == "[]":
        return []
    if stripped == "true":
        return True
    if stripped == "false":
        return False
    if (
        len(stripped) >= 2
        and stripped[0] == stripped[-1]
        and stripped[0] in {"'", '"'}
    ):
        return stripped[1:-1]
    return stripped


def _parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value == "true":
        return True
    if value == "false":
        return False
    return None


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _used_for_drift(status: str, source_of_truth: bool) -> bool:
    return status in _DRIFT_STATUSES and source_of_truth


def _blueprint_relative_path(blueprint_dir: Path, path: Path) -> str:
    return path.relative_to(blueprint_dir).as_posix()


def _fallback_blueprint_id(rel_path: str) -> str:
    stem = Path(rel_path).with_suffix("").as_posix()
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") or "blueprint"
