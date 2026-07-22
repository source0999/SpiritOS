from __future__ import annotations

import re
import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Callable

from source_proxy.planning.plan import ArchitectPlan, ContextSlice
from source_proxy.routing.litellm_router import available_model_aliases, get_router
from source_proxy.approval.external_gate import central_gate_check


@dataclass(frozen=True)
class ReviewFinding:
    id: str
    details: str
    path: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewReport:
    passed: bool
    findings: list[ReviewFinding]

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "findings": [finding.to_dict() for finding in self.findings],
        }


class ReviewerLLMError(ValueError):
    pass


def review_diff_deterministically(plan: ArchitectPlan, diff: str) -> ReviewReport:
    target_path = plan.coder_packet.target_file.path
    new_content = _materialize_target_content(plan, diff)
    base_content = _target_slice(plan.coder_packet.context_slices, target_path)
    findings: list[ReviewFinding] = []
    constraints = plan.coder_packet.constraints
    added, removed = _changed_line_counts(diff)

    for required in constraints.must_contain:
        if required not in new_content:
            findings.append(
                ReviewFinding("missing_must_contain", required, target_path)
            )

    for forbidden in constraints.must_not_contain:
        if forbidden in new_content:
            findings.append(
                ReviewFinding("forbidden_must_not_contain", forbidden, target_path)
            )

    if constraints.max_added_lines is not None and added > constraints.max_added_lines:
        findings.append(
            ReviewFinding(
                "max_added_lines_exceeded",
                f"{added}>{constraints.max_added_lines}",
                target_path,
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

    for import_name in constraints.preserve_imports:
        if not _import_is_preserved(new_content, import_name) and _import_changed_by_diff(
            diff,
            import_name,
            base_content,
        ):
            findings.append(ReviewFinding("imports_violated", import_name, target_path))

    for export_name in constraints.preserve_exports:
        if not _export_is_preserved(new_content, export_name):
            findings.append(ReviewFinding("exports_violated", export_name, target_path))

    for criterion in plan.coder_packet.acceptance_criteria:
        if criterion.kind != "literal":
            continue
        literal_needles = _literal_needles(criterion.description)
        if literal_needles and not any(
            required in new_content for required in literal_needles
        ):
            findings.append(
                ReviewFinding("literal_acceptance_missing", criterion.description, target_path)
            )

    return ReviewReport(passed=not findings, findings=findings)


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
    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return added, removed


def _materialize_target_content(plan: ArchitectPlan, diff: str) -> str:
    target_path = plan.coder_packet.target_file.path
    base_content = _target_slice(plan.coder_packet.context_slices, target_path)
    old_lines = base_content.splitlines()
    if base_content.endswith("\n"):
        old_lines.append("")
    file_patch = _patch_for_path(diff, target_path)
    if not file_patch:
        return base_content
    try:
        return _apply_file_patch(old_lines, file_patch)
    except ValueError:
        # If the patch is malformed, leave the failing apply check to the diff verifier.
        return "\n".join(_new_lines_from_patch(file_patch))


def _target_slice(slices: list[ContextSlice], target_path: str) -> str:
    for context_slice in slices:
        if context_slice.path == target_path and context_slice.kind == "target":
            return context_slice.content
    return ""


def _patch_for_path(diff: str, target_path: str) -> list[str]:
    lines = diff.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    current: list[str] = []
    current_path = ""
    found: list[str] = []

    def finish_current() -> None:
        nonlocal found
        if current_path == target_path:
            found = current

    for line in lines:
        if line.startswith("diff --git "):
            finish_current()
            current = [line]
            paths = _diff_git_paths(line)
            current_path = _normalize_diff_path(paths[1]) if len(paths) >= 2 else ""
            continue
        if line.startswith("--- "):
            if current and current[0].startswith("--- "):
                finish_current()
                current_path = ""
                current = []
            if not current:
                current = [line]
                current_path = _normalize_diff_path(line[4:])
                continue
        if current:
            current.append(line)
            if line.startswith("+++ "):
                next_path = _normalize_diff_path(line[4:].strip())
                if next_path:
                    current_path = next_path
    finish_current()
    return found


def _diff_git_paths(line: str) -> list[str]:
    body = line.removeprefix("diff --git ").strip()
    matches = re.findall(r'"((?:\\.|[^"])*)"', body)
    if len(matches) >= 2:
        return [match.replace(r"\"", '"') for match in matches[:2]]
    return body.split()


_HUNK_RE = re.compile(r"^@@\s+-(\d+)(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@")


def _apply_file_patch(old_lines: list[str], patch_lines: list[str]) -> str:
    output: list[str] = []
    old_index = 0
    i = 0
    while i < len(patch_lines):
        match = _HUNK_RE.match(patch_lines[i])
        if not match:
            i += 1
            continue
        old_start = int(match.group(1))
        hunk_old_index = max(old_start - 1, 0)
        output.extend(old_lines[old_index:hunk_old_index])
        old_index = hunk_old_index
        i += 1
        while i < len(patch_lines) and not _HUNK_RE.match(patch_lines[i]):
            line = patch_lines[i]
            if line == r"\ No newline at end of file":
                i += 1
                continue
            if line.startswith("diff --git "):
                break
            if line.startswith(" "):
                output.append(line[1:])
                old_index += 1
            elif line.startswith("-") and not line.startswith("---"):
                old_index += 1
            elif line.startswith("+") and not line.startswith("+++"):
                output.append(line[1:])
            i += 1
    output.extend(old_lines[old_index:])
    text = "\n".join(output)
    if text.endswith("\n"):
        return text
    return text + ("\n" if output and output[-1] == "" else "")


def _new_lines_from_patch(patch_lines: list[str]) -> list[str]:
    lines: list[str] = []
    for line in patch_lines:
        if line.startswith("+") and not line.startswith("+++"):
            lines.append(line[1:])
        elif line.startswith(" ") and not line.startswith("diff --git "):
            lines.append(line[1:])
    return lines


def _normalize_diff_path(raw_path: str) -> str:
    path = raw_path.strip().strip('"').replace("\\", "/")
    if "\t" in path:
        path = path.split("\t", 1)[0].strip()
    path = re.sub(r"\s+\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\s+[+-]\d{4})?)?$", "", path).strip()
    if path in {"", "/dev/null"}:
        return ""
    if path.startswith("a/") or path.startswith("b/"):
        path = path[2:]
    return path


def _literal_needles(description: str) -> list[str]:
    values = [
        match.group("value")
        for match in re.finditer(
            r"(?P<quote>[\"'])(?P<value>[^\"'\n]+)(?P=quote)",
            description,
        )
        if match.group("value")
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


def _import_is_preserved(content: str, import_name: str) -> bool:
    import_lines = "\n".join(
        line for line in content.splitlines() if re.match(r"\s*import\b", line)
    )
    return import_name in import_lines


def _import_changed_by_diff(diff: str, import_name: str, base_content: str) -> bool:
    if import_name not in base_content:
        return True
    for raw_line in diff.splitlines():
        if raw_line.startswith(("+++", "---")):
            continue
        if not raw_line.startswith(("+", "-")):
            continue
        line = raw_line[1:]
        if re.match(r"\s*import\b", line) and import_name in line:
            return True
    return False


def _export_is_preserved(content: str, export_name: str) -> bool:
    if export_name == "default":
        return bool(re.search(r"\bexport\s+default\b", content))
    escaped = re.escape(export_name)
    return bool(
        re.search(rf"\bexport\s+(?:async\s+)?(?:function|class|const|let|var|type|interface)\s+{escaped}\b", content)
        or re.search(rf"\bexport\s*\{{[^}}]*\b{escaped}\b[^}}]*\}}", content, flags=re.DOTALL)
    )


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
