from __future__ import annotations

import ast
import hashlib
import json
import posixpath
import re
import subprocess
from fnmatch import fnmatchcase
from dataclasses import asdict, dataclass, fields, replace
from contextlib import closing
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence, TypeVar

from source_proxy.decision.proposal_task import effective_planning_task_text
from source_proxy.planning.migrations import PLAN_MIGRATORS
from source_proxy.safety.paths import (
    has_percent_encoded_path_syntax,
    normalize_repo_path_candidate,
    path_escapes_workspace,
)


PLAN_SCHEMA_VERSION = 1

TaskClass = Literal["implement", "refactor", "fix", "style", "explain"]
Complexity = Literal["trivial", "small", "medium", "large"]
CoderOperation = Literal["edit", "create", "delete"]
CriterionKind = Literal["literal", "behavioral"]
ContextSliceKind = Literal["target", "import", "sibling", "type_definition", "doc"]
CoderResponseStatus = Literal["ok", "blocked"]
TaskSpecType = Literal[
    "modify_existing_file",
    "create_new_file",
    "delete_file",
    "create_file_bundle",
]
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
    base = task_spec_from_packet(
        plan.coder_packet,
        verification_plan=plan.verification_plan,
    )
    allowed_files = canonical_task_spec_paths_from_plan(plan)
    if allowed_files == base.allowed_files:
        return base
    return CoderTaskSpec(
        schema_version=base.schema_version,
        task_type="create_file_bundle",
        target=base.target,
        allowed_files=allowed_files,
        forbidden_files=list(base.forbidden_files),
        literal_requirements=list(base.literal_requirements),
        verification=list(base.verification),
        risk_tier=base.risk_tier,
        source=base.source,
    )


def canonical_task_spec_paths_from_plan(plan: ArchitectPlan) -> list[str]:
    """Derive exact pre-dispatch write authority from persisted public intent.

    A Coder-selected path is never authority.  The primary target is always
    present; additional paths are admitted only when they are exact mutation
    paths already encoded in the persisted task or acceptance criteria.
    """

    target = _normalize_repo_path(plan.coder_packet.target_file.path)
    intended = review_intent_paths_from_plan(plan)
    allowed = [target] if target else []
    for path in intended:
        normalized = _normalize_repo_path(path)
        if (
            not normalized
            or normalized == target
            or path_escapes_workspace(normalized)
            or has_percent_encoded_path_syntax(normalized)
            or _path_matches_forbidden(
                normalized,
                plan.coder_packet.forbidden_paths,
            )
        ):
            continue
        allowed.append(normalized)
    return _dedupe_preserve_order(allowed)


_MAX_TRACKED_TEST_INDEX_BYTES = 1_000_000
_MAX_TRACKED_TEST_ARTIFACTS = 256
_MAX_TRACKED_TEST_ARTIFACT_BYTES = 256_000
_MAX_TRACKED_TEST_CONTENT_BYTES = 1_000_000


def bind_requested_artifacts_to_plan(
    plan: ArchitectPlan,
    workspace_root: Path,
    *,
    authorized_paths: Sequence[str] | None = None,
) -> ArchitectPlan:
    """Persist one exact existing test artifact requested by public intent.

    This is a pre-dispatch authority derivation.  It considers only bounded,
    tracked, regular workspace files and adds authority only when exactly one
    existing test artifact is structurally bound to the primary target.  A
    Coder response, changed-file list, or post-generation snapshot is never an
    input.
    """

    root = workspace_root.resolve()
    try:
        persisted_root = Path(plan.bundle_snapshot.workspace_root).resolve()
    except (OSError, RuntimeError, ValueError):
        return plan
    if (
        not root.is_dir()
        or persisted_root != root
        or not task_requests_test_artifact(
            effective_planning_task_text(plan.source_task)
        )
    ):
        return plan

    target = _normalize_repo_path(plan.coder_packet.target_file.path)
    if not target:
        return plan
    existing_intent = review_intent_paths_from_plan(plan)
    if any(
        path != target and _review_test_artifact_path(path)
        for path in existing_intent
    ):
        return plan

    scopes: list[str] | None = None
    if authorized_paths is not None:
        scopes = _dedupe_preserve_order(
            [
                _normalize_repo_path(str(path or ""))
                for path in authorized_paths
            ]
        )
        if (
            not scopes
            or len(scopes) != len(authorized_paths)
            or any(
                not path
                or path_escapes_workspace(path)
                or has_percent_encoded_path_syntax(path)
                for path in scopes
            )
        ):
            return plan

    snapshots = _tracked_test_artifact_snapshots(
        root,
        target=target,
        authorized_paths=scopes,
        forbidden_paths=plan.coder_packet.forbidden_paths,
    )
    bound_paths = [
        path
        for path, snapshot in snapshots.items()
        if _test_artifact_is_bound_to_target(path, snapshot, target)
    ]
    if len(bound_paths) != 1:
        return plan

    test_path = bound_paths[0]
    criterion = AcceptanceCriterion(
        id="server-bound-focused-test-artifact",
        description=(
            f"Update existing focused test artifact {test_path} "
            "for the requested behavior."
        ),
        kind="behavioral",
    )
    packet = replace(
        plan.coder_packet,
        acceptance_criteria=[
            *plan.coder_packet.acceptance_criteria,
            criterion,
        ],
    )
    return replace(plan, coder_packet=packet)


