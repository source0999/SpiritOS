from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from difflib import SequenceMatcher
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from source_proxy.decision.proposal_task import effective_planning_task_text
from source_proxy.planning.plan import ArchitectPlan, ContextSlice
from source_proxy.routing.litellm_router import available_model_aliases, get_router
from source_proxy.approval.external_gate import central_gate_check
from source_proxy.safety.paths import (
    has_percent_encoded_path_syntax,
    normalize_repo_path_candidate,
    path_escapes_workspace,
)


@dataclass(frozen=True)
class ReviewFinding:
    id: str
    details: str
    path: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewEvidence:
    requirement_id: str
    requirement_kind: str
    intended_paths: list[str]
    inspected_path: str
    baseline_sha256: str
    applied_sha256: str
    diff_hunk_sha256: str
    diff_hunk_line_count: int
    task_id: str
    attempt_id: str
    extraction_method: str
    baseline_match_count: int
    applied_match_count: int
    introduced: bool | None
    satisfied: bool | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewReport:
    passed: bool
    findings: list[ReviewFinding]
    evidence: list[ReviewEvidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "findings": [finding.to_dict() for finding in self.findings],
            "evidence": [item.to_dict() for item in self.evidence],
        }


class ReviewerLLMError(ValueError):
    pass


def validate_review_artifact_snapshots(
    snapshots: Mapping[str, Any] | None,
    *,
    expected_paths: list[str],
) -> dict[str, str]:
    """Validate bounded server snapshots used to materialize secondary files."""

    if snapshots is None:
        return {}
    normalized_expected = list(dict.fromkeys(expected_paths))
    if set(snapshots) != set(normalized_expected) or len(snapshots) > 8:
        raise ValueError("review_artifact_snapshot_path_set_mismatch")
    baselines: dict[str, str] = {}
    total_chars = 0
    for path in normalized_expected:
        record = snapshots.get(path)
        if not isinstance(record, Mapping):
            raise ValueError("review_artifact_snapshot_record_invalid")
        content = record.get("content")
        exists = record.get("exists")
        if not (
            record.get("schema_version")
            == "coding.review-artifact-snapshot/v1"
            and record.get("path") == path
            and isinstance(exists, bool)
            and isinstance(content, str)
            and (exists or content == "")
            and record.get("content_sha256") == _sha256_text(content)
        ):
            raise ValueError("review_artifact_snapshot_integrity_invalid")
        total_chars += len(content)
        if total_chars > 1_000_000:
            raise ValueError("review_artifact_snapshot_budget_exceeded")
        baselines[path] = content
    return baselines


