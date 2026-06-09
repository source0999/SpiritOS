from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from contextlib import closing
from typing import Any, Literal, TypeVar

from source_proxy.planning.migrations import PLAN_MIGRATORS
from source_proxy.safety.paths import normalize_repo_path_candidate


PLAN_SCHEMA_VERSION = 1

TaskClass = Literal["implement", "refactor", "fix", "style", "explain"]
Complexity = Literal["trivial", "small", "medium", "large"]
CoderOperation = Literal["edit", "create", "delete"]
CriterionKind = Literal["literal", "behavioral"]
ContextSliceKind = Literal["target", "import", "sibling", "type_definition", "doc"]
CoderResponseStatus = Literal["ok", "blocked"]
TaskSpecType = Literal["modify_existing_file", "create_new_file", "delete_file"]
TaskSpecRiskTier = Literal["low", "medium", "high"]


class PlanSchemaTooNew(ValueError):
    pass


@dataclass(frozen=True)
class BundleSnapshot:
    bundle_path: str
    bundle_sha256: str
    workspace_root: str
    generated_at: str


@dataclass(frozen=True)
class TaskClassification:
    task_class: TaskClass
    visual_change: bool
    designer_required: bool
    estimated_complexity: Complexity


@dataclass(frozen=True)
class TargetFile:
    path: str
    exists: bool
    sha256_before: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_repo_path(self.path))


@dataclass(frozen=True)
class AcceptanceCriterion:
    id: str
    description: str
    kind: CriterionKind


@dataclass(frozen=True)
class ContentConstraints:
    must_contain: list[str]
    must_not_contain: list[str]
    preserve_imports: list[str]
    preserve_exports: list[str]
    max_added_lines: int | None
    max_removed_lines: int | None


@dataclass(frozen=True)
class ContextSlice:
    path: str
    kind: ContextSliceKind
    sha256: str
    content: str
    line_range: tuple[int, int] | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_repo_path(self.path))
        if self.line_range is not None:
            object.__setattr__(self, "line_range", tuple(self.line_range))


@dataclass(frozen=True)
class CoderPacket:
    target_file: TargetFile
    operation: CoderOperation
    acceptance_criteria: list[AcceptanceCriterion]
    constraints: ContentConstraints
    context_slices: list[ContextSlice]
    forbidden_paths: list[str]
    style_directives: list[str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "forbidden_paths",
            [_normalize_repo_path(path) for path in self.forbidden_paths],
        )


@dataclass(frozen=True)
class CoderResponse:
    status: CoderResponseStatus
    target_path: str
    replacement_content: str | None
    reasoning: str
    blocked_reason: str | None
    blocked_needed_context: str | None
    raw_response_excerpt: str = ""
    raw_response_length: int = 0
    parse_error_class: str = ""
    parse_error_message: str = ""
    json_attempt_count: int = 0
    coder_format_retry_count: int = 0
    last_json_error: str = ""
    structured_output_mode: str = ""
    file_block_repair_source: str = ""
    json_repair_source: str = ""
    markdown_fence_found: bool = False
    markdown_fence_stripped: bool = False
    markdown_fence_language: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_path", _normalize_repo_path(self.target_path))
        object.__setattr__(self, "reasoning", self.reasoning[:500])