def _tracked_test_artifact_snapshots(
    root: Path,
    *,
    target: str,
    authorized_paths: list[str] | None,
    forbidden_paths: list[str],
) -> dict[str, dict[str, Any]]:
    try:
        listed = subprocess.run(
            ["git", "ls-files", "--cached", "-z", "--"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if (
        listed.returncode != 0
        or len(listed.stdout) > _MAX_TRACKED_TEST_INDEX_BYTES
    ):
        return {}
    try:
        raw_paths = listed.stdout.decode("utf-8", errors="strict").split("\0")
    except UnicodeDecodeError:
        return {}

    candidates: list[str] = []
    seen: set[str] = set()
    for raw_path in raw_paths:
        if not raw_path:
            continue
        path = _normalize_repo_path(raw_path)
        if (
            not path
            or path != raw_path.replace("\\", "/")
            or path in seen
            or path == target
            or path_escapes_workspace(path)
            or has_percent_encoded_path_syntax(path)
            or not _review_test_artifact_path(path)
            or (
                authorized_paths is not None
                and not _path_in_authorized_scope(path, authorized_paths)
            )
            or _path_matches_forbidden(path, forbidden_paths)
        ):
            continue
        seen.add(path)
        candidates.append(path)
    candidates.sort()
    if len(candidates) > _MAX_TRACKED_TEST_ARTIFACTS:
        return {}

    snapshots: dict[str, dict[str, Any]] = {}
    total_bytes = 0
    for path in candidates:
        candidate = _existing_regular_workspace_file(root, path)
        if candidate is None:
            continue
        try:
            with candidate.open("rb") as stream:
                raw = stream.read(_MAX_TRACKED_TEST_ARTIFACT_BYTES + 1)
        except OSError:
            return {}
        if len(raw) > _MAX_TRACKED_TEST_ARTIFACT_BYTES:
            return {}
        total_bytes += len(raw)
        if total_bytes > _MAX_TRACKED_TEST_CONTENT_BYTES:
            return {}
        try:
            content = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return {}
        snapshots[path] = {
            "exists": True,
            "content": content,
        }
    return snapshots


def _existing_regular_workspace_file(root: Path, path: str) -> Path | None:
    candidate = root
    for part in Path(path).parts:
        candidate = candidate / part
        if candidate.is_symlink():
            return None
    try:
        resolved = candidate.resolve()
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return None
    return candidate if candidate.is_file() else None


def review_task_spec_from_plan(
    plan: ArchitectPlan,
    changed_files: list[str],
    *,
    authorized_paths: list[str] | tuple[str, ...],
    artifact_snapshots: Mapping[str, Any] | None = None,
) -> CoderTaskSpec:
    """Reuse the exact pre-dispatch TaskSpec for semantic review.

    ``changed_files`` and post-generation snapshots are evidence, never an
    authority source.  They may prove that a candidate stayed inside the
    persisted exact-file contract, but they cannot add model-selected paths.
    """

    base = task_spec_from_plan(plan)
    normalized_changed = [
        _normalize_repo_path(str(path or "")) for path in changed_files
    ]
    exact_paths = _dedupe_preserve_order(normalized_changed)
    authority = _dedupe_preserve_order(
        [_normalize_repo_path(str(path or "")) for path in authorized_paths]
    )
    if (
        not exact_paths
        or len(exact_paths) != len(normalized_changed)
        or not authority
        or any(
            path_escapes_workspace(path)
            or has_percent_encoded_path_syntax(path)
            for path in [*exact_paths, *authority]
        )
        or base.target not in exact_paths
        or any(not _path_in_authorized_scope(path, authority) for path in exact_paths)
        or any(
            _path_matches_forbidden(path, base.forbidden_files)
            for path in exact_paths
        )
    ):
        raise ValueError("review_task_spec_missing_primary_target")
    if any(path not in base.allowed_files for path in exact_paths):
        exact_authority_paths = [
            path
            for path in authority
            if (
                path
                and not path.endswith("/")
                and not any(char in path for char in "*?[]{}")
            )
        ]
        if any(path not in exact_authority_paths for path in exact_paths):
            raise ValueError("review_task_spec_unrequested_changed_file")
        return CoderTaskSpec(
            schema_version=base.schema_version,
            task_type="create_file_bundle",
            target=base.target,
            allowed_files=exact_paths,
            forbidden_files=list(base.forbidden_files),
            literal_requirements=list(base.literal_requirements),
            verification=list(base.verification),
            risk_tier=base.risk_tier,
            source=base.source,
        )
    del artifact_snapshots
    return base


_PUBLIC_CALLABLE_NAME_PATTERNS = (
    re.compile(
        r"(?P<quote>[`'\"])(?P<name>[A-Za-z_][A-Za-z0-9_]{0,127})(?P=quote)"
        r"\s+(?:(?:service|helper|utility)\s+)?(?:function|callable)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:function|callable)\s+(?:(?:named|called)\s+)?"
        r"(?P<quote>[`'\"])(?P<name>[A-Za-z_][A-Za-z0-9_]{0,127})(?P=quote)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?P<name>[A-Za-z_][A-Za-z0-9_]{0,127}_[A-Za-z0-9_]+)"
        r"\s+(?:(?:service|helper|utility)\s+)?function\b",
        re.IGNORECASE,
    ),
)
_PUBLIC_COUNT_RESULT_RE = re.compile(
    r"\b(?:return|returns|returning|compute|computes|computing|report|reports|reporting)\b"
    r"[^.!?\n]{0,160}\b(?:count|number|how\s+many)\b",
    re.IGNORECASE,
)
_PUBLIC_FIXED_LITERAL_FILTER_RE = re.compile(
    r"\b(?:where|whose)\b[^.!?\n]{0,120}?"
    r"(?:[`'\"][A-Za-z_][A-Za-z0-9_]*[`'\"]|[A-Za-z_][A-Za-z0-9_]*)"
    r"\s+(?:must\s+)?(?:exactly\s+)?"
    r"(?:equals?|matches?|is(?:\s+equal\s+to)?)\s+(?:exactly\s+)?"
    r"[`'\"][^`'\"\n]{1,96}[`'\"]",
    re.IGNORECASE,
)
_PUBLIC_ZERO_PARAMETER_RE = re.compile(
    r"(?:\b(?:no|zero)\s+(?:required\s+)?"
    r"(?:parameters?|arguments?)\b"
    r"|\bwithout\s+(?:any\s+)?(?:required\s+)?"
    r"(?:parameters?|arguments?)\b"
    r"|\b(?:accepts?|takes?|receives?)\s+no\s+"
    r"(?:parameters?|arguments?)\b)",
    re.IGNORECASE,
)
_PUBLIC_EXPLICIT_PARAMETER_RE = re.compile(
    r"(?:\b(?:parameters?|arguments?)\b"
    r"|\b(?:accepts?|taking|takes?|receives?)\b"
    r"|\bgiven\b"
    r"|\b(?:provided|supplied|passed[-\s]+in|caller[-\s]+supplied)\b"
    r"|\binputs?\b)",
    re.IGNORECASE,
)
_PUBLIC_CALLABLE_REQUEST_RE = re.compile(
    r"\b(?:add|create|define|implement|introduce|provide|write|"
    r"must|needs?\s+to|shall|should)\b",
    re.IGNORECASE,
)
_PUBLIC_NEGATED_CALLABLE_REQUEST_RE = re.compile(
    r"\b(?:do\s+not|don't|never|cannot|can't|no\s+need\s+to|"
    r"(?:must|shall|should)\s+not)\s+"
    r"(?:add|change|create|define|extend|implement|introduce|modify|"
    r"provide|update|write)\b",
    re.IGNORECASE,
)
_PUBLIC_OPTIONAL_INTEGER_CALLABLE_PATTERNS = (
    re.compile(
        r"\b(?:add|implement|introduce|provide)\b"
        r"(?P<feature>[^.!?\n]{0,160}?)\bto\s+"
        r"(?P<callable_quote>[`'\"])"
        r"(?P<callable>[A-Za-z_][A-Za-z0-9_]{0,127})"
        r"(?P=callable_quote)\s+with\s+optional\s+"
        r"(?P<parameters>[^.!?\n]{1,240}?)\s+"
        r"(?:arguments?|parameters?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:change|extend|modify|update)\s+"
        r"(?P<callable_quote>[`'\"])"
        r"(?P<callable>[A-Za-z_][A-Za-z0-9_]{0,127})"
        r"(?P=callable_quote)\s+"
        r"(?:with|to\s+(?:accept|receive|take))\s+optional\s+"
        r"(?P<parameters>[^.!?\n]{1,240}?)\s+"
        r"(?:arguments?|parameters?)\b",
        re.IGNORECASE,
    ),
)
_PUBLIC_QUOTED_IDENTIFIER_RE = re.compile(
    r"(?P<quote>[`'\"])(?P<name>[A-Za-z_][A-Za-z0-9_]{0,127})(?P=quote)"
)
_PUBLIC_COLLECTIVE_INTEGER_BOUND_RE = re.compile(
    r"\b(?P<quantifier>both|all)\s+"
    r"(?:values|arguments|parameters)\s+"
    r"(?:must|shall|should|need(?:s)?\s+to)\s+be\s+"
    r"(?P<bound>non[-\s]+negative|positive)\s+integers?\b",
    re.IGNORECASE,
)
_PUBLIC_COLLECTIVE_INTEGER_LANGUAGE_RE = re.compile(
    r"\b(?:both|all)\s+(?:values|arguments|parameters)\b"
    r"[^.!?\n]{0,80}\bintegers?\b"
    r"|\bvalues\b[^.!?\n]{0,80}\bintegers?\b",
    re.IGNORECASE,
)
_PUBLIC_VALUE_ERROR_INVALID_RE = re.compile(
    r"\braise\s+(?:an?\s+)?[`'\"]?ValueError[`'\"]?\s+"
    r"for\s+invalid\s+"
    r"(?P<topic>(?:[A-Za-z_][A-Za-z0-9_]*\s+){0,3})"
    r"(?:values?|arguments?|parameters?)\b",
    re.IGNORECASE,
)
_PUBLIC_OPTIONAL_ARGUMENT_ANCHOR_RE = re.compile(
    r"\boptional\b[^.!?\n]{0,240}\b(?:arguments?|parameters?)\b",
    re.IGNORECASE,
)
_PUBLIC_INTEGER_LANGUAGE_RE = re.compile(
    r"\b(?:integers?|non[-\s]+negative|positive|"
    r"at\s+least\s+[0-9]{1,7})\b",
    re.IGNORECASE,
)
_PUBLIC_UPPER_BOUND_RE = re.compile(
    r"\b(?:at\s+most|no\s+more\s+than|not\s+greater\s+than|"
    r"no\s+greater\s+than|must\s+not\s+exceed|cannot\s+exceed|"
    r"can't\s+exceed|not\s+exceed|does(?:n't|\s+not)\s+exceed|"
    r"may\s+not\s+exceed|no\s+higher\s+than|no\s+larger\s+than|"
    r"no\s+bigger\s+than|not\s+above|not\s+over|up\s+to|"
    r"less\s+than|fewer\s+than|below|under|at\s+or\s+(?:below|under)|"
    r"bounded\s+above\s+by|"
    r"upper\s+bound|ceiling|maximum|max(?:imum)?\s+of)\b"
    r"|[0-9]+\s+or\s+(?:less|fewer)\b|<=|≤|(?<![<=>])<(?![<=>])",
    re.IGNORECASE,
)
_PUBLIC_CONTEXT_BREAK_RE = re.compile(
    r"\b(?:separately|unrelated|independently|elsewhere|"
    r"normally|usually|typically|preferably|ideally|maybe|"
    r"for\s+example|as\s+an?\s+example|hypothetically|"
    r"suppose|imagine)\b|(?<!\w)e\.g\.(?!\w)",
    re.IGNORECASE,
)
_PUBLIC_NEGATION_PREFIX_RE = re.compile(
    r"\b(?:do\s+not|don't|never|cannot|can't|no\s+need\s+to|"
    r"(?:must|shall|should)\s+not)\b",
    re.IGNORECASE,
)
_PUBLIC_COLLECTIVE_CONTINUATION_RE = re.compile(
    r"^\s*(?:both|all|values|arguments|parameters)\b"
    r"|^\s*(?:defaults?|by\s+default|when\s+(?:omitted|not\s+provided)|"
    r"if\s+omitted)\b",
    re.IGNORECASE,
)
_PUBLIC_SUBJECT_SWITCH_RE = re.compile(
    r"\b(?:and|but|while|whereas)\s+"
    r"[A-Za-z_][A-Za-z0-9_]*\s+"
    r"(?:must|shall|should|is|needs?)\b",
    re.IGNORECASE,
)
_PUBLIC_NULLABILITY_RE = re.compile(
    r"\b(?:None|null)\b",
    re.IGNORECASE,
)
_PUBLIC_UNSUPPORTED_INTEGER_DOMAIN_RE = re.compile(
    r"\b(?:odd|even|divisible|multiple\s+of|except|"
    r"excluding\s+[0-9]+|prime|bounded\s+by|capped\s+(?:at|by)|"
    r"unless|except\s+when|only\s+when)\b",
    re.IGNORECASE,
)
_PUBLIC_BOUNDISH_RE = re.compile(
    r"\b(?:integers?|non[-\s]+negative|positive|at\s+least|"
    r"greater\s+than|minimum|min(?:imum)?\s+of)\b",
    re.IGNORECASE,
)


def _optional_integer_callable_contract_candidate(task: str) -> dict[str, Any]:
    """Derive an explicit bounded numeric callable contract from public prose.

    The recognizer is intentionally narrow.  It requires one named callable,
    an explicit list of optional named arguments, an integer lower bound for
    every argument, and an explicit ``ValueError`` requirement. Truly absent
    anchors yield no authority; partial or ambiguous anchored prose is invalid.
    """

    planning_text = effective_planning_task_text(str(task or ""))
    if not planning_text:
        return {
            "ok": True,
            "skipped": True,
            "reason_code": "optional_integer_contract_not_explicit",
            "callable": None,
            "parameters": [],
            "invalid_exception": None,
        }
    numeric_anchor_present = (
        _PUBLIC_OPTIONAL_ARGUMENT_ANCHOR_RE.search(planning_text) is not None
        and _PUBLIC_INTEGER_LANGUAGE_RE.search(planning_text) is not None
    )
    if len(planning_text) > 12_000:
        return {
            "ok": not numeric_anchor_present,
            "skipped": not numeric_anchor_present,
            "reason_code": (
                "optional_integer_contract_input_too_large"
                if numeric_anchor_present
                else "optional_integer_contract_not_explicit"
            ),
            "callable": None,
            "parameters": [],
            "invalid_exception": None,
        }

    matches = [
        match
        for pattern in _PUBLIC_OPTIONAL_INTEGER_CALLABLE_PATTERNS
        for match in pattern.finditer(planning_text)
    ]
    if not numeric_anchor_present:
        return {
            "ok": True,
            "skipped": True,
            "reason_code": "optional_integer_contract_not_explicit",
            "callable": None,
            "parameters": [],
            "invalid_exception": None,
        }
    if not matches:
        return {
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_ambiguous",
            "callable": None,
            "parameters": [],
            "invalid_exception": None,
        }
    if len(matches) != 1:
        return {
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_ambiguous",
            "callable": None,
            "parameters": [],
            "invalid_exception": None,
        }

    match = matches[0]
    clause_start = max(
        planning_text.rfind(separator, 0, match.start())
        for separator in (".", "!", "?", "\n")
    )
    clause_end_candidates = [
        index
        for separator in (".", "!", "?", "\n")
        if (index := planning_text.find(separator, match.end())) >= 0
    ]
    clause_end = (
        min(clause_end_candidates) + 1
        if clause_end_candidates
        else len(planning_text)
    )
    request_clause = planning_text[clause_start + 1 : clause_end]
    request_prefix = planning_text[
        max(clause_start + 1, match.start() - 80) : match.start()
    ]
    if (
        _PUBLIC_NEGATED_CALLABLE_REQUEST_RE.search(request_clause) is not None
        or _PUBLIC_NEGATION_PREFIX_RE.search(request_prefix) is not None
    ):
        return {
            "ok": True,
            "skipped": True,
            "reason_code": "optional_integer_contract_negated",
            "callable": None,
            "parameters": [],
            "invalid_exception": None,
        }
    contract_context = planning_text[match.start() :]
    if _PUBLIC_INTEGER_LANGUAGE_RE.search(contract_context) is None:
        return {
            "ok": True,
            "skipped": True,
            "reason_code": "optional_integer_contract_not_explicit",
            "callable": None,
            "parameters": [],
            "invalid_exception": None,
        }
    if _PUBLIC_UPPER_BOUND_RE.search(planning_text) is not None:
        return {
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_unsupported_upper_bound",
            "callable": match.group("callable"),
            "parameters": [],
            "invalid_exception": None,
        }
    if _PUBLIC_NULLABILITY_RE.search(planning_text) is not None:
        return {
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_unsupported_nullability",
            "callable": match.group("callable"),
            "parameters": [],
            "invalid_exception": None,
        }
    if _PUBLIC_UNSUPPORTED_INTEGER_DOMAIN_RE.search(planning_text) is not None:
        return {
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_unsupported_domain",
            "callable": match.group("callable"),
            "parameters": [],
            "invalid_exception": None,
        }
    parameter_text = match.group("parameters")
    parameter_names = [
        token.group("name")
        for token in _PUBLIC_QUOTED_IDENTIFIER_RE.finditer(parameter_text)
    ]
    connector_text = _PUBLIC_QUOTED_IDENTIFIER_RE.sub("", parameter_text)
    connector_ok = (
        re.fullmatch(
            r"(?:\s|,|\band\b)*",
            connector_text,
            flags=re.IGNORECASE,
        )
        is not None
    )
    if (
        not connector_ok
        or not 1 <= len(parameter_names) <= 4
        or len(parameter_names) != len(set(parameter_names))
        or match.group("callable") in parameter_names
    ):
        return {
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_ambiguous",
            "callable": None,
            "parameters": [],
            "invalid_exception": None,
        }

    collective_minimum: int | None = None
    def context_link_is_broken(position: int) -> bool:
        clause_start = max(
            contract_context.rfind(separator, 0, position)
            for separator in (".", "!", "?", "\n")
        )
        return (
            _PUBLIC_CONTEXT_BREAK_RE.search(
                contract_context[clause_start + 1 : position]
            )
            is not None
        )

    first_context_clause_end_candidates = [
        index
        for separator in (".", "!", "?", "\n")
        if (index := contract_context.find(separator)) >= 0
    ]
    first_context_clause_end = (
        min(first_context_clause_end_candidates)
        if first_context_clause_end_candidates
        else len(contract_context)
    )

    def collective_is_linked(
        collective: re.Match[str],
    ) -> bool:
        if context_link_is_broken(collective.start()):
            return False
        if collective.start() <= first_context_clause_end:
            return True
        clause_start = max(
            contract_context.rfind(separator, 0, collective.start())
            for separator in (".", "!", "?", "\n")
        )
        clause_prefix = contract_context[
            clause_start + 1 : collective.end()
        ]
        return (
            _PUBLIC_COLLECTIVE_CONTINUATION_RE.search(clause_prefix)
            is not None
        )

    collective_matches = [
        collective
        for collective in _PUBLIC_COLLECTIVE_INTEGER_BOUND_RE.finditer(
            contract_context
        )
        if collective_is_linked(collective)
    ]
    for collective in collective_matches:
        quantifier = collective.group("quantifier").lower()
        if quantifier == "both" and len(parameter_names) != 2:
            return {
                "ok": False,
                "skipped": False,
                "reason_code": "optional_integer_contract_ambiguous",
                "callable": match.group("callable"),
                "parameters": [],
                "invalid_exception": None,
            }
        inferred = (
            0
            if re.sub(r"[-\s]+", "", collective.group("bound").lower())
            == "nonnegative"
            else 1
        )
        if collective_minimum is not None and collective_minimum != inferred:
            return {
                "ok": False,
                "skipped": False,
                "reason_code": "optional_integer_contract_ambiguous",
                "callable": match.group("callable"),
                "parameters": [],
                "invalid_exception": None,
            }
        collective_minimum = inferred

    parameters: list[dict[str, Any]] = []
    parameter_references: list[tuple[int, int, str]] = []
    for parameter_name in parameter_names:
        reference_pattern = re.compile(
            rf"(?:[`'\"]{re.escape(parameter_name)}[`'\"]"
            rf"|(?<![A-Za-z0-9_`'\"])"
            rf"{re.escape(parameter_name)}"
            r"(?![A-Za-z0-9_`'\"])"
            r"(?=\s+(?:must|shall|should|needs?|is|at\s+least)))"
        )
        parameter_references.extend(
            (reference.start(), reference.end(), parameter_name)
            for reference in reference_pattern.finditer(contract_context)
        )
    parameter_references.sort(key=lambda item: (item[0], item[1], item[2]))

    def identifier_fragment(index: int) -> str:
        _start, reference_end, _name = parameter_references[index]
        next_identifier_start = (
            parameter_references[index + 1][0]
            if index + 1 < len(parameter_references)
            else len(contract_context)
        )
        punctuation_positions = [
            position
            for punctuation in (".", "!", "?", "\n")
            if (
                position := contract_context.find(
                    punctuation,
                    reference_end,
                )
            )
            >= 0
        ]
        fragment_end = min(
            [
                next_identifier_start,
                *(punctuation_positions or [len(contract_context)]),
                reference_end + 120,
            ]
        )
        fragment = contract_context[reference_end:fragment_end]
        subject_switch = _PUBLIC_SUBJECT_SWITCH_RE.search(fragment)
        if subject_switch is not None:
            fragment = fragment[: subject_switch.start()]
        semicolon = fragment.find(";")
        return fragment if semicolon < 0 else fragment[:semicolon]

    linked_integer_anchor = bool(collective_matches) or any(
        collective_is_linked(language_match)
        for language_match in _PUBLIC_COLLECTIVE_INTEGER_LANGUAGE_RE.finditer(
            contract_context
        )
    )
    linked_integer_anchor = linked_integer_anchor or any(
        reference_name in parameter_names
        and _PUBLIC_INTEGER_LANGUAGE_RE.search(identifier_fragment(index))
        is not None
        for index, (_start, _end, reference_name) in enumerate(
            parameter_references
        )
    )
    if not linked_integer_anchor:
        return {
            "ok": True,
            "skipped": True,
            "reason_code": "optional_integer_contract_not_explicit",
            "callable": None,
            "parameters": [],
            "invalid_exception": None,
        }

    for name in parameter_names:
        qualitative_minima: set[int] = set()
        at_least_minima: set[int] = set()
        integer_explicit = collective_minimum is not None
        for index, (_start, _end, reference_name) in enumerate(
            parameter_references
        ):
            if reference_name != name:
                continue
            fragment = identifier_fragment(index)
            for bound_match in re.finditer(
                r"\b(?P<bound>non[-\s]+negative|positive)\s+integer\b",
                fragment,
                flags=re.IGNORECASE,
            ):
                integer_explicit = True
                bound = re.sub(
                    r"[-\s]+",
                    "",
                    bound_match.group("bound").lower(),
                )
                qualitative_minima.add(
                    0 if bound == "nonnegative" else 1
                )
            for minimum_match in re.finditer(
                r"\bat\s+least\s+(?P<minimum>[0-9]{1,7})\b",
                fragment,
                flags=re.IGNORECASE,
            ):
                at_least_minima.add(
                    int(minimum_match.group("minimum"))
                )
                if re.search(r"\binteger\b", fragment, re.IGNORECASE):
                    integer_explicit = True

        if (
            not integer_explicit
            or len(qualitative_minima) > 1
            or len(at_least_minima) > 1
            or any(
                minimum > 1_000_000
                for minimum in [*qualitative_minima, *at_least_minima]
            )
        ):
            return {
                "ok": False,
                "skipped": False,
                "reason_code": (
                    "optional_integer_contract_ambiguous"
                    if len(qualitative_minima) > 1
                    or len(at_least_minima) > 1
                    else "optional_integer_contract_incomplete"
                ),
                "callable": match.group("callable"),
                "parameters": [],
                "invalid_exception": None,
            }
        explicit_minima = [
            *([collective_minimum] if collective_minimum is not None else []),
            *qualitative_minima,
            *at_least_minima,
        ]
        if not explicit_minima:
            return {
                "ok": False,
                "skipped": False,
                "reason_code": "optional_integer_contract_incomplete",
                "callable": match.group("callable"),
                "parameters": [],
                "invalid_exception": None,
            }
        parameters.append(
            {
                "name": name,
                "minimum": max(explicit_minima),
            }
        )

    request_words = {
        word.lower()
        for word in re.findall(
            r"[A-Za-z_][A-Za-z0-9_]*",
            match.group(0),
        )
    }
    linked_value_error_matches = []
    for value_error_match in _PUBLIC_VALUE_ERROR_INVALID_RE.finditer(
        contract_context
    ):
        topic_words = {
            word.lower()
            for word in re.findall(
                r"[A-Za-z_][A-Za-z0-9_]*",
                value_error_match.group("topic") or "",
            )
        }
        if (
            not topic_words
            or topic_words & request_words
            or topic_words & {name.lower() for name in parameter_names}
        ):
            linked_value_error_matches.append(value_error_match)
    if len(linked_value_error_matches) != 1:
        return {
            "ok": False,
            "skipped": False,
            "reason_code": (
                "optional_integer_contract_ambiguous"
                if len(linked_value_error_matches) > 1
                else "optional_integer_contract_incomplete"
            ),
            "callable": match.group("callable"),
            "parameters": parameters,
            "invalid_exception": None,
        }

    return {
        "ok": True,
        "skipped": False,
        "reason_code": "",
        "callable": match.group("callable"),
        "parameters": parameters,
        "invalid_exception": "ValueError",
    }


def optional_integer_callable_contract(task: str) -> dict[str, Any]:
    """Derive one exact lower-bounded integer contract from public prose.

    The older candidate recognizer remains a defense-in-depth comparison, but
    it never grants authority.  This boundary independently binds one
    affirmative callable request, its exact parameter subjects, pure
    lower-bound clauses, and one callable-owned ``ValueError`` duty.  Any
    partial, contradictory, relational, detached, or unsupported constraint
    fails closed.
    """

    planning_text = effective_planning_task_text(str(task or ""))
    absent = {
        "ok": True,
        "skipped": True,
        "reason_code": "optional_integer_contract_not_explicit",
        "callable": None,
        "parameters": [],
        "invalid_exception": None,
    }
    if not planning_text:
        return absent

    numeric_anchor_present = (
        _PUBLIC_OPTIONAL_ARGUMENT_ANCHOR_RE.search(planning_text) is not None
        and _PUBLIC_INTEGER_LANGUAGE_RE.search(planning_text) is not None
    )
    if len(planning_text) > 12_000:
        if not numeric_anchor_present:
            return absent
        return {
            **absent,
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_input_too_large",
        }

    request_matches = [
        match
        for pattern in _PUBLIC_OPTIONAL_INTEGER_CALLABLE_PATTERNS
        for match in pattern.finditer(planning_text)
    ]
    if not request_matches:
        if not numeric_anchor_present:
            return absent
        return {
            **absent,
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_ambiguous",
        }
    if len(request_matches) != 1:
        return {
            **absent,
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_ambiguous",
        }

    request = request_matches[0]
    sentence_start = max(
        planning_text.rfind(separator, 0, request.start())
        for separator in (".", "!", "?", "\n")
    )
    sentence_end_candidates = [
        position
        for separator in (".", "!", "?", "\n")
        if (position := planning_text.find(separator, request.end())) >= 0
    ]
    sentence_end = (
        min(sentence_end_candidates)
        if sentence_end_candidates
        else len(planning_text)
    )
    if planning_text[: sentence_start + 1].strip():
        return {
            **absent,
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_ambiguous",
            "callable": request.group("callable"),
        }
    request_sentence = planning_text[sentence_start + 1 : sentence_end]
    request_prefix = planning_text[sentence_start + 1 : request.start()]
    request_suffix = planning_text[request.end() : sentence_end]
    request_authority_text = planning_text[
        sentence_start + 1 : request.end()
    ]
    if (
        _PUBLIC_NEGATED_CALLABLE_REQUEST_RE.search(request_sentence)
        is not None
        or _PUBLIC_NEGATION_PREFIX_RE.search(request_prefix) is not None
        or re.search(
            r"\b(?:not|never|forbidden|prohibited|avoid|decline|refuse)\b",
            request_authority_text,
            flags=re.IGNORECASE,
        )
        is not None
    ):
        return {
            **absent,
            "reason_code": "optional_integer_contract_negated",
        }
    if (
        re.fullmatch(
            r"\s*(?:"
            r"(?:please|kindly)\s+"
            r"|(?:(?:can|could|would)\s+you(?:\s+please)?|"
            r"please\s+(?:can|could|would)\s+you)\s+"
            r"|(?:task|request|requirement)\s*:\s*"
            r")?",
            request_prefix,
            flags=re.IGNORECASE,
        )
        is None
        or _PUBLIC_CONTEXT_BREAK_RE.search(request_prefix) is not None
    ):
        return absent
    if request_suffix.strip():
        return {
            **absent,
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_ambiguous",
            "callable": request.group("callable"),
        }
    feature_text = request.groupdict().get("feature")
    if feature_text is not None:
        normalized_feature = " ".join(feature_text.split())
        if normalized_feature.lower() not in {
            "pagination",
            "paging",
            "pagination support",
            "paging support",
        }:
            return {
                **absent,
                "ok": False,
                "skipped": False,
                "reason_code": "optional_integer_contract_ambiguous",
                "callable": request.group("callable"),
            }

    parameter_text = request.group("parameters")
    parameter_tokens = list(
        _PUBLIC_QUOTED_IDENTIFIER_RE.finditer(parameter_text)
    )
    parameter_names = [
        token.group("name")
        for token in parameter_tokens
    ]
    parameter_separators = [
        parameter_text[left.end() : right.start()]
        for left, right in zip(
            parameter_tokens,
            parameter_tokens[1:],
            strict=False,
        )
    ]
    parameter_structure_ok = bool(parameter_tokens) and not (
        parameter_text[: parameter_tokens[0].start()].strip()
        or parameter_text[parameter_tokens[-1].end() :].strip()
    )
    if parameter_structure_ok and parameter_separators:
        for index, separator in enumerate(parameter_separators):
            is_final = index == len(parameter_separators) - 1
            allowed = (
                r"\s*(?:,|and|,\s*and)\s*"
                if is_final
                else r"\s*,\s*"
            )
            if re.fullmatch(
                allowed,
                separator,
                flags=re.IGNORECASE,
            ) is None:
                parameter_structure_ok = False
                break
    if (
        not parameter_structure_ok
        or not 1 <= len(parameter_names) <= 4
        or len(parameter_names) != len(set(parameter_names))
        or request.group("callable") in parameter_names
    ):
        return {
            **absent,
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_ambiguous",
        }

    anchored_text = planning_text[request.start() :]
    if _PUBLIC_UPPER_BOUND_RE.search(planning_text) is not None:
        return {
            **absent,
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_unsupported_upper_bound",
            "callable": request.group("callable"),
        }
    if _PUBLIC_NULLABILITY_RE.search(planning_text) is not None:
        return {
            **absent,
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_unsupported_nullability",
            "callable": request.group("callable"),
        }
    if _PUBLIC_UNSUPPORTED_INTEGER_DOMAIN_RE.search(planning_text) is not None:
        return {
            **absent,
            "ok": False,
            "skipped": False,
            "reason_code": "optional_integer_contract_unsupported_domain",
            "callable": request.group("callable"),
        }

    def invalid(
        reason_code: str = "optional_integer_contract_incomplete",
        *,
        parameters: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "ok": False,
            "skipped": False,
            "reason_code": reason_code,
            "callable": request.group("callable"),
            "parameters": list(parameters or []),
            "invalid_exception": None,
        }

    def numeric_connector_is_exact(connector: str) -> bool:
        return (
            re.fullmatch(
                r"\s*(?:"
                r"and\s+"
                r"|,\s*(?:(?:and|with)\s+)?"
                r"|\(\s*with\s+"
                r")",
                connector,
                flags=re.IGNORECASE,
            )
            is not None
        )

    def sentence_prefix(position: int) -> str:
        start = max(
            anchored_text.rfind(separator, 0, position)
            for separator in (".", "!", "?", "\n")
        )
        return anchored_text[start + 1 : position]

    def context_is_detached(position: int) -> bool:
        return (
            _PUBLIC_CONTEXT_BREAK_RE.search(sentence_prefix(position))
            is not None
        )

    collective_re = re.compile(
        r"\b(?P<quantifier>both|all)\s+"
        r"(?:values|arguments|parameters)\s+"
        r"(?:must|shall|should|need(?:s)?\s+to)\s+be\s+"
        r"(?:(?P<quality>non[-\s]+negative|positive)\s+)?"
        r"integers?\b",
        re.IGNORECASE,
    )
    collective_type = False
    collective_minimum: int | None = None
    accepted_spans: list[tuple[int, int]] = [
        (0, request.end() - request.start())
    ]
    numeric_spans: list[tuple[int, int]] = []
    detached_numeric_seen = False
    collective_matches = list(collective_re.finditer(anchored_text))
    linked_collectives: list[re.Match[str]] = []
    for collective in collective_matches:
        prefix = sentence_prefix(collective.start()).strip()
        in_request_sentence = collective.start() <= (
            sentence_end - request.start()
        )
        linked_prefix = (
            not prefix
            or (
                in_request_sentence
                and re.fullmatch(
                    r"[\s,;:()\-]*",
                    anchored_text[
                        request.end() - request.start() : collective.start()
                    ],
                )
                is not None
            )
            or re.fullmatch(
                r"defaults?\s+should\s+still\s+return\s+all\s+records,\s*",
                prefix,
                flags=re.IGNORECASE,
            )
            is not None
        )
        if context_is_detached(collective.start()) or not linked_prefix:
            detached_numeric_seen = True
            continue
        linked_collectives.append(collective)
    if len(linked_collectives) > 1:
        return invalid("optional_integer_contract_ambiguous")
    if linked_collectives:
        collective = linked_collectives[0]
        if (
            collective.group("quantifier").lower() == "both"
            and len(parameter_names) != 2
        ):
            return invalid("optional_integer_contract_ambiguous")
        collective_type = True
        quality = collective.group("quality")
        if quality:
            normalized = re.sub(r"[-\s]+", "", quality.lower())
            collective_minimum = 0 if normalized == "nonnegative" else 1
        accepted_spans.append(collective.span())
        numeric_spans.append(collective.span())

    parameter_atoms: dict[str, list[tuple[int, bool, tuple[int, int]]]] = {
        name: [] for name in parameter_names
    }
    detached_parameter_constraint = False
    for name in parameter_names:
        subject = (
            rf"(?:[`'\"]{re.escape(name)}[`'\"]"
            rf"|(?<![A-Za-z0-9_`'\"]){re.escape(name)}"
            r"(?![A-Za-z0-9_`'\"]))"
        )
        atom_re = re.compile(
            subject
            + r"\s+(?:(?:must|shall|should|need(?:s)?\s+to|is)"
            r"\s+(?:be\s+)?|)"
            r"(?P<bound>"
            r"(?:an?\s+)?(?P<quality>non[-\s]+negative|positive)"
            r"(?P<integer>\s+integer)?"
            r"|at\s+least\s+(?P<minimum>[0-9]{1,7})"
            r"(?![A-Za-z0-9_]|[.,][0-9])"
            r"|>=\s*(?P<symbolic_minimum>[0-9]{1,7})"
            r"(?![A-Za-z0-9_]|[.,][0-9])"
            r")"
            r"(?:\s+when\s+(?:provided|supplied|passed))?"
            r"(?=\s*(?:[,;.)]|\band\b|$))",
            re.IGNORECASE,
        )
        for atom in atom_re.finditer(anchored_text):
            if atom.start() < request.end() - request.start():
                continue
            prefix = sentence_prefix(atom.start())
            prefix_start = atom.start() - len(prefix)
            preceding_spans = [
                (start, end)
                for start, end in accepted_spans
                if end <= atom.start() and end >= prefix_start
            ]
            if prefix.strip():
                if not preceding_spans:
                    detached_parameter_constraint = True
                    continue
                preceding_end = max(end for _start, end in preceding_spans)
                connector = anchored_text[preceding_end : atom.start()]
                if not numeric_connector_is_exact(connector):
                    detached_parameter_constraint = True
                    continue
            if (
                _PUBLIC_CONTEXT_BREAK_RE.search(prefix) is not None
                or re.search(
                    r"\b(?:does?\s+not|do\s+not|need\s+not|"
                    r"never|no\s+need\s+to)\b",
                    prefix[-80:],
                    flags=re.IGNORECASE,
                )
                is not None
            ):
                detached_parameter_constraint = True
                continue
            quality = atom.group("quality")
            if quality:
                normalized = re.sub(r"[-\s]+", "", quality.lower())
                minimum = 0 if normalized.endswith("nonnegative") else 1
            else:
                raw_minimum = (
                    atom.group("minimum") or atom.group("symbolic_minimum")
                )
                minimum = int(raw_minimum)
            if minimum > 1_000_000:
                return invalid("optional_integer_contract_ambiguous")
            integer_explicit = atom.group("integer") is not None
            parameter_atoms[name].append(
                (minimum, integer_explicit, atom.span())
            )
            accepted_spans.append(atom.span())
            numeric_spans.append(atom.span())

    def occurrence_is_accepted(position: int) -> bool:
        return any(start <= position < end for start, end in accepted_spans)

    residual_constraint_seen = False
    residual_vocabulary = re.compile(
        r"\b(?:must|shall|should|need(?:s)?|is|are|not|never|"
        r"integers?|non[-\s]+negative|positive|at\s+least|"
        r"greater\s+than|minimum|min(?:imum)?\s+of|"
        r"unchanged|provided|supplied|passed)\b|>=|>",
        re.IGNORECASE,
    )
    pre_request_text = planning_text[: request.start()]
    for name in parameter_names:
        pre_request_reference = re.compile(
            rf"(?:[`'\"]{re.escape(name)}[`'\"]"
            rf"|(?<![A-Za-z0-9_`'\"]){re.escape(name)}"
            r"(?![A-Za-z0-9_`'\"]))",
            re.IGNORECASE,
        )
        for reference in pre_request_reference.finditer(pre_request_text):
            _ = reference
            return invalid("optional_integer_contract_ambiguous")
    for name in parameter_names:
        reference_re = re.compile(
            rf"(?:[`'\"]{re.escape(name)}[`'\"]"
            rf"|(?<![A-Za-z0-9_`'\"]){re.escape(name)}"
            r"(?![A-Za-z0-9_`'\"]))",
            re.IGNORECASE,
        )
        for reference in reference_re.finditer(anchored_text):
            if reference.start() < request.end() - request.start():
                continue
            if occurrence_is_accepted(reference.start()):
                continue
            following = anchored_text[reference.end() :]
            following = re.split(r"[.!?\n;]", following, maxsplit=1)[0]
            if residual_vocabulary.search(following) is None:
                continue
            residual_constraint_seen = True

    if not linked_collectives and all(
        not atoms for atoms in parameter_atoms.values()
    ):
        if detached_parameter_constraint:
            return invalid("optional_integer_contract_ambiguous")
        linked_unparsed_numeric = False
        for sentence_match in re.finditer(
            r"[^.!?\n]+(?:[.!?]+|$)",
            anchored_text[
                request.end() - request.start() :
            ],
        ):
            sentence = sentence_match.group(0).strip()
            if _PUBLIC_INTEGER_LANGUAGE_RE.search(sentence) is None:
                continue
            if _PUBLIC_CONTEXT_BREAK_RE.search(sentence) is not None:
                continue
            mentions_parameter = any(
                re.search(
                    rf"(?:[`'\"]{re.escape(name)}[`'\"]"
                    rf"|(?<![A-Za-z0-9_`'\"]){re.escape(name)}"
                    r"(?![A-Za-z0-9_`'\"]))",
                    sentence,
                    flags=re.IGNORECASE,
                )
                is not None
                for name in parameter_names
            )
            pronoun_link = (
                re.match(
                    r"^\s*(?:both|all|values?|arguments?|parameters?)\b",
                    sentence,
                    flags=re.IGNORECASE,
                )
                is not None
            )
            if mentions_parameter or pronoun_link:
                linked_unparsed_numeric = True
                break
        if not linked_unparsed_numeric:
            return absent
        return invalid()

    if detached_parameter_constraint:
        residual_constraint_seen = True
    if any(len(atoms) > 1 for atoms in parameter_atoms.values()):
        return invalid("optional_integer_contract_ambiguous")

    parameters: list[dict[str, Any]] = []
    for name in parameter_names:
        atoms = parameter_atoms[name]
        if not collective_type and (
            not atoms or atoms[0][1] is not True
        ):
            return invalid()
        explicit_minimum = atoms[0][0] if atoms else None
        if (
            collective_minimum is not None
            and explicit_minimum is not None
            and explicit_minimum < collective_minimum
        ):
            return invalid("optional_integer_contract_ambiguous")
        minima = [
            value
            for value in (collective_minimum, explicit_minimum)
            if value is not None
        ]
        if not minima:
            if (
                detached_numeric_seen
                and not linked_collectives
                and all(not items for items in parameter_atoms.values())
            ):
                return absent
            return invalid()
        parameters.append({"name": name, "minimum": max(minima)})

    if residual_constraint_seen:
        return invalid("optional_integer_contract_ambiguous")

    callable_name = request.group("callable")
    value_error_re = re.compile(
        r"(?:^|[.!?;\n]\s*)"
        r"(?P<owner>"
        r"raise"
        r"|(?:[`'\"]?"
        + re.escape(callable_name)
        + r"[`'\"]?)\s+(?:must|shall|should)\s+raise"
        r")\s+(?:an?\s+)?[`'\"]?ValueError[`'\"]?\s+"
        r"for\s+invalid\s+"
        r"(?P<topic>(?:[A-Za-z_][A-Za-z0-9_]*\s+){0,3})"
        r"(?:values?|arguments?|parameters?)\b",
        re.IGNORECASE,
    )
    linked_value_errors = []
    for value_error_match in value_error_re.finditer(anchored_text):
        suffix_end_candidates = [
            position
            for separator in (".", "!", "?", "\n")
            if (
                position := anchored_text.find(
                    separator,
                    value_error_match.end(),
                )
            )
            >= 0
        ]
        suffix_end = (
            min(suffix_end_candidates)
            if suffix_end_candidates
            else len(anchored_text)
        )
        if not anchored_text[value_error_match.end() : suffix_end].strip():
            linked_value_errors.append(value_error_match)
    all_value_errors = list(
        _PUBLIC_VALUE_ERROR_INVALID_RE.finditer(anchored_text)
    )
    if len(linked_value_errors) != 1 or len(all_value_errors) != 1:
        return invalid(
            "optional_integer_contract_ambiguous"
            if len(all_value_errors) > 1
            else "optional_integer_contract_incomplete",
            parameters=parameters,
        )
    value_error = linked_value_errors[0]
    topic_phrase = " ".join(
        str(value_error.group("topic") or "").lower().split()
    )
    if topic_phrase not in {
        "",
        "argument",
        "arguments",
        "parameter",
        "parameters",
        "pagination",
        "paging",
    }:
        return invalid(parameters=parameters)

    ordered_numeric_spans = sorted(set(numeric_spans))
    seen_numeric_spans: set[tuple[int, int]] = set()
    seen_error_sentence = False
    for sentence_match in re.finditer(
        r"[^.!?\n]+(?:[.!?]+|$)",
        anchored_text,
    ):
        raw_sentence = sentence_match.group(0)
        leading = len(raw_sentence) - len(raw_sentence.lstrip())
        body = raw_sentence.strip()
        body = body.rstrip(".!?").rstrip()
        if not body:
            continue
        body_start = sentence_match.start() + leading
        body_end = body_start + len(body)
        request_end = request.end() - request.start()
        if body_start == 0 and body_end == request_end:
            continue
        if "ValueError" in body:
            if seen_error_sentence:
                return invalid(
                    "optional_integer_contract_ambiguous",
                    parameters=parameters,
                )
            if not (
                value_error.start("owner") == body_start
                and value_error.end() == body_end
                and value_error.start() < body_end
                and value_error.end() > body_start
            ):
                return invalid(parameters=parameters)
            seen_error_sentence = True
            continue
        if seen_error_sentence:
            return invalid(
                "optional_integer_contract_ambiguous",
                parameters=parameters,
            )
        sentence_spans = [
            span
            for span in ordered_numeric_spans
            if body_start <= span[0] and span[1] <= body_end
        ]
        if not sentence_spans:
            return invalid(
                "optional_integer_contract_ambiguous",
                parameters=parameters,
            )
        prefix = anchored_text[body_start : sentence_spans[0][0]]
        if prefix.strip() and (
            re.fullmatch(
                r"defaults?\s+should\s+still\s+return\s+all\s+records,\s*",
                prefix,
                flags=re.IGNORECASE,
            )
            is None
        ):
            return invalid(
                "optional_integer_contract_ambiguous",
                parameters=parameters,
            )
        for previous, following in zip(
            sentence_spans,
            sentence_spans[1:],
            strict=False,
        ):
            connector = anchored_text[previous[1] : following[0]]
            if not numeric_connector_is_exact(connector):
                return invalid(
                    "optional_integer_contract_ambiguous",
                    parameters=parameters,
                )
        suffix = anchored_text[sentence_spans[-1][1] : body_end]
        suffix_is_empty = (
            re.fullmatch(r"\s*\)*\s*", suffix) is not None
        )
        suffix_is_preservation = (
            re.fullmatch(
                r"\s*\)*\s*,?\s*and\s+the\s+function\s+"
                r"must\s+never\s+mutate\s+"
                r"(?:the\s+module(?:'s|’s)\s+stored\s+records|"
                r"(?:the\s+)?stored\s+records|(?:the\s+)?records)\s*",
                suffix,
                flags=re.IGNORECASE,
            )
            is not None
        )
        if not suffix_is_empty and not suffix_is_preservation:
            return invalid(
                "optional_integer_contract_ambiguous",
                parameters=parameters,
            )
        seen_numeric_spans.update(sentence_spans)
    if (
        seen_numeric_spans != set(ordered_numeric_spans)
        or not seen_error_sentence
    ):
        return invalid(parameters=parameters)

    strict_result = {
        "ok": True,
        "skipped": False,
        "reason_code": "",
        "callable": callable_name,
        "parameters": parameters,
        "invalid_exception": "ValueError",
    }
    candidate = _optional_integer_callable_contract_candidate(planning_text)
    if (
        candidate.get("ok") is True
        and candidate.get("skipped") is not True
        and {
            "callable": candidate.get("callable"),
            "parameter_names": [
                item.get("name")
                for item in candidate.get("parameters", [])
                if isinstance(item, Mapping)
            ],
        }
        != {
            "callable": strict_result["callable"],
            "parameter_names": [
                item["name"] for item in strict_result["parameters"]
            ],
        }
    ):
        return invalid("optional_integer_contract_ambiguous")
    return strict_result


def optional_integer_callable_shape_check(
    task: str,
    python_source: str,
) -> dict[str, Any]:
    """Check the explicit optional-argument shape without executing source."""

    contract = optional_integer_callable_contract(task)
    if contract.get("skipped") is True:
        return {
            **contract,
            "missing_parameters": [],
            "violations": [],
        }
    if contract.get("ok") is not True:
        return {
            **contract,
            "missing_parameters": [],
            "violations": [
                {
                    "callable": contract.get("callable"),
                    "reason": contract.get("reason_code")
                    or "optional_integer_contract_invalid",
                }
            ],
        }
    try:
        tree = ast.parse(str(python_source or ""))
    except (SyntaxError, ValueError):
        return {
            **contract,
            "ok": False,
            "reason_code": "optional_integer_callable_source_invalid",
            "missing_parameters": [],
            "violations": [],
        }

    callable_name = str(contract["callable"])
    definitions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == callable_name
    ]
    violations: list[dict[str, Any]] = []
    if len(definitions) != 1:
        return {
            **contract,
            "ok": False,
            "reason_code": "optional_integer_callable_shape_mismatch",
            "missing_parameters": (
                [item["name"] for item in contract["parameters"]]
                if not definitions
                else []
            ),
            "violations": [
                {
                    "callable": callable_name,
                    "reason": (
                        "missing_module_callable"
                        if not definitions
                        else "ambiguous_module_callable"
                    ),
                }
            ],
        }

    definition = definitions[0]
    if isinstance(definition, ast.AsyncFunctionDef):
        violations.append(
            {"callable": callable_name, "reason": "async_callable_not_supported"}
        )
    positional_only = {
        argument.arg for argument in definition.args.posonlyargs
    }
    positional = [
        *definition.args.posonlyargs,
        *definition.args.args,
    ]
    positional_default_start = len(positional) - len(definition.args.defaults)
    optional_names = {
        argument.arg
        for index, argument in enumerate(positional)
        if index >= positional_default_start
    }
    optional_names.update(
        argument.arg
        for argument, default in zip(
            definition.args.kwonlyargs,
            definition.args.kw_defaults,
            strict=True,
        )
        if default is not None
    )
    declared_names = {
        argument.arg
        for argument in [
            *definition.args.posonlyargs,
            *definition.args.args,
            *definition.args.kwonlyargs,
        ]
    }
    required_names = declared_names - optional_names
    requested_names = {
        str(item["name"]) for item in contract["parameters"]
    }
    missing_parameters = sorted(requested_names - declared_names)
    for name in sorted(requested_names & positional_only):
        violations.append(
            {
                "callable": callable_name,
                "parameter": name,
                "reason": "named_parameter_is_positional_only",
            }
        )
    for name in sorted(requested_names & required_names):
        violations.append(
            {
                "callable": callable_name,
                "parameter": name,
                "reason": "parameter_is_not_optional",
            }
        )
    for name in sorted(required_names - requested_names):
        violations.append(
            {
                "callable": callable_name,
                "parameter": name,
                "reason": "unrequested_required_parameter",
            }
        )
    for name in missing_parameters:
        violations.append(
            {
                "callable": callable_name,
                "parameter": name,
                "reason": "missing_parameter",
            }
        )
    return {
        **contract,
        "ok": not violations,
        "reason_code": (
            ""
            if not violations
            else "optional_integer_callable_shape_mismatch"
        ),
        "missing_parameters": missing_parameters,
        "violations": violations,
    }


def fixed_literal_zero_arg_callable_names(task: str) -> list[str]:
    """Derive a narrow callable-shape contract from public task prose.

    A count helper that embeds a task-supplied filter literal has no reason to
    invent a required caller input when the request supplies none.  This
    recognizer is deliberately conservative: the callable, count result, and
    fixed-literal predicate must all occur in the same public sentence, and
    any explicit parameter language disables the inference.
    """

    planning_text = effective_planning_task_text(str(task or ""))
    names: list[str] = []
    clauses = re.split(r"(?<=[.!?])\s+|\n+", planning_text)
    for raw_clause in clauses:
        clause = raw_clause.strip()
        if not clause or len(clause) > 1_200:
            continue
        if (
            _PUBLIC_COUNT_RESULT_RE.search(clause) is None
            or _PUBLIC_FIXED_LITERAL_FILTER_RE.search(clause) is None
        ):
            continue
        parameter_neutral = _PUBLIC_ZERO_PARAMETER_RE.sub("", clause)
        if _PUBLIC_EXPLICIT_PARAMETER_RE.search(parameter_neutral):
            continue
        for pattern in _PUBLIC_CALLABLE_NAME_PATTERNS:
            for match in pattern.finditer(clause):
                prefix = clause[: match.start()]
                if (
                    _PUBLIC_CALLABLE_REQUEST_RE.search(prefix) is None
                    or _PUBLIC_NEGATED_CALLABLE_REQUEST_RE.search(prefix)
                    is not None
                ):
                    continue
                name = match.group("name")
                if name not in names:
                    names.append(name)
    return names


def _fixed_literal_callable_owner_name(task: str, callable_name: str) -> str | None:
    """Return an explicitly named class owner for a derived callable."""

    planning_text = effective_planning_task_text(str(task or ""))
    escaped_name = re.escape(callable_name)
    quoted_name = rf"[`'\"]{escaped_name}[`'\"]"
    callable_reference = (
        rf"(?:{quoted_name}\s+"
        r"(?:(?:service|helper|utility)\s+)?(?:function|callable)"
        r"|(?:function|callable)\s+(?:(?:named|called)\s+)?"
        rf"{quoted_name}"
        rf"|\b{escaped_name}\b\s+"
        r"(?:(?:service|helper|utility)\s+)?function)"
    )
    owner = (
        r"[`'\"]?(?P<owner>(?-i:[A-Z])[A-Za-z0-9_]*)[`'\"]?"
    )
    patterns = (
        re.compile(
            rf"{callable_reference}\s+"
            r"(?:as\s+(?:an?\s+)?method\s+)?"
            r"(?:to|on|in|inside|within)\s+"
            rf"(?:the\s+)?(?:class\s+)?{owner}",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:on|in|inside|within)\s+(?:the\s+)?(?:class\s+)?"
            rf"{owner}[^.!?\n]{{0,120}}{callable_reference}",
            re.IGNORECASE,
        ),
    )
    for pattern in patterns:
        match = pattern.search(planning_text)
        if match is not None:
            return match.group("owner")
    return None