def review_diff_deterministically(
    plan: ArchitectPlan,
    diff: str,
    *,
    task_spec: Mapping[str, Any] | None = None,
    task_id: str | None = None,
    attempt_id: str | None = None,
    artifact_snapshots: Mapping[str, Any] | None = None,
) -> ReviewReport:
    target_path = plan.coder_packet.target_file.path
    changed_paths = _changed_paths(diff)
    try:
        snapshot_baselines = validate_review_artifact_snapshots(
            artifact_snapshots,
            expected_paths=changed_paths,
        )
    except ValueError as error:
        return ReviewReport(
            passed=False,
            findings=[
                ReviewFinding(
                    "review_artifact_snapshots_invalid",
                    str(error),
                    target_path,
                )
            ],
            evidence=[],
        )
    target_baseline = snapshot_baselines.get(target_path)
    new_content = _materialize_target_content(
        plan,
        diff,
        baseline_content=target_baseline,
    )
    materialized = {
        path: (
            new_content
            if path == target_path
            else _materialize_path_content(
                plan,
                diff,
                path,
                baseline_content=snapshot_baselines.get(path),
            )
        )
        for path in changed_paths
    }
    materialized.setdefault(target_path, new_content)
    base_content = (
        target_baseline
        if target_baseline is not None
        else _target_slice(plan.coder_packet.context_slices, target_path)
    )
    findings: list[ReviewFinding] = []
    evidence: list[ReviewEvidence] = []
    unbound_existing_paths = [
        path
        for path in changed_paths
        if path not in snapshot_baselines
        and _context_slice_for_path(plan.coder_packet.context_slices, path) is None
        and not _patch_creates_complete_file(_patch_for_path(diff, path), path)
    ]
    constraints = plan.coder_packet.constraints
    added, removed = _changed_line_counts(diff)
    bound_task_id = str(task_id or plan.task_id)
    bound_attempt_id = str(
        attempt_id
        or (
            f"review-input:{plan.plan_id}:"
            f"{hashlib.sha256(diff.encode('utf-8')).hexdigest()[:16]}"
        )
    )
    if bound_task_id != plan.task_id:
        return ReviewReport(
            passed=False,
            findings=[
                ReviewFinding(
                    "review_task_binding_mismatch",
                    f"{bound_task_id}!={plan.task_id}",
                    target_path,
                )
            ],
            evidence=[],
        )
    exact_allowed_paths = _exact_allowed_review_paths(task_spec, target_path)
    for duplicate_path in _duplicate_diff_section_paths(diff):
        findings.append(
            ReviewFinding(
                "duplicate_diff_path_sections",
                "A changed artifact must have exactly one diff section.",
                duplicate_path,
            )
        )
    canonical_task = effective_planning_task_text(plan.source_task)

    for index, required in enumerate(constraints.must_contain):
        requirement_id = f"constraint.must_contain.{index}"
        change_mode = _requirement_change_mode(canonical_task, required)
        requirement_evidence, satisfied = _exact_requirement_evidence(
            plan=plan,
            diff=diff,
            materialized=materialized,
            requirement_id=requirement_id,
            requirement_kind="must_contain",
            needles=[required],
            intended_paths=[target_path],
            task_id=bound_task_id,
            attempt_id=bound_attempt_id,
            extraction_method="architect_constraint_exact_literal",
            change_mode=change_mode,
            artifact_baselines=snapshot_baselines,
        )
        evidence.extend(requirement_evidence)
        if not satisfied:
            misplaced = _misplaced_requirement_evidence(requirement_evidence)
            finding_id = (
                f"must_contain_misplaced_{misplaced[0]}"
                if misplaced is not None
                else (
                    "must_contain_not_introduced"
                    if change_mode is not None
                    and any(item.applied_match_count for item in requirement_evidence)
                    else "missing_must_contain"
                )
            )
            findings.append(
                ReviewFinding(
                    finding_id,
                    required,
                    misplaced[1] if misplaced is not None else target_path,
                )
            )

    for index, forbidden in enumerate(constraints.must_not_contain):
        requirement_id = f"constraint.must_not_contain.{index}"
        # Architect constraints are target-file constraints. Secondary tests,
        # docs, or helpers may legitimately mention a removed token while
        # verifying or documenting its absence from the target artifact.
        inspected_paths = [target_path]
        matched_paths: list[str] = []
        for path in inspected_paths:
            content = materialized.get(path, "")
            baseline = snapshot_baselines.get(
                path,
                _target_slice(plan.coder_packet.context_slices, path),
            )
            patch = _patch_for_path(diff, path)
            matched = forbidden in content
            if matched:
                matched_paths.append(path)
            evidence.append(
                _review_evidence(
                    requirement_id=requirement_id,
                    requirement_kind="must_not_contain",
                    intended_paths=inspected_paths,
                    inspected_path=path,
                    baseline=baseline,
                    applied=content,
                    patch=patch,
                    task_id=bound_task_id,
                    attempt_id=bound_attempt_id,
                    extraction_method="architect_constraint_forbidden_literal",
                    baseline_match_count=baseline.count(forbidden),
                    applied_match_count=content.count(forbidden),
                    introduced=None,
                    satisfied=not matched,
                )
            )
        for finding_path in matched_paths:
            findings.append(
                ReviewFinding(
                    "forbidden_must_not_contain",
                    forbidden,
                    finding_path,
                )
            )

    diff_sha256 = hashlib.sha256(diff.encode("utf-8")).hexdigest()
    if constraints.max_added_lines is not None and added > constraints.max_added_lines:
        findings.append(
            ReviewFinding(
                "max_added_lines_exceeded",
                f"{added}>{constraints.max_added_lines}",
                target_path,
            )
        )
    if constraints.max_added_lines is not None:
        evidence.append(
            ReviewEvidence(
                requirement_id="constraint.max_added_lines",
                requirement_kind="max_added_lines",
                intended_paths=changed_paths or [target_path],
                inspected_path="*",
                baseline_sha256=_sha256_text(""),
                applied_sha256=diff_sha256,
                diff_hunk_sha256=diff_sha256,
                diff_hunk_line_count=len(diff.splitlines()),
                task_id=bound_task_id,
                attempt_id=bound_attempt_id,
                extraction_method="unified_diff_added_line_count",
                baseline_match_count=0,
                applied_match_count=added,
                introduced=None,
                satisfied=added <= constraints.max_added_lines,
            )
        )

    if constraints.max_removed_lines is not None and removed > constraints.max_removed_lines:
        findings.append(
            ReviewFinding(
                "max_removed_lines_exceeded",
                f"{removed}>{constraints.max_removed_lines}",
                target_path,
            )
        )
    if constraints.max_removed_lines is not None:
        evidence.append(
            ReviewEvidence(
                requirement_id="constraint.max_removed_lines",
                requirement_kind="max_removed_lines",
                intended_paths=changed_paths or [target_path],
                inspected_path="*",
                baseline_sha256=_sha256_text(""),
                applied_sha256=diff_sha256,
                diff_hunk_sha256=diff_sha256,
                diff_hunk_line_count=len(diff.splitlines()),
                task_id=bound_task_id,
                attempt_id=bound_attempt_id,
                extraction_method="unified_diff_removed_line_count",
                baseline_match_count=0,
                applied_match_count=removed,
                introduced=None,
                satisfied=removed <= constraints.max_removed_lines,
            )
        )

    for index, import_name in enumerate(constraints.preserve_imports):
        baseline_preserved = _import_is_preserved(base_content, import_name)
        applied_preserved = _import_is_preserved(new_content, import_name)
        preserved = not baseline_preserved or applied_preserved
        evidence.append(
            _review_evidence(
                requirement_id=f"constraint.preserve_import.{index}",
                requirement_kind="preserve_import",
                intended_paths=[target_path],
                inspected_path=target_path,
                baseline=base_content,
                applied=new_content,
                patch=_patch_for_path(diff, target_path),
                task_id=bound_task_id,
                attempt_id=bound_attempt_id,
                extraction_method="target_import_statement_scan",
                baseline_match_count=int(baseline_preserved),
                applied_match_count=int(applied_preserved),
                introduced=None,
                satisfied=preserved,
            )
        )
        if not preserved:
            findings.append(ReviewFinding("imports_violated", import_name, target_path))

    for index, export_name in enumerate(constraints.preserve_exports):
        baseline_export = _export_is_preserved(base_content, export_name)
        applied_export = _export_is_preserved(new_content, export_name)
        preserved = not baseline_export or applied_export
        evidence.append(
            _review_evidence(
                requirement_id=f"constraint.preserve_export.{index}",
                requirement_kind="preserve_export",
                intended_paths=[target_path],
                inspected_path=target_path,
                baseline=base_content,
                applied=new_content,
                patch=_patch_for_path(diff, target_path),
                task_id=bound_task_id,
                attempt_id=bound_attempt_id,
                extraction_method="target_export_statement_scan",
                baseline_match_count=int(baseline_export),
                applied_match_count=int(applied_export),
                introduced=None,
                satisfied=preserved,
            )
        )
        if not preserved:
            findings.append(ReviewFinding("exports_violated", export_name, target_path))

    for index, (source, final, transformation_path) in enumerate(
        _task_transformation_requirements(
            canonical_task,
            target_path=target_path,
            exact_allowed_paths=exact_allowed_paths,
        )
    ):
        intended_paths = [transformation_path]
        transformation_satisfied = False
        for path in intended_paths:
            baseline = snapshot_baselines.get(
                path,
                _target_slice(plan.coder_packet.context_slices, path),
            )
            applied = materialized.get(path, baseline)
            patch = _patch_for_path(diff, path)
            relevant_patch = _transformation_evidence_patch(patch, source, final)
            baseline_source_count = baseline.count(source)
            applied_source_count = applied.count(source)
            satisfied = bool(
                baseline_source_count > 0
                and final in applied
                and relevant_patch
            )
            transformation_satisfied = transformation_satisfied or satisfied
            evidence.append(
                _review_evidence(
                    requirement_id=f"task.transformation.{index}",
                    requirement_kind="transformation",
                    intended_paths=intended_paths,
                    inspected_path=path,
                    baseline=baseline,
                    applied=applied,
                    patch=relevant_patch or patch,
                    task_id=bound_task_id,
                    attempt_id=bound_attempt_id,
                    extraction_method="task_exact_transformation_source_and_final_hunk",
                    baseline_match_count=baseline_source_count,
                    applied_match_count=applied_source_count,
                    introduced=bool(relevant_patch),
                    satisfied=satisfied,
                )
            )
        if not transformation_satisfied:
            findings.append(
                ReviewFinding(
                    "transformation_source_not_replaced",
                    f'{source!r} was not replaced by {final!r} in one relevant hunk.',
                    intended_paths[0],
                )
            )

    for criterion in plan.coder_packet.acceptance_criteria:
        if criterion.kind != "literal":
            evidence.append(
                _review_evidence(
                    requirement_id=criterion.id,
                    requirement_kind="behavioral",
                    intended_paths=[target_path],
                    inspected_path=target_path,
                    baseline=base_content,
                    applied=new_content,
                    patch=_patch_for_path(diff, target_path),
                    task_id=bound_task_id,
                    attempt_id=bound_attempt_id,
                    extraction_method="behavioral_deferred_to_tests_and_verifier",
                    baseline_match_count=0,
                    applied_match_count=0,
                    introduced=None,
                    satisfied=None,
                )
            )
            continue
        intended_paths, unauthorized_paths, artifact_path_spans = (
            _criterion_intended_paths(
                criterion.description,
                target_path=target_path,
                exact_allowed_paths=exact_allowed_paths,
            )
        )
        literal_needles = _literal_needles(
            criterion.description,
            excluded_spans=artifact_path_spans,
        )
        if unauthorized_paths:
            findings.append(
                ReviewFinding(
                    "literal_acceptance_path_unauthorized",
                    criterion.description,
                    unauthorized_paths[0],
                )
            )
            intended_paths = unauthorized_paths
        requirement_evidence, satisfied = _exact_requirement_evidence(
            plan=plan,
            diff=diff,
            materialized=materialized,
            requirement_id=criterion.id,
            requirement_kind="literal_acceptance",
            needles=literal_needles,
            intended_paths=intended_paths,
            task_id=bound_task_id,
            attempt_id=bound_attempt_id,
            extraction_method="quoted_or_class_fragment_literal",
            change_mode=(
                _requirement_change_mode(
                    canonical_task,
                    " ".join(literal_needles),
                )
                or _requirement_change_mode(
                    criterion.description,
                    " ".join(literal_needles),
                )
            ),
            authority_satisfied=not unauthorized_paths,
            artifact_baselines=snapshot_baselines,
        )
        evidence.extend(requirement_evidence)
        if literal_needles and not satisfied and not unauthorized_paths:
            change_mode = _requirement_change_mode(
                canonical_task,
                " ".join(literal_needles),
            ) or _requirement_change_mode(
                criterion.description,
                " ".join(literal_needles),
            )
            misplaced = _misplaced_requirement_evidence(requirement_evidence)
            finding_id = (
                f"literal_acceptance_misplaced_{misplaced[0]}"
                if misplaced is not None
                else (
                    "literal_acceptance_not_introduced"
                    if change_mode is not None
                    and any(item.applied_match_count for item in requirement_evidence)
                    else "literal_acceptance_missing"
                )
            )
            findings.append(
                ReviewFinding(
                    finding_id,
                    criterion.description,
                    misplaced[1] if misplaced is not None else intended_paths[0],
                )
            )

    for path in unbound_existing_paths:
        findings.append(
            ReviewFinding(
                "artifact_baseline_unbound",
                "An existing changed artifact requires a server-owned snapshot or plan context.",
                path,
            )
        )
    return ReviewReport(passed=not findings, findings=findings, evidence=evidence)