@dataclass(frozen=True)
class CoderTaskSpec:
    schema_version: int
    task_type: TaskSpecType
    target: str
    allowed_files: list[str]
    forbidden_files: list[str]
    literal_requirements: list[str]
    verification: list[str]
    risk_tier: TaskSpecRiskTier
    source: str

    def __post_init__(self) -> None:
        target = _normalize_repo_path(self.target)
        object.__setattr__(self, "target", target)
        object.__setattr__(
            self,
            "allowed_files",
            [_normalize_repo_path(path) for path in self.allowed_files],
        )
        object.__setattr__(
            self,
            "forbidden_files",
            [_normalize_repo_path(path) for path in self.forbidden_files],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationCheck:
    id: str
    command: list[str]
    blocking: bool
    timeout_seconds: int


@dataclass(frozen=True)
class VerificationPlan:
    required_checks: list[VerificationCheck]
    designer_review_required: bool
    architect_review_required: bool


@dataclass(frozen=True)
class PlanBudget:
    max_coder_attempts: int
    max_total_seconds: int
    cloud_escalation_allowed: bool


@dataclass(frozen=True)
class ArchitectPlan:
    plan_id: str
    task_id: str
    schema_version: int
    created_at: str
    source_task: str
    bundle_snapshot: BundleSnapshot
    classification: TaskClassification
    coder_packet: CoderPacket
    verification_plan: VerificationPlan
    budget: PlanBudget

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ArchitectPlan:
        _reject_unknown_keys(cls, payload)
        payload = migrate_plan_payload(payload)
        schema_version = payload.get("schema_version")
        if schema_version != PLAN_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported ArchitectPlan schema_version {schema_version!r}; "
                f"expected {PLAN_SCHEMA_VERSION}."
            )
        return cls(
            plan_id=_require_str(payload, "plan_id"),
            task_id=_require_str(payload, "task_id"),
            schema_version=PLAN_SCHEMA_VERSION,
            created_at=_require_str(payload, "created_at"),
            source_task=_require_str(payload, "source_task"),
            bundle_snapshot=_bundle_snapshot_from_dict(
                _require_dict(payload, "bundle_snapshot")
            ),
            classification=_classification_from_dict(
                _require_dict(payload, "classification")
            ),
            coder_packet=_coder_packet_from_dict(_require_dict(payload, "coder_packet")),
            verification_plan=_verification_plan_from_dict(
                _require_dict(payload, "verification_plan")
            ),
            budget=_budget_from_dict(_require_dict(payload, "budget")),
        )


def task_spec_from_plan(plan: ArchitectPlan) -> CoderTaskSpec:
    return task_spec_from_packet(
        plan.coder_packet,
        verification_plan=plan.verification_plan,
    )


def task_spec_from_packet(
    packet: CoderPacket,
    *,
    verification_plan: VerificationPlan | None = None,
) -> CoderTaskSpec:
    target = packet.target_file.path
    literal_requirements = _dedupe_preserve_order(packet.constraints.must_contain)
    return CoderTaskSpec(
        schema_version=PLAN_SCHEMA_VERSION,
        task_type=_task_spec_type(packet),
        target=target,
        allowed_files=[target] if target else [],
        forbidden_files=list(packet.forbidden_paths),
        literal_requirements=literal_requirements,
        verification=_task_spec_verification(literal_requirements, verification_plan),
        risk_tier=_task_spec_risk_tier(packet),
        source="deterministic",
    )


def validate_task_spec_for_packet(
    task_spec: CoderTaskSpec,
    packet: CoderPacket,
) -> list[str]:
    errors: list[str] = []
    target = packet.target_file.path
    if task_spec.schema_version != PLAN_SCHEMA_VERSION:
        errors.append("schema_version")
    if not target:
        errors.append("target")
    if task_spec.target != target:
        errors.append("target_mismatch")
    if task_spec.allowed_files != [target]:
        errors.append("allowed_files")
    if any(_path_matches_forbidden_pattern(target, pattern) for pattern in task_spec.forbidden_files):
        errors.append("target_forbidden")
    if task_spec.task_type != _task_spec_type(packet):
        errors.append("task_type")
    if task_spec.source != "deterministic":
        errors.append("source")
    return errors


def _task_spec_type(packet: CoderPacket) -> TaskSpecType:
    if packet.operation == "create":
        return "create_new_file"
    if packet.operation == "delete":
        return "delete_file"
    return "modify_existing_file"


def _task_spec_risk_tier(packet: CoderPacket) -> TaskSpecRiskTier:
    if packet.operation == "delete":
        return "high"
    if packet.operation == "create":
        return "medium"
    return "low"


def _task_spec_verification(
    literal_requirements: list[str],
    verification_plan: VerificationPlan | None,
) -> list[str]:
    labels: list[str] = []
    checks = verification_plan.required_checks if verification_plan is not None else []
    for check in checks:
        labels.append(_verification_check_label(check.id))
    if not labels:
        labels.append("git apply check")
    if literal_requirements:
        labels.append("literal present")
    labels.append("target-only")
    return _dedupe_preserve_order(labels)


def _verification_check_label(check_id: str) -> str:
    normalized = check_id.replace("_", " ").replace("-", " ").strip().lower()
    if normalized == "git apply check":
        return normalized
    return normalized or "verification check"