def fixed_literal_callable_shape_check(
    task: str,
    python_source: str,
) -> dict[str, Any]:
    """Check already-materialized Python against the derived public contract."""

    names = fixed_literal_zero_arg_callable_names(task)
    if not names:
        return {
            "ok": True,
            "skipped": True,
            "reason_code": "",
            "required_zero_arg_callables": [],
            "missing_callables": [],
            "violations": [],
        }
    try:
        tree = ast.parse(str(python_source or ""))
    except (SyntaxError, ValueError):
        return {
            "ok": False,
            "skipped": False,
            "reason_code": "fixed_literal_callable_source_invalid",
            "required_zero_arg_callables": names,
            "missing_callables": [],
            "violations": [],
        }

    definitions: dict[
        str,
        list[
            tuple[
                ast.FunctionDef | ast.AsyncFunctionDef,
                int,
                str | None,
                bool,
            ]
        ],
    ] = {name: [] for name in names}

    def collect_definitions(
        body: list[ast.stmt],
        *,
        class_name: str | None,
    ) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name not in definitions:
                    continue
                is_static = any(
                    (
                        isinstance(decorator, ast.Name)
                        and decorator.id == "staticmethod"
                    )
                    or (
                        isinstance(decorator, ast.Attribute)
                        and decorator.attr == "staticmethod"
                    )
                    for decorator in node.decorator_list
                )
                positional = [*node.args.posonlyargs, *node.args.args]
                invalid_bound_receiver = (
                    class_name is not None and not is_static and not positional
                )
                definitions[node.name].append(
                    (
                        node,
                        1 if class_name is not None and not is_static else 0,
                        class_name,
                        invalid_bound_receiver,
                    )
                )
            elif isinstance(node, ast.ClassDef):
                collect_definitions(node.body, class_name=node.name)

    collect_definitions(tree.body, class_name=None)

    selected_definitions: dict[
        str,
        tuple[
            ast.FunctionDef | ast.AsyncFunctionDef,
            int,
            str | None,
            bool,
        ]
        | None,
    ] = {}
    for name in names:
        owner_name = _fixed_literal_callable_owner_name(task, name)
        candidates = [
            definition
            for definition in definitions[name]
            if definition[2] == owner_name
        ]
        selected_definitions[name] = candidates[-1] if candidates else None

    missing = [name for name in names if selected_definitions[name] is None]
    violations: list[dict[str, Any]] = []
    for name in names:
        selected = selected_definitions[name]
        if selected is None:
            continue
        (
            effective_definition,
            implicit_positional_count,
            _owner_name,
            invalid_bound_receiver,
        ) = selected
        positional = [
            *effective_definition.args.posonlyargs,
            *effective_definition.args.args,
        ]
        required_count = max(
            0,
            len(positional)
            - len(effective_definition.args.defaults)
            - implicit_positional_count,
        )
        required_keyword_only_count = sum(
            default is None
            for default in effective_definition.args.kw_defaults
        )
        required_total = required_count + required_keyword_only_count
        if required_total or invalid_bound_receiver:
            violation = {
                "callable": name,
                "required_positional_parameters": required_count,
                "required_keyword_only_parameters": (
                    required_keyword_only_count
                ),
                "required_parameters": required_total,
            }
            if invalid_bound_receiver:
                violation["invalid_bound_receiver"] = True
            violations.append(violation)
    return {
        "ok": not missing and not violations,
        "skipped": False,
        "reason_code": (
            ""
            if not missing and not violations
            else "fixed_literal_callable_shape_mismatch"
        ),
        "required_zero_arg_callables": names,
        "missing_callables": missing,
        "violations": violations,
    }