def review_diff_with_llm(
    plan: ArchitectPlan,
    diff: str,
    *,
    llm_call: Callable[[str, str], str] | None = None,
) -> ReviewReport:
    if plan.classification.task_class not in {"implement", "refactor", "style"}:
        return ReviewReport(passed=True, findings=[])

    alias = _reviewer_model_alias()
    if not alias and llm_call is None:
        return ReviewReport(passed=True, findings=[])
    if llm_call is None and alias not in available_model_aliases():
        return ReviewReport(passed=True, findings=[])

    selected_alias = alias or "local"
    prompt = _reviewer_prompt(plan, diff)
    try:
        raw = (
            llm_call(prompt, selected_alias)
            if llm_call is not None
            else _call_reviewer_llm(prompt, model_alias=selected_alias)
        )
        return _review_report_from_llm_payload(
            _parse_json_object(raw),
            default_path=plan.coder_packet.target_file.path,
        )
    except Exception:
        # The Reviewer is advisory. Slow, unavailable, or malformed LLM output falls back
        # to the deterministic review result instead of blocking approval.
        return ReviewReport(passed=True, findings=[])


def reviewer_llm_is_configured() -> bool:
    alias = _reviewer_model_alias()
    return bool(alias and alias in available_model_aliases())


def _changed_line_counts(diff: str) -> tuple[int, int]:
    added = 0
    removed = 0
    for line, kind in _classified_diff_lines(diff):
        if kind == "addition":
            added += 1
        elif kind == "removal":
            removed += 1
    return added, removed


def _materialize_target_content(
    plan: ArchitectPlan,
    diff: str,
    *,
    baseline_content: str | None = None,
) -> str:
    target_path = plan.coder_packet.target_file.path
    return _materialize_path_content(
        plan,
        diff,
        target_path,
        baseline_content=baseline_content,
    )


def _materialize_path_content(
    plan: ArchitectPlan,
    diff: str,
    target_path: str,
    *,
    baseline_content: str | None = None,
) -> str:
    context_slice = _context_slice_for_path(
        plan.coder_packet.context_slices,
        target_path,
    )
    baseline_is_bound = baseline_content is not None or context_slice is not None
    base_content = (
        baseline_content
        if baseline_content is not None
        else (context_slice.content if context_slice is not None else "")
    )
    file_patch = _patch_for_path(diff, target_path)
    if not file_patch:
        return base_content
    try:
        return _apply_file_patch(base_content, file_patch)
    except ValueError:
        # Never invent applied evidence from a malformed patch.  The independent
        # Git apply check reports the syntax failure; deterministic review keeps
        # the trusted baseline so malformed additions cannot satisfy a contract.
        return base_content if baseline_is_bound else _new_content_from_patch(file_patch)


def _target_slice(slices: list[ContextSlice], target_path: str) -> str:
    fallback = ""
    for context_slice in slices:
        if context_slice.path != target_path:
            continue
        if context_slice.kind == "target":
            return context_slice.content
        fallback = context_slice.content
    return fallback


def _changed_paths(diff: str) -> list[str]:
    paths: list[str] = []
    for candidate, _patch in _file_patch_sections(diff):
        if candidate and candidate != "/dev/null" and candidate not in paths:
            paths.append(candidate)
    return paths


def _exact_allowed_review_paths(
    task_spec: Mapping[str, Any] | None,
    target_path: str,
) -> list[str]:
    """Return exact server-authorized artifact paths, never broad patterns."""

    paths = [target_path]
    if not isinstance(task_spec, Mapping):
        return paths
    values = task_spec.get("allowed_files", task_spec.get("allowedFiles"))
    if not isinstance(values, list):
        return paths
    for value in values:
        normalized = _normalize_repo_path(str(value or ""))
        if (
            not normalized
            or path_escapes_workspace(normalized)
            or has_percent_encoded_path_syntax(normalized)
            or normalized.endswith("/")
            or any(char in normalized for char in "*?[]{}")
        ):
            continue
        if normalized not in paths:
            paths.append(normalized)
    return paths


def _criterion_intended_paths(
    description: str,
    *,
    target_path: str,
    exact_allowed_paths: list[str],
) -> tuple[list[str], list[str], list[tuple[int, int]]]:
    mentioned: list[str] = []
    unauthorized: list[str] = []
    artifact_path_spans: list[tuple[int, int]] = []
    quoted_spans: list[tuple[int, int]] = []
    for match in re.finditer(
        r"(?P<quote>[\"'`])(?P<value>[^\"'`\n]+)(?P=quote)",
        description,
    ):
        quoted_spans.append(match.span())
        value = _normalize_repo_path(match.group("value"))
        if (
            not value
            or not _looks_like_artifact_path(value, exact_allowed_paths)
            or not _path_occurrence_is_artifact_binding(
                description,
                match.start(),
                match.end(),
            )
        ):
            continue
        artifact_path_spans.append(match.span())
        if value in exact_allowed_paths:
            if value not in mentioned:
                mentioned.append(value)
        else:
            unauthorized.append(value)
    for path in exact_allowed_paths:
        for match in re.finditer(
            rf"(?<![A-Za-z0-9_./-]){re.escape(path)}"
            rf"(?![A-Za-z0-9_/-]|\.[A-Za-z0-9_-])",
            description.replace("\\", "/"),
        ):
            if any(start <= match.start() < end for start, end in quoted_spans):
                continue
            if not _path_occurrence_is_artifact_binding(
                description,
                match.start(),
                match.end(),
            ):
                continue
            if path not in mentioned:
                mentioned.append(path)
    return (
        mentioned or [target_path],
        list(dict.fromkeys(unauthorized)),
        list(dict.fromkeys(artifact_path_spans)),
    )