def _path_matches_forbidden_pattern(path: str, pattern: str) -> bool:
    normalized = _normalize_repo_path(path)
    blocked = _normalize_repo_path(pattern)
    if not normalized or not blocked:
        return False
    if blocked.endswith("/*"):
        return normalized.startswith(blocked[:-1])
    if blocked.endswith("/"):
        return normalized.startswith(blocked)
    return normalized == blocked


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def save_plan(task_id: str, plan: ArchitectPlan) -> None:
    if plan.task_id != task_id:
        raise ValueError(f"Plan task_id {plan.task_id!r} does not match {task_id!r}.")
    from source_proxy.tasks import long_running as _tasks

    payload = json.dumps(plan.to_dict(), separators=(",", ":"), sort_keys=True)
    with closing(_tasks._connect()) as connection:
        _tasks._initialize_store(connection)
        cursor = connection.execute(
            """
            UPDATE long_running_tasks
            SET architect_plan_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (payload, _tasks._now_iso(), task_id),
        )
        if cursor.rowcount == 0:
            raise KeyError(f"Long-running task not found: {task_id}")
        connection.commit()


def load_plan(task_id: str) -> ArchitectPlan | None:
    from source_proxy.tasks import long_running as _tasks

    with closing(_tasks._connect()) as connection:
        _tasks._initialize_store(connection)
        row = connection.execute(
            """
            SELECT architect_plan_json
            FROM long_running_tasks
            WHERE id = ?
            """,
            (task_id,),
        ).fetchone()
    if row is None:
        raise KeyError(f"Long-running task not found: {task_id}")
    raw = row["architect_plan_json"]
    if not raw:
        return None
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise TypeError("Stored architect plan JSON must be an object.")
    return ArchitectPlan.from_dict(payload)


def migrate_plan_payload(payload: dict[str, Any]) -> dict[str, Any]:
    version = payload.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise TypeError("schema_version must be an integer.")
    if version > PLAN_SCHEMA_VERSION:
        raise PlanSchemaTooNew(
            f"ArchitectPlan schema_version {version} is newer than supported "
            f"{PLAN_SCHEMA_VERSION}."
        )
    migrated = dict(payload)
    while version < PLAN_SCHEMA_VERSION:
        migrator = PLAN_MIGRATORS.get(version)
        if migrator is None:
            raise ValueError(f"No migrator registered for ArchitectPlan schema_version {version}.")
        migrated = migrator(migrated)
        next_version = migrated.get("schema_version")
        if not isinstance(next_version, int) or next_version <= version:
            raise ValueError(f"Migrator for schema_version {version} did not advance version.")
        version = next_version
    return migrated


T = TypeVar("T")


def _bundle_snapshot_from_dict(payload: dict[str, Any]) -> BundleSnapshot:
    _reject_unknown_keys(BundleSnapshot, payload)
    return BundleSnapshot(
        bundle_path=_require_str(payload, "bundle_path"),
        bundle_sha256=_require_str(payload, "bundle_sha256"),
        workspace_root=_require_str(payload, "workspace_root"),
        generated_at=_require_str(payload, "generated_at"),
    )


def _classification_from_dict(payload: dict[str, Any]) -> TaskClassification:
    _reject_unknown_keys(TaskClassification, payload)
    return TaskClassification(
        task_class=_literal(payload, "task_class", {"implement", "refactor", "fix", "style", "explain"}),
        visual_change=_require_bool(payload, "visual_change"),
        designer_required=_require_bool(payload, "designer_required"),
        estimated_complexity=_literal(
            payload,
            "estimated_complexity",
            {"trivial", "small", "medium", "large"},
        ),
    )


def _target_file_from_dict(payload: dict[str, Any]) -> TargetFile:
    _reject_unknown_keys(TargetFile, payload)
    sha = payload.get("sha256_before")
    if sha is not None and not isinstance(sha, str):
        raise TypeError("sha256_before must be a string or null.")
    return TargetFile(
        path=_require_str(payload, "path"),
        exists=_require_bool(payload, "exists"),
        sha256_before=sha,
    )


def _criterion_from_dict(payload: dict[str, Any]) -> AcceptanceCriterion:
    _reject_unknown_keys(AcceptanceCriterion, payload)
    return AcceptanceCriterion(
        id=_require_str(payload, "id"),
        description=_require_str(payload, "description"),
        kind=_literal(payload, "kind", {"literal", "behavioral"}),
    )


def _constraints_from_dict(payload: dict[str, Any]) -> ContentConstraints:
    _reject_unknown_keys(ContentConstraints, payload)
    return ContentConstraints(
        must_contain=_require_str_list(payload, "must_contain"),
        must_not_contain=_require_str_list(payload, "must_not_contain"),
        preserve_imports=_require_str_list(payload, "preserve_imports"),
        preserve_exports=_require_str_list(payload, "preserve_exports"),
        max_added_lines=_optional_int(payload, "max_added_lines"),
        max_removed_lines=_optional_int(payload, "max_removed_lines"),
    )


def _context_slice_from_dict(payload: dict[str, Any]) -> ContextSlice:
    _reject_unknown_keys(ContextSlice, payload)
    line_range = payload.get("line_range")
    if line_range is not None:
        if (
            not isinstance(line_range, (list, tuple))
            or len(line_range) != 2
            or not all(isinstance(value, int) for value in line_range)
        ):
            raise TypeError("line_range must be a two-item integer sequence or null.")
        line_range = (line_range[0], line_range[1])
    return ContextSlice(
        path=_require_str(payload, "path"),
        kind=_literal(payload, "kind", {"target", "import", "sibling", "type_definition", "doc"}),
        sha256=_require_str(payload, "sha256"),
        content=_require_str(payload, "content"),
        line_range=line_range,
    )


def _coder_packet_from_dict(payload: dict[str, Any]) -> CoderPacket:
    _reject_unknown_keys(CoderPacket, payload)
    return CoderPacket(
        target_file=_target_file_from_dict(_require_dict(payload, "target_file")),
        operation=_literal(payload, "operation", {"edit", "create", "delete"}),
        acceptance_criteria=[
            _criterion_from_dict(item)
            for item in _require_dict_list(payload, "acceptance_criteria")
        ],
        constraints=_constraints_from_dict(_require_dict(payload, "constraints")),
        context_slices=[
            _context_slice_from_dict(item)
            for item in _require_dict_list(payload, "context_slices")
        ],
        forbidden_paths=_require_str_list(payload, "forbidden_paths"),
        style_directives=_require_str_list(payload, "style_directives"),
    )


def _verification_check_from_dict(payload: dict[str, Any]) -> VerificationCheck:
    _reject_unknown_keys(VerificationCheck, payload)
    return VerificationCheck(
        id=_require_str(payload, "id"),
        command=_require_str_list(payload, "command"),
        blocking=_require_bool(payload, "blocking"),
        timeout_seconds=_require_int(payload, "timeout_seconds"),
    )


def _verification_plan_from_dict(payload: dict[str, Any]) -> VerificationPlan:
    _reject_unknown_keys(VerificationPlan, payload)
    return VerificationPlan(
        required_checks=[
            _verification_check_from_dict(item)
            for item in _require_dict_list(payload, "required_checks")
        ],
        designer_review_required=_require_bool(payload, "designer_review_required"),
        architect_review_required=_require_bool(payload, "architect_review_required"),
    )


def _budget_from_dict(payload: dict[str, Any]) -> PlanBudget:
    _reject_unknown_keys(PlanBudget, payload)
    return PlanBudget(
        max_coder_attempts=_require_int(payload, "max_coder_attempts"),
        max_total_seconds=_require_int(payload, "max_total_seconds"),
        cloud_escalation_allowed=_require_bool(payload, "cloud_escalation_allowed"),
    )


def _reject_unknown_keys(cls: type[Any], payload: dict[str, Any]) -> None:
    allowed = {field.name for field in fields(cls)}
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError(
            f"Unknown field(s) for {cls.__name__}: {', '.join(sorted(unknown))}"
        )


def _require_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise TypeError(f"{key} must be an object.")
    return value


def _require_dict_list(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise TypeError(f"{key} must be a list of objects.")
    return value


def _require_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string.")
    return value


def _require_str_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError(f"{key} must be a list of strings.")
    return value


def _require_bool(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise TypeError(f"{key} must be a boolean.")
    return value


def _require_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{key} must be an integer.")
    return value


def _optional_int(payload: dict[str, Any], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{key} must be an integer or null.")
    return value


def _literal(payload: dict[str, Any], key: str, allowed: set[str]) -> Any:
    value = _require_str(payload, key)
    if value not in allowed:
        raise ValueError(f"{key} must be one of: {', '.join(sorted(allowed))}.")
    return value


def _normalize_repo_path(path: str) -> str:
    return normalize_repo_path_candidate(path)