def _bounded_capability_intent_paths(
    plan: ArchitectPlan,
    exact_paths: list[str],
    *,
    trusted_intent_paths: set[str],
    artifact_snapshots: Mapping[str, Any] | None,
) -> set[str]:
    """Authorize only narrow task capabilities backed by pre-apply snapshots."""

    snapshots = _validated_capability_snapshots(artifact_snapshots, exact_paths)
    if not snapshots:
        return set()
    task = effective_planning_task_text(plan.source_task)
    extras = [path for path in exact_paths if path not in trusted_intent_paths]
    authorized: set[str] = set()

    test_extras = [path for path in extras if _review_test_artifact_path(path)]
    if (
        len(test_extras) == 1
        and task_requests_test_artifact(task)
        and _test_artifact_is_bound_to_target(
            test_extras[0],
            snapshots[test_extras[0]],
            plan.coder_packet.target_file.path,
        )
    ):
        authorized.add(test_extras[0])

    remaining = [path for path in extras if path not in authorized]
    if (
        len(remaining) == 1
        and task_requests_shared_helper_artifact(task)
        and _new_shared_helper_is_structurally_bound(
            remaining[0],
            exact_paths=exact_paths,
            trusted_intent_paths=trusted_intent_paths,
            snapshots=snapshots,
        )
    ):
        authorized.add(remaining[0])
    return authorized