def _looks_like_artifact_path(value: str, exact_allowed_paths: list[str]) -> bool:
    name = value.rsplit("/", 1)[-1].lower()
    return bool(
        value in exact_allowed_paths
        or "/" in value
        or name.startswith(".")
        or re.search(r"\.[a-z0-9][a-z0-9_-]{0,12}$", name)
    )


def _path_occurrence_is_artifact_binding(
    description: str,
    start: int,
    end: int,
) -> bool:
    line_start = description.rfind("\n", 0, start) + 1
    line_end = description.find("\n", end)
    if line_end < 0:
        line_end = len(description)
    prefix = description[max(line_start, start - 96) : start]
    suffix = description[end : min(line_end, end + 96)]
    suffix_binds = bool(
        re.match(
            r"\s+(?:must|should|shall)\s+(?:contain|include|have)\b",
            suffix,
            flags=re.IGNORECASE,
        )
    )
    prefix_binds = bool(
        re.search(
            r"\b(?:artifact|file|in|inside|target|to|within|exact\s+path)"
            r"(?:\s+path)?\s*$",
            prefix,
            flags=re.IGNORECASE,
        )
    )
    suffix_is_literal_contract = bool(
        re.match(
            r"\s+(?:must|should|shall|needs?\s+to)\s+"
            r"(?:appear\b(?:\s+in\s+(?:the\s+)?(?:output|text|label|message))?"
            r"|equal\b"
            r"|(?:be\s+)?(?:displayed|emitted|printed|rendered|shown)\b)",
            suffix,
            flags=re.IGNORECASE,
        )
    )
    if suffix_is_literal_contract:
        return False
    if suffix_binds:
        return True
    if prefix_binds and not re.search(
        r"\b(?:copy|display|emit|print|render|say|show)\b[^\n.!?]{0,80}$",
        prefix,
        flags=re.IGNORECASE,
    ):
        return True
    if re.match(
        r"\s+(?:in|as)\s+(?:the\s+)?(?:rendered\s+)?"
        r"(?:output|text|label|message)\b",
        suffix,
        flags=re.IGNORECASE,
    ):
        return False
    return bool(
        re.match(
            r"\s+(?:artifact|file|target)(?:\s+path)?\b",
            suffix,
            flags=re.IGNORECASE,
        )
    )


def _description_mentions_path(description: str, path: str) -> bool:
    return bool(
        re.search(
            rf"(?<![A-Za-z0-9_./-]){re.escape(path)}"
            rf"(?![A-Za-z0-9_/-]|\.[A-Za-z0-9_-])",
            description.replace("\\", "/"),
        )
    )


def _exact_requirement_evidence(
    *,
    plan: ArchitectPlan,
    diff: str,
    materialized: Mapping[str, str],
    requirement_id: str,
    requirement_kind: str,
    needles: list[str],
    intended_paths: list[str],
    task_id: str,
    attempt_id: str,
    extraction_method: str,
    change_mode: str | None,
    authority_satisfied: bool = True,
    artifact_baselines: Mapping[str, str] | None = None,
) -> tuple[list[ReviewEvidence], bool]:
    evidence: list[ReviewEvidence] = []
    any_satisfied = False
    target_path = plan.coder_packet.target_file.path
    for path in intended_paths:
        context_slice = _context_slice_for_path(plan.coder_packet.context_slices, path)
        baseline = (
            artifact_baselines.get(path, "")
            if artifact_baselines is not None and path in artifact_baselines
            else (context_slice.content if context_slice is not None else "")
        )
        patch = _patch_for_path(diff, path)
        artifact_bound = bool(
            path == target_path
            or context_slice is not None
            or (artifact_baselines is not None and path in artifact_baselines)
            or _patch_creates_complete_file(patch, path)
        )
        applied = materialized.get(path)
        if applied is None:
            applied = (
                _materialize_path_content(
                    plan,
                    diff,
                    path,
                    baseline_content=baseline,
                )
                if patch
                else baseline
            )
        baseline_counts = [baseline.count(needle) for needle in needles]
        applied_counts = [applied.count(needle) for needle in needles]
        baseline_match_count = min(baseline_counts) if baseline_counts else 0
        applied_match_count = min(applied_counts) if applied_counts else 0
        added_match_counts = [
            _added_hunk_text(patch).count(needle) for needle in needles
        ]
        evidence_patch = _relevant_evidence_patch(patch, needles)
        hunk_introduced = bool(
            added_match_counts and min(added_match_counts) > 0
        )
        introduced = (
            (
                hunk_introduced
                and (
                    change_mode != "introduce"
                    or applied_match_count > baseline_match_count
                )
            )
            if needles
            else None
        )
        satisfied: bool | None = None
        if needles:
            satisfied = bool(
                authority_satisfied
                and artifact_bound
                and applied_match_count > 0
                and (change_mode is None or introduced is True)
            )
            any_satisfied = any_satisfied or satisfied
        evidence.append(
            _review_evidence(
                requirement_id=requirement_id,
                requirement_kind=requirement_kind,
                intended_paths=intended_paths,
                inspected_path=path,
                baseline=baseline,
                applied=applied,
                patch=evidence_patch,
                task_id=task_id,
                attempt_id=attempt_id,
                extraction_method=(
                    (
                        extraction_method
                        if authority_satisfied
                        else f"{extraction_method}:unauthorized_path"
                    )
                    if artifact_bound
                    else f"{extraction_method}:artifact_baseline_unbound"
                ),
                baseline_match_count=baseline_match_count,
                applied_match_count=applied_match_count,
                introduced=introduced,
                satisfied=satisfied,
            )
        )
    if needles:
        for path, applied in materialized.items():
            if path in intended_paths:
                continue
            applied_counts = [applied.count(needle) for needle in needles]
            applied_match_count = min(applied_counts) if applied_counts else 0
            if applied_match_count <= 0:
                continue
            baseline = (
                artifact_baselines.get(path, "")
                if artifact_baselines is not None and path in artifact_baselines
                else _target_slice(plan.coder_packet.context_slices, path)
            )
            patch = _patch_for_path(diff, path)
            evidence_patch = _relevant_evidence_patch(patch, needles)
            baseline_counts = [baseline.count(needle) for needle in needles]
            baseline_match_count = min(baseline_counts) if baseline_counts else 0
            category = _artifact_evidence_category(path)
            evidence.append(
                _review_evidence(
                    requirement_id=requirement_id,
                    requirement_kind=requirement_kind,
                    intended_paths=intended_paths,
                    inspected_path=path,
                    baseline=baseline,
                    applied=applied,
                    patch=evidence_patch,
                    task_id=task_id,
                    attempt_id=attempt_id,
                    extraction_method=f"{extraction_method}:misplaced:{category}",
                    baseline_match_count=baseline_match_count,
                    applied_match_count=applied_match_count,
                    introduced=bool(
                        min(
                            _added_hunk_text(patch).count(needle)
                            for needle in needles
                        )
                        > 0
                    ),
                    satisfied=False,
                )
            )
    return evidence, any_satisfied