def task_requests_test_artifact(task: str) -> bool:
    """Recognize an affirmative request to create or update test code."""

    for clause in re.split(r"[.!?\n]+", str(task or "")):
        for test_match in re.finditer(r"\btests?\b", clause, re.IGNORECASE):
            actions = list(
                re.finditer(
                    r"\b(?P<verb>add|create|include|modify|update|write)\b",
                    clause[: test_match.start()],
                    re.IGNORECASE,
                )
            )
            if not actions:
                continue
            action = actions[-1]
            qualifier = clause[action.end() : test_match.start()]
            if len(qualifier) > 120:
                continue
            prefix = clause[: action.start()]
            suffix = clause[test_match.end() :]
            if _authority_action_is_nonaffirmative(prefix, suffix):
                continue
            if re.search(
                r"\b(?:0|except|instead\s+of|neither|no|nor|not|"
                r"other\s+than|rather\s+than|without|zero)\b",
                qualifier,
                re.IGNORECASE,
            ):
                continue
            if action.group("verb").lower() == "write" and re.search(
                r"\babout\b", qualifier, re.IGNORECASE
            ):
                continue
            if action.group("verb").lower() == "include" and re.search(
                r"\bexisting\b", qualifier, re.IGNORECASE
            ):
                continue
            if re.match(
                r"\s+(?:in|into|to)\s+(?:the\s+)?"
                r"(?:documentation|docs?|reference|report)\b",
                suffix,
                re.IGNORECASE,
            ):
                continue
            return True
    return False