def _added_hunk_text(patch: list[str]) -> str:
    changed_lines: list[str] = []
    old_lines: list[str] = []
    new_lines: list[str] = []

    def finish_hunk() -> None:
        if not old_lines and not new_lines:
            return
        matcher = SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
        for tag, _old_start, _old_end, new_start, new_end in matcher.get_opcodes():
            if tag in {"insert", "replace"}:
                changed_lines.extend(new_lines[new_start:new_end])
        old_lines.clear()
        new_lines.clear()

    in_hunk = False
    for line in patch:
        if line.startswith("@@"):
            finish_hunk()
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if line.startswith("+"):
            new_lines.append(line[1:])
        elif line.startswith("-"):
            old_lines.append(line[1:])
        elif line.startswith(" "):
            value = line[1:]
            old_lines.append(value)
            new_lines.append(value)
    finish_hunk()
    return "\n".join(changed_lines)


def _relevant_evidence_patch(
    patch: list[str],
    needles: list[str],
) -> list[str]:
    if not patch or not needles:
        return patch
    header: list[str] = []
    hunks: list[list[str]] = []
    current: list[str] = []
    for line in patch:
        if line.startswith("@@"):
            if current:
                hunks.append(current)
            current = [line]
        elif current:
            current.append(line)
        else:
            header.append(line)
    if current:
        hunks.append(current)
    relevant = [
        hunk
        for hunk in hunks
        if any(
            needle in _added_hunk_text(hunk)
            or any(
                needle in line[1:]
                for line in hunk
                if line.startswith((" ", "+"))
            )
            for needle in needles
        )
    ]
    if not relevant:
        return patch
    return [*header, *(line for hunk in relevant for line in hunk)]


def _artifact_evidence_category(path: str) -> str:
    normalized = path.replace("\\", "/").lower()
    name = normalized.rsplit("/", 1)[-1]
    parts = [part for part in normalized.split("/") if part]
    if "decoy" in name or "/decoy/" in f"/{normalized}/":
        return "decoy"
    if any(part in {"evidence", "generated", "artifacts"} for part in parts[:-1]):
        return "generated_evidence"
    if (
        normalized.startswith(("test/", "tests/"))
        or "/tests/" in f"/{normalized}/"
        or "/__tests__/" in f"/{normalized}/"
        or name.startswith("test_")
        or ".test." in name
        or ".spec." in name
    ):
        return "test"
    if normalized.startswith(("doc/", "docs/")) or name.endswith(
        (".md", ".mdx", ".rst")
    ):
        return "documentation"
    return "wrong_production"


def _misplaced_requirement_evidence(
    evidence: list[ReviewEvidence],
) -> tuple[str, str] | None:
    for item in evidence:
        marker = ":misplaced:"
        if marker in item.extraction_method:
            return item.extraction_method.rsplit(marker, 1)[-1], item.inspected_path
    return None


def _review_evidence(
    *,
    requirement_id: str,
    requirement_kind: str,
    intended_paths: list[str],
    inspected_path: str,
    baseline: str,
    applied: str,
    patch: list[str],
    task_id: str,
    attempt_id: str,
    extraction_method: str,
    baseline_match_count: int,
    applied_match_count: int,
    introduced: bool | None,
    satisfied: bool | None,
) -> ReviewEvidence:
    patch_text = "\n".join(patch)
    return ReviewEvidence(
        requirement_id=requirement_id,
        requirement_kind=requirement_kind,
        intended_paths=list(intended_paths),
        inspected_path=inspected_path,
        baseline_sha256=_sha256_text(baseline),
        applied_sha256=_sha256_text(applied),
        diff_hunk_sha256=_sha256_text(patch_text),
        diff_hunk_line_count=len(patch),
        task_id=task_id,
        attempt_id=attempt_id,
        extraction_method=extraction_method,
        baseline_match_count=baseline_match_count,
        applied_match_count=applied_match_count,
        introduced=introduced,
        satisfied=satisfied,
    )


def _context_slice_for_path(
    slices: list[ContextSlice],
    path: str,
) -> ContextSlice | None:
    for context_slice in slices:
        if context_slice.path == path:
            return context_slice
    return None


def _patch_creates_complete_file(patch: list[str], path: str) -> bool:
    classified = _classified_diff_lines("\n".join(patch))
    old_is_null = any(
        kind == "old_header" and line.strip() == "--- /dev/null"
        for line, kind in classified
    )
    new_matches = any(
        kind == "new_header" and _normalize_diff_path(line[4:]) == path
        for line, kind in classified
    )
    return old_is_null and new_matches


_TASK_TRANSFORMATION_PATTERNS = (
    re.compile(
        r"\b(?:replace|change|rename)\s+"
        r"(?:(?:the\s+)?(?:copy|heading|label|message|response|status|string|text|title|value|word)\s+)?"
        r"(?P<src_quote>[\"'`])(?P<source>[^\"'`\n]+)(?P=src_quote)\s+"
        r"(?:with|to|as)\s+"
        r"(?P<final_quote>[\"'`])(?P<final>[^\"'`\n]+)(?P=final_quote)",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\bswap\s+"
        r"(?:(?:the\s+)?(?:copy|heading|label|message|response|status|string|text|title|value|word)\s+)?"
        r"(?P<src_quote>[\"'`])(?P<source>[^\"'`\n]+)(?P=src_quote)\s+for\s+"
        r"(?P<final_quote>[\"'`])(?P<final>[^\"'`\n]+)(?P=final_quote)",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\bfrom\s+"
        r"(?P<src_quote>[\"'`])(?P<source>[^\"'`\n]+)(?P=src_quote)\s+to\s+"
        r"(?P<final_quote>[\"'`])(?P<final>[^\"'`\n]+)(?P=final_quote)",
        flags=re.IGNORECASE,
    ),
)