def task_requests_shared_helper_artifact(task: str) -> bool:
    """Recognize an affirmative duplicate-logic refactor into one helper."""

    normalized = str(task or "")
    if not re.search(r"\b(?:duplicat\w*|repeat\w*)\b", normalized, re.IGNORECASE):
        return False
    if re.search(
        r"\b(?:do|does|did|should|must|shall|can|could|will|would|may)"
        r"\s+not\b[^.!?\n]{0,512}\brefactor(?:ing)?\b"
        r"|\b(?:cannot|can't|couldn't|didn't|doesn't|don't|mustn't|"
        r"needn't|shan't|shouldn't|won't|wouldn't|never|no)\b"
        r"[^.!?\n]{0,512}\brefactor(?:ing)?\b"
        r"|\brefactor(?:ing)?\b[^.!?\n]{0,160}"
        r"\b(?:cannot|can't|couldn't|didn't|doesn't|don't|isn't|mustn't|"
        r"needn't|never|not|shan't|shouldn't|wasn't|weren't|won't|"
        r"wouldn't)\b"
        r"|\brefactor(?:ing)?\b[^.!?\n]{0,160}\bno\s+longer\b"
        r"|\brefactor(?:ing)?\b[^.!?\n]{0,160}"
        r"\b(?:forbidden|not\s+(?:allowed|permitted|required)|"
        r"out\s+of\s+scope|prohibited)\b",
        normalized,
        re.IGNORECASE,
    ):
        return False
    clauses = re.split(r"[.!?\n]+", normalized)
    helper_any_re = re.compile(
        r"(?:\b(?:shared|common)\b[^\n]{0,48}\bhelpers?\b|"
        r"\bhelpers?\b[^\n]{0,48}\b"
        r"(?:shared\s+by|used\s+by|for\s+both)\b)",
        re.IGNORECASE,
    )
    helper_re = re.compile(
        r"(?:\b(?:shared|common)\b[^\n]{0,48}\bhelper\b|"
        r"\bhelper\b[^\n]{0,48}\b"
        r"(?:shared\s+by|used\s+by|for\s+both)\b)",
        re.IGNORECASE,
    )
    affirmative_helper_segments = 0
    for clause in clauses:
        for segment in re.split(
            r"\b(?:but|however|yet)\b",
            clause,
            flags=re.IGNORECASE,
        ):
            helper_mentions = list(helper_any_re.finditer(segment))
            if not helper_mentions:
                continue
            if len(helper_mentions) != 1:
                return False
            helper_any = helper_mentions[0]
            helper_match = helper_re.search(segment)
            actions = (
                list(
                    re.finditer(
                        r"\b(?:extract|refactor)\b",
                        segment[: helper_match.start()],
                        re.IGNORECASE,
                    )
                )
                if helper_match is not None
                else []
            )
            if (
                helper_match is None
                or not actions
                or helper_match.start() - actions[-1].end() > 160
            ):
                return False
            affirmative_helper_segments += 1
            if re.search(
                r"\b(?:do|does|did|should|must|shall|can|could|will|"
                r"would|may)\s+not\b"
                r"|\b(?:cannot|can't|couldn't|didn't|doesn't|don't|isn't|"
                r"mustn't|needn't|shan't|shouldn't|wasn't|weren't|won't|"
                r"wouldn't|never)\b"
                r"|\b(?:avoid(?:ing)?|refrain\s+from|refuse\s+to|without)\b"
                r"|\b(?:anything|everything)\s+(?:but|except|other\s+than)\b"
                r"|\b(?:except|instead\s+of|neither|no|not|other\s+than|"
                r"rather\s+than)\b"
                r"|\b(?:consider|discuss|document|evaluate|explain|describe)\b"
                r"[^.!?\n]{0,512}\b(?:whether|how)\b"
                r"|\b(?:maybe|perhaps)\b",
                segment[: helper_any.start()],
                re.IGNORECASE,
            ) or re.search(
                r"\b(?:forbidden|not\s+(?:allowed|permitted|required)|"
                r"out\s+of\s+scope|prohibited)\b"
                r"|\b(?:should|must|shall|can|could|may|will|would)\s+not\b"
                r"|\b(?:cannot|can't|mustn't|never|not|shouldn't)\b",
                segment[helper_any.end() :],
                re.IGNORECASE,
            ):
                return False
    if affirmative_helper_segments != 1:
        return False
    affirmative_request_seen = False
    for clause in clauses:
        helper_match = helper_re.search(clause)
        if helper_match is None:
            continue
        actions = list(
            re.finditer(
                r"\b(?:extract|refactor)\b",
                clause[: helper_match.start()],
                re.IGNORECASE,
            )
        )
        if not actions:
            continue
        refactor_match = actions[-1]
        if helper_match.start() - refactor_match.end() > 160:
            continue
        if _authority_action_is_nonaffirmative(
            clause[: refactor_match.start()],
            clause[helper_match.end() :],
        ):
            return False
        action_span = clause[refactor_match.start() : helper_match.end()]
        if re.search(
            r"\b(?:is|are|was|were)\s+(?:strictly\s+)?"
            r"(?:forbidden|prohibited)\b",
            action_span,
            re.IGNORECASE,
        ) or re.search(
            r"\b(?:not|never)\b[^,;:]{0,64}"
            r"\b(?:into|to|using|with)\b[^,;:]{0,32}"
            r"\b(?:shared|common)\b[^,;:]{0,24}\bhelper\b",
            action_span,
            re.IGNORECASE,
        ) or re.search(
            r"\bwithout\s+(?:a\s+|the\s+)?"
            r"(?:(?:shared|common)\s+)?helper\b",
            action_span,
            re.IGNORECASE,
        ) or re.search(
            r"\b(?:instead\s+of|neither|nor|other\s+than|rather\s+than)\b",
            action_span,
            re.IGNORECASE,
        ):
            return False
        affirmative_request_seen = True
    return affirmative_request_seen