def _task_transformation_requirements(
    text: str,
    *,
    target_path: str,
    exact_allowed_paths: list[str],
) -> list[tuple[str, str, str]]:
    requirements: list[tuple[str, str, str]] = []
    for pattern in _TASK_TRANSFORMATION_PATTERNS:
        for match in pattern.finditer(text):
            line_start = text.rfind("\n", 0, match.start()) + 1
            if re.search(
                r"\b(?:do\s+not|don't|must\s+not|never)\s*$",
                text[line_start : match.start()],
                flags=re.IGNORECASE,
            ):
                continue
            source = match.group("source").strip()
            final = match.group("final").strip()
            if not source or not final or source == final:
                continue
            line_end = text.find("\n", match.end())
            if line_end < 0:
                line_end = len(text)
            line = text[line_start:line_end]
            relative_source_start = match.start("source") - line_start
            relative_source_end = match.end("source") - line_start
            relative_final_start = match.start("final") - line_start
            relative_final_end = match.end("final") - line_start
            if (
                _looks_like_artifact_path(source, [])
                and _path_occurrence_is_artifact_binding(
                    line,
                    relative_source_start,
                    relative_source_end,
                )
            ) or (
                _looks_like_artifact_path(final, [])
                and _path_occurrence_is_artifact_binding(
                    line,
                    relative_final_start,
                    relative_final_end,
                )
            ):
                continue
            intended_path = target_path
            normalized_line = line.replace("\\", "/")
            matched_path = ""
            for allowed_path in exact_allowed_paths:
                for path_match in re.finditer(
                    rf"(?<![A-Za-z0-9_./-]){re.escape(allowed_path)}"
                    rf"(?![A-Za-z0-9_/-]|\.[A-Za-z0-9_-])",
                    normalized_line,
                ):
                    binding_start = path_match.start()
                    binding_end = path_match.end()
                    if (
                        binding_start > 0
                        and binding_end < len(normalized_line)
                        and normalized_line[binding_start - 1] in "\"'`"
                        and normalized_line[binding_end]
                        == normalized_line[binding_start - 1]
                    ):
                        binding_start -= 1
                        binding_end += 1
                    if _path_occurrence_is_artifact_binding(
                        normalized_line,
                        binding_start,
                        binding_end,
                    ):
                        matched_path = allowed_path
                        break
                if matched_path:
                    break
            if matched_path:
                intended_path = matched_path
            pair = (source, final, intended_path)
            if pair not in requirements:
                requirements.append(pair)
    return requirements


def _transformation_evidence_patch(
    patch: list[str],
    source: str,
    final: str,
) -> list[str]:
    header: list[str] = []
    hunks: list[list[str]] = []
    current: list[str] = []
    for line in patch:
        if line.startswith("@@"):
            if current:
                hunks.append(current)
            current = [line]
        elif current:
            current.append(line)
        else:
            header.append(line)
    if current:
        hunks.append(current)
    relevant = [hunk for hunk in hunks if _hunk_replaces_literal(hunk, source, final)]
    return [*header, *(line for hunk in relevant for line in hunk)] if relevant else []


def _hunk_replaces_literal(hunk: list[str], source: str, final: str) -> bool:
    old_lines: list[str] = []
    new_lines: list[str] = []
    for line in hunk[1:]:
        if line == r"\ No newline at end of file":
            continue
        if line.startswith("-"):
            old_lines.append(line[1:])
        elif line.startswith("+"):
            new_lines.append(line[1:])
        elif line.startswith(" "):
            old_lines.append(line[1:])
            new_lines.append(line[1:])
    matcher = SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if tag != "replace":
            continue
        old_segment = "\n".join(old_lines[old_start:old_end])
        new_segment = "\n".join(new_lines[new_start:new_end])
        if source in old_segment and final in new_segment:
            return True
    return False


def _is_structural_symbol_target_reference(
    text: str,
    *,
    position: int,
    needle: str,
    clause_prefix: str,
) -> bool:
    """Distinguish an existing code target from a literal being introduced.

    Backticked identifiers commonly name the object of a requested change, as
    in ``Add pagination to `list_records``` or ``Update `load_record``` (the
    identifier is expected to survive, not to appear on a newly added line).
    Replacement destinations remain change requirements: ``Rename `old` to
    `new``` must still prove that ``new`` was introduced.
    """

    if re.fullmatch(
        r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*",
        needle,
    ) is None:
        return False
    end = position + len(needle)
    if (
        position <= 0
        or end >= len(text)
        or text[position:end].casefold() != needle.casefold()
        or text[position - 1] != "`"
        or text[end] != "`"
    ):
        return False

    prefix = clause_prefix.rstrip()
    # Replacement destinations use a narrow verb/preposition grammar.  Keep
    # the match in the current request segment so an earlier rename cannot
    # turn a later structural target into a required new symbol.
    request_segment = re.split(
        r"(?:\b(?:and|then)\s+|[;,]\s*)(?="
        r"(?:add|append|change|convert|create|fix|insert|introduce|modify|"
        r"refactor|rename|replace|swap|transform|update|write)\b)",
        prefix,
        flags=re.IGNORECASE,
    )[-1]
    if re.search(
        r"(?:"
        r"\b(?:change|convert|rename|transform)\b[^\n.!?]{0,120}\bto"
        r"|\breplace\b[^\n.!?]{0,120}\bwith"
        r"|\bswap\b[^\n.!?]{0,120}\b(?:for|with)"
        r")\s+`$",
        request_segment,
        flags=re.IGNORECASE,
    ):
        return False
    if re.search(
        r"\b(?:to|in|inside|within|on|for|with)\s+`$",
        prefix,
        flags=re.IGNORECASE,
    ):
        return True
    return bool(
        re.search(
            r"\b(?:change|fix|modify|refactor|rename|replace|update)\s+`$",
            prefix,
            flags=re.IGNORECASE,
        )
    )


def _requirement_change_mode(text: str, needle: str) -> str | None:
    normalized = str(text or "")
    positions = [
        match.start()
        for match in re.finditer(re.escape(needle), normalized, flags=re.IGNORECASE)
    ] if needle else []
    prefixes = []
    for position in positions or [min(len(normalized), 160)]:
        prefix = normalized[max(0, position - 160) : position]
        boundary = max(
            prefix.rfind("\n"),
            prefix.rfind("."),
            prefix.rfind("!"),
            prefix.rfind("?"),
        )
        clause_prefix = prefix[boundary + 1 :].strip()
        if _is_structural_symbol_target_reference(
            normalized,
            position=position,
            needle=needle,
            clause_prefix=clause_prefix,
        ):
            continue
        prefixes.append(clause_prefix)
    introduce_verbs = r"add|append|create|insert|introduce|newly\s+include"
    mutate_verbs = r"change|convert|modify|rename|replace|swap|transform|update|write"
    verbs = rf"{introduce_verbs}|{mutate_verbs}"
    for prefix in prefixes:
        if re.search(
            rf"\b(?:do\s+not|don't|must\s+not|never)\s+(?:{verbs})\b",
            prefix,
            flags=re.IGNORECASE,
        ):
            continue
        if re.search(
            rf"^(?:(?:please|can\s+you|could\s+you|we\s+need\s+to|need\s+to)\s+)?"
            rf"(?:(?:in|inside|within|file|target)\b[^,:]{{0,72}}[:,]\s*)?"
            rf"(?:{verbs})\b[^\n.!?]{{0,120}}$",
            prefix,
            flags=re.IGNORECASE,
        ):
            verb_match = re.search(
                rf"\b(?P<verb>{verbs})\b",
                prefix,
                flags=re.IGNORECASE,
            )
            if verb_match and re.fullmatch(
                introduce_verbs,
                verb_match.group("verb"),
                flags=re.IGNORECASE,
            ):
                return "introduce"
            return "mutate"
    return None


def _requirement_requires_change(text: str, needle: str) -> bool:
    return _requirement_change_mode(text, needle) is not None


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _patch_for_path(diff: str, target_path: str) -> list[str]:
    found: list[str] = []
    for path, patch in _file_patch_sections(diff):
        if path == target_path:
            found = patch
    return found


def _file_patch_sections(diff: str) -> list[tuple[str, list[str]]]:
    """Split a unified diff without confusing hunk content with file headers.

    A valid added source line such as ``++ counter;`` is encoded as
    ``+++ counter;``.  Header recognition therefore has to be stateful instead
    of relying on a global string-prefix test.
    """

    sections: list[tuple[str, list[str]]] = []
    current: list[str] = []
    current_path = ""
    seen_old_header = False

    def finish_current() -> None:
        nonlocal current, current_path, seen_old_header
        if current and current_path:
            sections.append((current_path, current))
        current = []
        current_path = ""
        seen_old_header = False

    for line, kind in _classified_diff_lines(diff):
        if kind == "diff_header":
            finish_current()
            current = [line]
            paths = _diff_git_paths(line)
            current_path = (
                _normalize_diff_path(paths[1]) if len(paths) >= 2 else ""
            )
            continue
        if kind == "old_header":
            if seen_old_header:
                finish_current()
            if not current:
                current = []
            current.append(line)
            seen_old_header = True
            old_path = _normalize_diff_path(line[4:].strip())
            if old_path:
                current_path = old_path
            continue
        if kind == "new_header":
            if not current:
                current = []
            current.append(line)
            new_path = _normalize_diff_path(line[4:].strip())
            if new_path:
                current_path = new_path
            continue
        if current:
            current.append(line)
    finish_current()
    return sections


def _duplicate_diff_section_paths(diff: str) -> list[str]:
    counts: dict[str, int] = {}
    for path, _patch in _file_patch_sections(diff):
        if path:
            counts[path] = counts.get(path, 0) + 1
    return [path for path, count in counts.items() if count > 1]


def _diff_git_paths(line: str) -> list[str]:
    body = line.removeprefix("diff --git ").strip()
    matches = re.findall(r'"((?:\\.|[^"])*)"', body)
    if len(matches) >= 2:
        return [match.replace(r"\"", '"') for match in matches[:2]]
    return body.split()


_HUNK_RE = re.compile(r"^@@\s+-(\d+)(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@")
_HUNK_COUNTS_RE = re.compile(
    r"^@@\s+-\d+(?:,(\d+))?\s+\+\d+(?:,(\d+))?\s+@@"
)


def _classified_diff_lines(diff: str) -> list[tuple[str, str]]:
    lines = diff.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    classified: list[tuple[str, str]] = []
    in_hunk = False
    old_remaining = 0
    new_remaining = 0
    for line in lines:
        if line.startswith("diff --git "):
            in_hunk = False
            old_remaining = 0
            new_remaining = 0
            classified.append((line, "diff_header"))
            continue
        hunk_match = _HUNK_COUNTS_RE.match(line)
        if hunk_match:
            old_remaining = int(hunk_match.group(1) or "1")
            new_remaining = int(hunk_match.group(2) or "1")
            in_hunk = old_remaining > 0 or new_remaining > 0
            classified.append((line, "hunk_header"))
            continue
        if in_hunk:
            if line == r"\ No newline at end of file":
                classified.append((line, "no_newline"))
                continue
            if line.startswith("+"):
                new_remaining -= 1
                kind = "addition"
            elif line.startswith("-"):
                old_remaining -= 1
                kind = "removal"
            elif line.startswith(" "):
                old_remaining -= 1
                new_remaining -= 1
                kind = "context"
            else:
                kind = "hunk_metadata"
            classified.append((line, kind))
            if old_remaining <= 0 and new_remaining <= 0:
                in_hunk = False
            continue
        if line.startswith("--- "):
            kind = "old_header"
        elif line.startswith("+++ "):
            kind = "new_header"
        else:
            kind = "metadata"
        classified.append((line, kind))
    return classified


def _content_line_records(content: str) -> list[tuple[str, bool]]:
    if not content:
        return []
    parts = content.split("\n")
    if content.endswith("\n"):
        return [(line, True) for line in parts[:-1]]
    return [
        *((line, True) for line in parts[:-1]),
        (parts[-1], False),
    ]


def _apply_file_patch(old_content: str, patch_lines: list[str]) -> str:
    old_lines = _content_line_records(old_content)
    output: list[tuple[str, bool]] = []
    old_index = 0
    i = 0
    while i < len(patch_lines):
        match = _HUNK_RE.match(patch_lines[i])
        if not match:
            i += 1
            continue
        old_start = int(match.group(1))
        hunk_old_index = max(old_start - 1, 0)
        if hunk_old_index < old_index or hunk_old_index > len(old_lines):
            raise ValueError("invalid unified diff hunk position")
        output.extend(old_lines[old_index:hunk_old_index])
        old_index = hunk_old_index
        i += 1
        previous_kind = ""
        while i < len(patch_lines) and not _HUNK_RE.match(patch_lines[i]):
            line = patch_lines[i]
            if line == r"\ No newline at end of file":
                if previous_kind in {"addition", "context"} and output:
                    output[-1] = (output[-1][0], False)
                i += 1
                continue
            if line.startswith("diff --git "):
                break
            if line.startswith(" "):
                if old_index >= len(old_lines) or old_lines[old_index][0] != line[1:]:
                    raise ValueError("unified diff context does not match baseline")
                output.append((line[1:], True))
                old_index += 1
                previous_kind = "context"
            elif line.startswith("-"):
                if old_index >= len(old_lines) or old_lines[old_index][0] != line[1:]:
                    raise ValueError("unified diff removal does not match baseline")
                old_index += 1
                previous_kind = "removal"
            elif line.startswith("+"):
                output.append((line[1:], True))
                previous_kind = "addition"
            i += 1
    output.extend(old_lines[old_index:])
    return "".join(f"{line}{'\n' if has_newline else ''}" for line, has_newline in output)


def _new_lines_from_patch(patch_lines: list[str]) -> list[str]:
    lines: list[str] = []
    in_hunk = False
    for line in patch_lines:
        if _HUNK_RE.match(line):
            in_hunk = True
            continue
        if in_hunk and line.startswith("+"):
            lines.append(line[1:])
        elif in_hunk and line.startswith(" "):
            lines.append(line[1:])
    return lines


def _new_content_from_patch(patch_lines: list[str]) -> str:
    records: list[tuple[str, bool]] = []
    in_hunk = False
    previous_kind = ""
    for line in patch_lines:
        if _HUNK_RE.match(line):
            in_hunk = True
            previous_kind = ""
            continue
        if not in_hunk:
            continue
        if line == r"\ No newline at end of file":
            if previous_kind in {"addition", "context"} and records:
                records[-1] = (records[-1][0], False)
            continue
        if line.startswith("+"):
            records.append((line[1:], True))
            previous_kind = "addition"
        elif line.startswith(" "):
            records.append((line[1:], True))
            previous_kind = "context"
        elif line.startswith("-"):
            previous_kind = "removal"
    return "".join(
        f"{line}{'\n' if has_newline else ''}" for line, has_newline in records
    )


def _normalize_repo_path(raw_path: str) -> str:
    return normalize_repo_path_candidate(raw_path, strip_diff_prefix=False)


def _normalize_diff_path(raw_path: str) -> str:
    return normalize_repo_path_candidate(raw_path, strip_diff_prefix=True)