def _authority_action_is_nonaffirmative(prefix: str, suffix: str) -> bool:
    """Reject negated, prohibited, or merely discussed authority actions."""

    raw_tail = prefix[-256:].replace("’", "'")
    if re.search(
        r"\b(?:anything|everything)\s+but\s*$",
        raw_tail,
        re.IGNORECASE,
    ):
        return True
    prefix_tail = re.split(
        r"\b(?:but|however|yet)\b",
        raw_tail,
        flags=re.IGNORECASE,
    )[-1]
    if re.search(
        r"(?:^|\b)(?:"
        r"(?:do|does|did|should|must|shall|can|could|will|would|may)\s+not|"
        r"cannot|can't|couldn't|didn't|doesn't|don't|isn't|mustn't|"
        r"needn't|shan't|shouldn't|wasn't|weren't|won't|wouldn't|never|"
        r"(?:isn't|aren't|wasn't|weren't)\s+"
        r"(?:allowed|permitted|required)\s+to|"
        r"not\s+(?:allowed|permitted|required)\s+to|"
        r"under\s+no\s+circumstances|"
        r"(?:there\s+is\s+)?no\s+(?:need|requirement)\s+to|"
        r"(?:there\s+)?(?:must|should)\s+be\s+no|"
        r"(?:is|are|was|were)\s+(?:strictly\s+)?"
        r"(?:forbidden|prohibited)\s+to|"
        r"avoid(?:ing)?(?:\s+(?:a|an|the))?|"
        r"refrain\s+from|refuse\s+to|"
        r"(?:anything|everything)\s+(?:except|other\s+than)|"
        r"except|instead\s+of|other\s+than|rather\s+than|without"
        r")\b[^,;:.!?]{0,96}$",
        prefix_tail,
        re.IGNORECASE,
    ):
        return True
    if re.search(
        r"\b(?:neither|no|not(?:\s+to)?)\s+$",
        prefix_tail,
        re.IGNORECASE,
    ):
        return True
    if re.search(
        r"\b(?:consider|discuss|document|evaluate|explain|describe)\b"
        r"[^,;:.!?]{0,96}"
        r"(?:whether|how)?(?:\s+to)?\s*$|"
        r"\b(?:maybe|perhaps)\s*$",
        prefix_tail,
        re.IGNORECASE,
    ):
        return True
    if re.search(
        r"\b(?:can|could|may|might|should|would)\s+(?:i|we)\s*$",
        prefix_tail,
        re.IGNORECASE,
    ):
        return True
    return bool(
        re.match(
            r"\s+(?:(?:(?:is|are|was|were)|"
            r"(?:isn't|aren't|wasn't|weren't))\s+(?:"
            r"(?:strictly\s+)?(?:forbidden|prohibited)|"
            r"(?:not\s+)?(?:allowed|permitted|required)|"
            r"out\s+of\s+scope"
            r")|(?:cannot|can't|couldn't|shouldn't|mustn't)\s+"
            r"be\s+(?:done|performed|required))\b",
            suffix,
            re.IGNORECASE,
        )
    )


def _validated_capability_snapshots(
    snapshots: Mapping[str, Any] | None,
    exact_paths: list[str],
) -> dict[str, dict[str, Any]]:
    if not isinstance(snapshots, Mapping) or set(snapshots) != set(exact_paths):
        return {}
    validated: dict[str, dict[str, Any]] = {}
    total_chars = 0
    for path in exact_paths:
        record = snapshots.get(path)
        if not isinstance(record, Mapping):
            return {}
        content = record.get("content")
        exists = record.get("exists")
        if not (
            record.get("schema_version") == "coding.review-artifact-snapshot/v1"
            and record.get("path") == path
            and isinstance(exists, bool)
            and isinstance(content, str)
            and (exists or content == "")
            and record.get("content_sha256")
            == hashlib.sha256(content.encode("utf-8")).hexdigest()
        ):
            return {}
        total_chars += len(content)
        if total_chars > 1_000_000:
            return {}
        validated[path] = dict(record)
    return validated


def _review_test_artifact_path(path: str) -> bool:
    normalized = path.lower()
    name = normalized.rsplit("/", 1)[-1]
    return bool(
        normalized.startswith(("test/", "tests/"))
        or "/tests/" in f"/{normalized}/"
        or "/__tests__/" in f"/{normalized}/"
        or name.startswith("test_")
        or ".test." in name
        or ".spec." in name
    )


def _test_artifact_is_bound_to_target(
    test_path: str,
    snapshot: Mapping[str, Any],
    target_path: str,
) -> bool:
    target_name = target_path.rsplit("/", 1)[-1]
    target_stem = target_name.rsplit(".", 1)[0]
    target_module = target_path.rsplit(".", 1)[0].replace("/", ".")
    test_name = test_path.rsplit("/", 1)[-1].lower()
    conventional_names = {
        f"test_{target_stem}.py",
        f"{target_stem}_test.py",
        f"{target_stem}.test.ts",
        f"{target_stem}.test.tsx",
        f"{target_stem}.test.js",
        f"{target_stem}.test.jsx",
        f"{target_stem}.spec.ts",
        f"{target_stem}.spec.tsx",
        f"{target_stem}.spec.js",
        f"{target_stem}.spec.jsx",
    }
    if snapshot.get("exists") is False:
        return test_name in conventional_names
    content = str(snapshot.get("content") or "")
    parent_module, _, module_name = target_module.rpartition(".")
    python_binding = False
    if test_path.lower().endswith(".py"):
        try:
            tree = ast.parse(content)
        except (SyntaxError, ValueError):
            tree = None
        if tree is not None:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) and any(
                    alias.name == target_module for alias in node.names
                ):
                    python_binding = True
                    break
                if isinstance(node, ast.ImportFrom):
                    if node.module == target_module or (
                        node.module == parent_module
                        and any(alias.name == module_name for alias in node.names)
                    ):
                        python_binding = True
                        break
    script_binding = any(
        _script_specifier_targets_path(
            specifier,
            test_path=test_path,
            target_path=target_path,
        )
        for specifier in _active_script_module_specifiers(content)
    )
    return python_binding or script_binding


def _active_script_module_specifiers(content: str) -> list[str]:
    """Extract module strings from active import/require syntax only."""

    chars = list(content)
    specifiers: list[str] = []
    state = "code"
    regex_class = False
    index = 0
    while index < len(chars):
        char = chars[index]
        next_char = chars[index + 1] if index + 1 < len(chars) else ""
        if state == "code":
            if char in {'"', "'"}:
                quote = char
                start = index
                end = index + 1
                while end < len(chars):
                    if chars[end] == "\\":
                        end += 2
                        continue
                    if chars[end] == quote:
                        break
                    if chars[end] in "\r\n":
                        break
                    end += 1
                prefix = "".join(chars[max(0, start - 256) : start])
                if end < len(chars) and chars[end] == quote and re.search(
                    r"(?:\b(?:import|export)\b[^\n;]{0,200}\bfrom|"
                    r"\brequire\s*\(|\bimport\s*\(|\bimport)\s*$",
                    prefix,
                    re.IGNORECASE,
                ):
                    specifiers.append(content[start + 1 : end])
                stop = min(end + 1, len(chars))
                for masked_index in range(start, stop):
                    if chars[masked_index] not in "\r\n":
                        chars[masked_index] = " "
                index = stop
                continue
            elif char == "`":
                chars[index] = " "
                state = "template"
            elif char == "/" and next_char == "/":
                chars[index] = chars[index + 1] = " "
                state = "line_comment"
                index += 1
            elif char == "/" and next_char == "*":
                chars[index] = chars[index + 1] = " "
                state = "block_comment"
                index += 1
            elif char == "/":
                prior = "".join(chars[max(0, index - 80) : index]).rstrip()
                if _script_slash_begins_regex(prior):
                    chars[index] = " "
                    regex_class = False
                    state = "regex"
        elif state == "regex":
            if char != "\n":
                chars[index] = " "
            if char == "\\":
                if index + 1 < len(chars) and chars[index + 1] != "\n":
                    chars[index + 1] = " "
                index += 1
            elif char == "[":
                regex_class = True
            elif char == "]":
                regex_class = False
            elif char == "/" and not regex_class:
                state = "code"
        elif state == "template":
            if char != "\n":
                chars[index] = " "
            if char == "\\":
                if index + 1 < len(chars) and chars[index + 1] != "\n":
                    chars[index + 1] = " "
                index += 1
            elif char == "`":
                state = "code"
        elif state == "line_comment":
            if char == "\n":
                state = "code"
            else:
                chars[index] = " "
        elif state == "block_comment":
            if char == "*" and next_char == "/":
                chars[index] = chars[index + 1] = " "
                state = "code"
                index += 1
            elif char != "\n":
                chars[index] = " "
        index += 1
    return specifiers


def _script_slash_begins_regex(prior: str) -> bool:
    line_tail = prior.rsplit("\n", 1)[-1]
    if not line_tail.strip():
        return True
    return bool(
        re.search(
            r"(?:^|[=(:,!\[{;?&|+*%^~<>}-]|=>|"
            r"\b(?:await|case|default|delete|do|else|extends|in|instanceof|"
            r"new|of|return|throw|typeof|void|yield))\s*$",
            line_tail,
        )
        or re.search(
            r"\b(?:catch|for|if|switch|while|with)\s*\([^;\n]*\)\s*$",
            line_tail,
        )
    )


def _script_specifier_targets_path(
    specifier: str,
    *,
    test_path: str,
    target_path: str,
) -> bool:
    script_suffixes = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}
    target_suffix = "." + target_path.rsplit(".", 1)[-1].lower()
    if target_suffix not in script_suffixes:
        return False
    normalized_specifier = str(specifier or "").strip().replace("\\", "/")
    if not normalized_specifier or any(
        marker in normalized_specifier for marker in ("\x00", "?", "#")
    ):
        return False
    if normalized_specifier.startswith("."):
        resolved = posixpath.normpath(
            posixpath.join(posixpath.dirname(test_path), normalized_specifier)
        )
    elif normalized_specifier.startswith("/"):
        resolved = posixpath.normpath(normalized_specifier.lstrip("/"))
    elif "/" in normalized_specifier:
        resolved = posixpath.normpath(normalized_specifier)
    else:
        return False
    if resolved == ".." or resolved.startswith("../"):
        return False

    def without_script_suffix(path: str) -> str:
        lowered = path.lower()
        for suffix in script_suffixes:
            if lowered.endswith(suffix):
                return path[: -len(suffix)]
        return path

    target_module_path = without_script_suffix(target_path)
    resolved_module_path = without_script_suffix(resolved)
    return bool(
        resolved_module_path == target_module_path
        or resolved_module_path.rstrip("/") + "/index" == target_module_path
    )


def _new_shared_helper_is_structurally_bound(
    helper_path: str,
    *,
    exact_paths: list[str],
    trusted_intent_paths: set[str],
    snapshots: Mapping[str, Mapping[str, Any]],
) -> bool:
    helper_record = snapshots.get(helper_path)
    if not isinstance(helper_record, Mapping) or helper_record.get("exists") is not False:
        return False
    if _review_test_artifact_path(helper_path):
        return False
    helper_parent, _, helper_name = helper_path.rpartition("/")
    helper_suffix = "." + helper_name.rsplit(".", 1)[-1] if "." in helper_name else ""
    if not helper_suffix or helper_name.startswith("."):
        return False
    trusted_sources = [
        path
        for path in exact_paths
        if path in trusted_intent_paths
        and path != helper_path
        and not _review_test_artifact_path(path)
        and snapshots.get(path, {}).get("exists") is True
        and path.rpartition("/")[0] == helper_parent
        and path.endswith(helper_suffix)
    ]
    return len(trusted_sources) >= 2