def _literal_needles(
    description: str,
    *,
    excluded_spans: list[tuple[int, int]] | None = None,
) -> list[str]:
    excluded = set(excluded_spans or [])
    values = [
        match.group("value")
        for match in re.finditer(
            r"(?P<quote>[\"'`])(?P<value>[^\"'`\n]+)(?P=quote)",
            description,
        )
        if match.group("value") and match.span() not in excluded
    ]
    class_fragment = re.search(
        r"\bclass\s+fragment\s+(?P<value>[^\s.][^\n.]*)\.?$",
        description,
        flags=re.IGNORECASE,
    )
    if class_fragment:
        value = class_fragment.group("value").strip("`'\" ")
        if value:
            values.append(value)
    # A literal criterion must encode the literal explicitly (quoted text or
    # the established ``class fragment`` form).  Treating an imperative such
    # as "Render OK." as the required source bytes confuses behavior wording
    # with a literal contract and creates an impossible reviewer retry.
    return values


_JS_IMPORT_MODULE_RE = re.compile(
    r"^\s*import(?:\s+type)?(?:[\s\S]*?\s+from\s+)?[\"']([^\"']+)[\"'];?\s*$",
    re.MULTILINE,
)
_PYTHON_RELATIVE_IMPORT_MODULE_RE = re.compile(
    r"^\s*from\s+(\.+[A-Za-z_][A-Za-z0-9_.]*)\s+import\s+",
    re.MULTILINE,
)


def _import_is_preserved(content: str, import_name: str) -> bool:
    active_js = _strip_js_comments_and_templates(content)
    modules = {
        *(match.group(1) for match in _JS_IMPORT_MODULE_RE.finditer(active_js)),
        *_active_python_relative_imports(content),
    }
    return import_name in modules


def _active_python_relative_imports(content: str) -> set[str]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return set()
    return {
        f"{'.' * node.level}{node.module or ''}"
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level > 0
    }


def _strip_js_comments_and_templates(content: str) -> str:
    chars = list(content)
    index = 0
    state = "code"
    quote = ""
    while index < len(chars):
        char = chars[index]
        next_char = chars[index + 1] if index + 1 < len(chars) else ""
        if state == "code":
            if char in {"'", '"'}:
                state = "string"
                quote = char
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
        elif state == "string":
            if char == "\\":
                index += 1
            elif char == quote:
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
    return "".join(chars)


def _export_is_preserved(content: str, export_name: str) -> bool:
    return export_name in _active_export_names(content)


def _active_export_names(content: str) -> set[str]:
    """Parse public export names while respecting named-export alias direction."""

    active = _mask_js_comments_and_strings(content)
    names: set[str] = set()
    for match in re.finditer(
        r"\bexport\s+(?:(?P<default>default)\s+)?"
        r"(?:(?:declare|abstract|async)\s+)*"
        r"(?:function|class|const|let|var|type|interface|enum|namespace|module)\s+"
        r"(?P<name>[A-Za-z_$][\w$]*)",
        active,
    ):
        names.add("default" if match.group("default") else match.group("name"))
    if re.search(r"\bexport\s+default\b", active):
        names.add("default")
    for match in re.finditer(
        r"\bexport\s+(?:type\s+)?\{(?P<body>[^}]*)\}",
        active,
        flags=re.DOTALL,
    ):
        for raw_item in match.group("body").split(","):
            item = re.sub(r"^\s*type\s+", "", raw_item).strip()
            specifier = re.fullmatch(
                r"(?P<local>[A-Za-z_$][\w$]*)"
                r"(?:\s+as\s+(?P<exported>[A-Za-z_$][\w$]*))?",
                item,
            )
            if specifier:
                names.add(specifier.group("exported") or specifier.group("local"))
    names.update(
        re.findall(
            r"\bexport\s*\*\s*as\s*([A-Za-z_$][\w$]*)\s+from\b",
            active,
        )
    )
    names.update(
        re.findall(
            r"\b(?:module\.)?exports\.([A-Za-z_$][\w$]*)\s*=",
            active,
        )
    )
    if re.search(r"\bmodule\.exports\s*=", active):
        names.add("module.exports")
    return names


def _mask_js_comments_and_strings(content: str) -> str:
    pattern = re.compile(
        r"(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|"
        r"`(?:\\.|[^`\\])*`|//[^\n]*|/\*[\s\S]*?\*/)",
    )

    def mask(match: re.Match[str]) -> str:
        value = match.group(0)
        return "".join("\n" if char == "\n" else " " for char in value)

    return pattern.sub(mask, content)


def _reviewer_model_alias() -> str:
    return os.getenv("SOURCE_PROXY_REVIEWER_MODEL_ALIAS", "").strip()


def _call_reviewer_llm(prompt: str, *, model_alias: str) -> str:
    central_gate_check("model_call", run_id="reviewer_llm", model_alias=model_alias)
    completion = get_router().completion(
        model=model_alias,
        messages=[{"role": "system", "content": prompt}],
        stream=False,
        temperature=0,
        timeout=float(os.getenv("SOURCE_PROXY_REVIEWER_TIMEOUT_SECONDS", "10")),
    )
    payload = completion.model_dump() if hasattr(completion, "model_dump") else dict(completion)
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        return content if isinstance(content, str) else ""
    text = first.get("text")
    return text if isinstance(text, str) else ""


def _reviewer_prompt(plan: ArchitectPlan, diff: str) -> str:
    directives = plan.coder_packet.style_directives
    criteria = [
        criterion.description
        for criterion in plan.coder_packet.acceptance_criteria
        if criterion.kind == "behavioral"
    ]
    return "\n".join(
        [
            "You are the Source Reviewer. Review only the unified diff against the listed directives.",
            "Return one JSON object only.",
            'Schema: {"passed": boolean, "findings": [{"id": string, "details": string, "path": string}]}',
            'Use id "style_directive_violation" for style directive violations.',
            "Report only clear violations of the listed style_directives or acceptance_criteria.",
            "Do not suggest general improvements. Do not block for preferences not listed here.",
            "",
            f"Target: {plan.coder_packet.target_file.path}",
            "Style directives:",
            *[f"- {directive}" for directive in directives],
            "Acceptance criteria:",
            *[f"- {criterion}" for criterion in criteria],
            "",
            "Unified diff:",
            diff[:120_000],
        ]
    )


def _parse_json_object(raw: str) -> dict[str, Any]:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ReviewerLLMError("Reviewer response did not contain a JSON object.")
    parsed = json.loads(raw[start : end + 1])
    if not isinstance(parsed, dict):
        raise ReviewerLLMError("Reviewer response JSON must be an object.")
    return parsed


def _review_report_from_llm_payload(
    payload: dict[str, Any],
    *,
    default_path: str,
) -> ReviewReport:
    raw_findings = payload.get("findings")
    findings: list[ReviewFinding] = []
    if isinstance(raw_findings, list):
        for item in raw_findings[:10]:
            if not isinstance(item, dict):
                continue
            finding_id = str(item.get("id") or "reviewer_finding").strip()
            details = str(item.get("details") or "").strip()
            path = str(item.get("path") or default_path).strip().replace("\\", "/")
            if not finding_id or not details:
                continue
            findings.append(
                ReviewFinding(
                    id=finding_id[:80],
                    details=details[:500],
                    path=path[:240] or default_path,
                )
            )
    passed = bool(payload.get("passed")) and not findings
    return ReviewReport(passed=passed, findings=findings)