_ROOT_REVIEW_ARTIFACT_NAMES = frozenset(
    {
        "dockerfile",
        "jenkinsfile",
        "license",
        "makefile",
        "notice",
        "procfile",
    }
)
_UNQUOTED_REVIEW_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./\\-])"
    r"(?P<path>"
    r"(?:[A-Za-z0-9_.@()+-]+[\\/])+"
    r"(?:\.[A-Za-z0-9_@()+-]+|"
    r"[A-Za-z0-9_@()+-]+(?:\.[A-Za-z0-9_@()+-]+)*)"
    r"|(?:[A-Za-z0-9_.@()+-]+[\\/])*"
    r"(?:\.[A-Za-z0-9_@()+-]+|[A-Za-z0-9_@()+-]+\.[A-Za-z0-9_-]+)"
    r"|Dockerfile|Jenkinsfile|LICENSE|Makefile|NOTICE|Procfile"
    r")"
    r"(?![A-Za-z0-9_/\\-]|\.[A-Za-z0-9_-])"
)
_REVIEW_MUTATION_VERB_RE = re.compile(
    r"\b(?:"
    r"add(?:ed|ing|s)?|append(?:ed|ing|s)?|"
    r"chang(?:e|ed|es|ing)|creat(?:e|ed|es|ing)|"
    r"delet(?:e|ed|es|ing)|edit(?:ed|ing|s)?|"
    r"ensur(?:e|ed|es|ing)|implement(?:ed|ing|s)?|"
    r"insert(?:ed|ing|s)?|modif(?:y|ied|ies|ying)|"
    r"mak(?:e|es|ing)|mov(?:e|ed|es|ing)|remov(?:e|ed|es|ing)|"
    r"renam(?:e|ed|es|ing)|replac(?:e|ed|es|ing)|"
    r"rewrit(?:e|es|ing|ten)|set(?:s|ting)?|updat(?:e|ed|es|ing)|"
    r"writ(?:e|es|ing|ten)"
    r")\b",
    flags=re.IGNORECASE,
)
_REVIEW_NON_MUTATION_VERB_RE = re.compile(
    r"\b(?:affect(?:ed|ing|s)?|exclud(?:e|ed|es|ing)|"
    r"impact(?:ed|ing|s)?|keep|kept|leav(?:e|es|ing|t)|"
    r"omit(?:ted|ting|s)?|"
    r"describ(?:e|ed|es|ing)|discuss(?:ed|es|ing)?|"
    r"document(?:ed|ing|s)?|explain(?:ed|ing|s)?|"
    r"mention(?:ed|ing|s)?|preserv(?:e|ed|es|ing)|"
    r"referenc(?:e|ed|es|ing)|read(?:ing)?|inspect(?:ed|ing|s)?|"
    r"touch(?:ed|ing|es)?|us(?:e|ed|es|ing))\b",
    flags=re.IGNORECASE,
)


def review_intent_paths_from_plan(plan: ArchitectPlan) -> list[str]:
    """Return ordered exact artifacts authorized by trusted task intent."""

    intended = [plan.coder_packet.target_file.path]
    trusted_texts = [
        effective_planning_task_text(plan.source_task),
        *(criterion.description for criterion in plan.coder_packet.acceptance_criteria),
    ]
    for text in trusted_texts:
        for raw_path, start, end in _review_path_occurrences(text):
            path = _normalize_repo_path(raw_path)
            if (
                not _looks_like_exact_review_artifact(path)
                or path_escapes_workspace(path)
                or has_percent_encoded_path_syntax(path)
                or not _path_occurrence_requests_mutation(text, start, end)
            ):
                continue
            if path not in intended:
                intended.append(path)
    return intended


def _review_path_occurrences(text: str) -> list[tuple[str, int, int]]:
    occurrences: list[tuple[str, int, int]] = []
    quoted_spans: list[tuple[int, int]] = []
    for match in re.finditer(
        r"(?P<quote>[\"'`])(?P<value>[^\"'`\r\n]+)(?P=quote)",
        text or "",
    ):
        quoted_spans.append(match.span())
        value = match.group("value")
        if _looks_like_exact_review_artifact(_normalize_repo_path(value)):
            occurrences.append((value, match.start(), match.end()))
    for match in _UNQUOTED_REVIEW_PATH_RE.finditer(text or ""):
        if any(start <= match.start() < end for start, end in quoted_spans):
            continue
        occurrences.append((match.group("path"), match.start(), match.end()))
    return occurrences


def _looks_like_exact_review_artifact(path: str) -> bool:
    if (
        not path
        or path.endswith("/")
        or any(char.isspace() for char in path)
        or any(char in path for char in "*?[]{}")
    ):
        return False
    name = path.rsplit("/", 1)[-1]
    return bool(
        "/" in path
        or name.startswith(".")
        or "." in name
        or name.lower() in _ROOT_REVIEW_ARTIFACT_NAMES
    )


def _path_occurrence_requests_mutation(text: str, start: int, end: int) -> bool:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end < 0:
        line_end = len(text)
    prefix = text[line_start:start]
    suffix = text[end:line_end]

    # Dotted framework/product names can look like root-level files.  In
    # descriptions such as "modify page.tsx as a Next.js app route", the
    # name after "as a" describes the target's type and is never a second
    # mutation artifact.
    if re.search(r"\bas\s+(?:an?\s+)?$", prefix, flags=re.IGNORECASE):
        return False
    if _path_occurrence_is_output_literal(prefix, suffix):
        return False
    if re.search(
        r"\b(?:not|no\s+changes?\s+to)\s+(?:the\s+)?"
        r"(?:artifact|file|target)?(?:\s+path)?\s*$",
        prefix,
        flags=re.IGNORECASE,
    ):
        return False
    if re.match(
        r"\s+(?:remains?|stays?|is|must\s+be|should\s+be|shall\s+be)"
        r"\s+(?:preserved|unchanged|unmodified|untouched)\b",
        suffix,
        flags=re.IGNORECASE,
    ):
        return False
    if re.match(
        r"\s+(?:(?:must|should|shall)\s+(?:remain|stay)\s+"
        r"(?:preserved|unchanged|unmodified|untouched)|"
        r"(?:must|should|shall)\s+not\s+be\s+"
        r"(?:altered|changed|modified|removed|updated))\b",
        suffix,
        flags=re.IGNORECASE,
    ):
        return False

    if re.match(
        r"\s+(?:must|should|shall|needs?\s+to)\s+(?:not\s+)?"
        r"(?:contain|include|have|display|emit|render|show)\b",
        suffix,
        flags=re.IGNORECASE,
    ):
        return True
    suffix_action = re.match(r"\s*(?:[:,\-]|\u2014)\s*", suffix)
    if suffix_action is not None:
        suffix_match = _REVIEW_MUTATION_VERB_RE.match(
            suffix[suffix_action.end() :].lstrip()
        )
        if suffix_match is not None:
            return True

    clause_prefix = re.split(r"(?:[!?]\s+|;\s*|\.\s+(?=[A-Z]))", prefix)[-1]
    mutations = list(_REVIEW_MUTATION_VERB_RE.finditer(clause_prefix))
    if not mutations:
        return False
    last_mutation = mutations[-1]
    non_mutations = list(_REVIEW_NON_MUTATION_VERB_RE.finditer(clause_prefix))
    if non_mutations and non_mutations[-1].start() > last_mutation.start():
        return False
    before_mutation = clause_prefix[: last_mutation.start()]
    after_mutation = clause_prefix[last_mutation.end() :]
    if re.search(
        r"\b(?:apart\s+from|except|instead\s+of|neither|nor|"
        r"other\s+than|rather\s+than)\b",
        after_mutation,
        re.IGNORECASE,
    ):
        return False
    return not _authority_action_is_nonaffirmative(before_mutation, suffix)


def _path_occurrence_is_output_literal(prefix: str, suffix: str) -> bool:
    if re.search(
        r"\b(?:change|replace|set|update)\b[^\n.!?]{0,80}"
        r"\b(?:displayed|emitted|printed|rendered|shown)\b"
        r"[^\n.!?]{0,24}\b(?:filename|file\s+name|label|path|text|value)\b"
        r"[^\n.!?]{0,16}\b(?:as|to)\s*$",
        prefix,
        re.IGNORECASE,
    ):
        return True
    if re.search(
        r"\b(?:artifact|file|target)(?:\s+path)?\s*$",
        prefix,
        flags=re.IGNORECASE,
    ):
        return False
    if re.search(
        r"\b(?:copy|display|filename|heading|label|mention|message|output|path|response|"
        r"status|string|text|title|value|word)\s*$",
        prefix,
        flags=re.IGNORECASE,
    ):
        return True
    return bool(
        re.search(
            r"\b(?:add|append|display|emit|include|insert|print|render|show|write)"
            r"\b[^\n.!?]{0,80}$",
            prefix,
            flags=re.IGNORECASE,
        )
        and re.match(
            r"\s+(?:to|in|inside|as)\s+(?:the\s+)?(?:rendered\s+)?"
            r"(?:copy|display|label|message|output|text)\b",
            suffix,
            flags=re.IGNORECASE,
        )
    )


def _path_in_authorized_scope(path: str, scopes: list[str]) -> bool:
    return any(
        path == scope.rstrip("/")
        or path.startswith(scope.rstrip("/") + "/")
        for scope in scopes
    )


def _path_matches_forbidden(path: str, forbidden: list[str]) -> bool:
    for raw in forbidden:
        pattern = str(raw or "").replace("\\", "/").strip()
        if not pattern:
            continue
        if any(char in pattern for char in "*?["):
            if fnmatchcase(path, pattern):
                return True
            continue
        if path == pattern.rstrip("/") or (
            pattern.endswith("/") and path.startswith(pattern)
        ):
            return True
    return False


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


def validate_task_spec_for_plan(
    task_spec: CoderTaskSpec,
    plan: ArchitectPlan,
) -> list[str]:
    """Validate the complete deterministic TaskSpec against its persisted plan."""

    packet = plan.coder_packet
    base = task_spec_from_packet(
        packet,
        verification_plan=plan.verification_plan,
    )
    expected_allowed = canonical_task_spec_paths_from_plan(plan)
    expected_task_type: TaskSpecType = (
        "create_file_bundle"
        if len(expected_allowed) > 1
        else base.task_type
    )
    errors: list[str] = []
    if task_spec.schema_version != PLAN_SCHEMA_VERSION:
        errors.append("schema_version")
    if not task_spec.target or task_spec.target != packet.target_file.path:
        errors.append("target")
    if (
        not task_spec.allowed_files
        or task_spec.allowed_files[0] != task_spec.target
    ):
        errors.append("target_first")
    if task_spec.target not in task_spec.allowed_files:
        errors.append("target_in_allowed_files")
    if task_spec.allowed_files != _dedupe_preserve_order(task_spec.allowed_files):
        errors.append("allowed_files_deduplicated")
    if any(
        not path
        or path != _normalize_repo_path(path)
        or path_escapes_workspace(path)
        or has_percent_encoded_path_syntax(path)
        for path in task_spec.allowed_files
    ):
        errors.append("allowed_files_safe")
    if task_spec.allowed_files != expected_allowed:
        errors.append("allowed_files")
    if any(
        _path_matches_forbidden(path, base.forbidden_files)
        for path in task_spec.allowed_files
    ):
        errors.append("allowed_files_forbidden")
    if task_spec.task_type != expected_task_type:
        errors.append("task_type")
    for field_name in (
        "forbidden_files",
        "literal_requirements",
        "verification",
        "risk_tier",
        "source",
    ):
        if getattr(task_spec, field_name) != getattr(base, field_name):
            errors.append(field_name)
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
