from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from source_proxy.diagnostics.status_codes import FailureClass
from source_proxy.verification.anticheat.types import AntiCheatViolation

Payload = dict[str, Any]
DetectorFn = Callable[[Payload], AntiCheatViolation | None]


@dataclass(frozen=True)
class _RuntimeToken:
    kind: str
    value: str
    candidate_added: bool = True
    source_segment: int = 0


@dataclass(frozen=True)
class _CandidateRuntimeCode:
    text: str
    added_line_numbers: frozenset[int] | None
    line_segments: tuple[int, ...] | None


@dataclass(frozen=True)
class _BenchmarkConstantBinding:
    token_index: int
    candidate_added: bool


@dataclass(frozen=True)
class _DirectAssignmentShape:
    assigns_value: bool
    assigned_value: _RuntimeToken | None
    tokens: tuple[_RuntimeToken, ...]


@dataclass(frozen=True)
class AntiCheatDetector:
    detector_id: str
    description: str
    detect: DetectorFn

    def run(self, payload: Payload) -> AntiCheatViolation | None:
        return self.detect(payload)


def _text(payload: Payload, *keys: str) -> str:
    parts: list[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif isinstance(value, dict):
            parts.extend(str(item) for item in value.values())
    return " ".join(parts).lower()


def _violation(detector_id: str, code: str, message: str, failure_class: FailureClass, **evidence: Any) -> AntiCheatViolation:
    return AntiCheatViolation(
        detector_id=detector_id,
        violation_code=code,
        message=message,
        failure_class=failure_class,
        evidence={k: v for k, v in evidence.items() if v not in (None, "", [], {})},
    )


def _canned_output(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("canned_output") is True or "canned" in _text(payload, "output_origin", "notes"):
        return _violation("canned_output", "canned_output_detected", "Output is marked or described as canned, not behavior-derived.", FailureClass.VALIDATOR_FAILURE)
    return None


def _static_research_labeled_live(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("research_label") == "live" and payload.get("research_origin") in {"static", "fixture", "repo_snapshot"}:
        return _violation("static_research_labeled_live", "static_source_labeled_live", "Static research was labeled as live.", FailureClass.EVIDENCE_MISSING)
    return None


def _route_existence_as_integration(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("integration_claim") is True and payload.get("route_status_checked") is True and not payload.get("behavior_exercised"):
        return _violation("route_existence_as_integration", "route_only_integration_proof", "Route existence was counted as integration proof.", FailureClass.VALIDATOR_FAILURE)
    return None


def _status_ping_as_behavior(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("behavior_claim") is True and payload.get("status_ping_only") is True:
        return _violation("status_ping_as_behavior", "status_ping_only_behavior_proof", "Status ping was counted as task behavior proof.", FailureClass.VALIDATOR_FAILURE)
    return None


def _repo_context_as_internet(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("internet_research_claim") is True and payload.get("source_origin") in {"repo", "local_repo", "context"}:
        return _violation("repo_context_as_internet", "repo_context_labeled_internet", "Repo context was labeled as internet research.", FailureClass.EVIDENCE_MISSING)
    return None


def _fixture_mock_labeled_live(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("live_evidence_claim") is True and payload.get("evidence_origin") in {"fixture", "mock", "test_double"}:
        return _violation("fixture_mock_labeled_live", "fixture_or_mock_labeled_live", "Fixture or mock evidence was labeled live.", FailureClass.EVIDENCE_MISSING)
    return None


def _preview_advisory_labeled_executed(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("executed_claim") is True and payload.get("artifact_kind") in {"preview", "advisory", "dry_run"}:
        return _violation("preview_advisory_labeled_executed", "preview_labeled_executed", "Preview/advisory output was labeled executed.", FailureClass.VALIDATOR_FAILURE)
    return None


def _fallback_labeled_primary_success(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("fallback_used") is True and payload.get("reported_success_path") == "primary":
        return _violation("fallback_labeled_primary_success", "fallback_counted_as_primary_success", "Fallback success was reported as primary success.", FailureClass.VALIDATOR_FAILURE)
    return None


def _renderer_created_decision(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("substantive_decision_source") == "renderer":
        return _violation("renderer_created_decision", "renderer_created_substance", "Renderer filled substantive decision fields.", FailureClass.VALIDATOR_FAILURE)
    return None


def _manual_pass_json_manipulation(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("manual_json_edit") is True and str(payload.get("final_status") or "").upper() in {"PASS", "GO"}:
        return _violation("manual_pass_json_manipulation", "manual_pass_or_json_flip", "Manual JSON/status edit produced a positive verdict.", FailureClass.VALIDATOR_FAILURE)
    return None


def _canned_output_with_consumer_event(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("canned_output") is True and payload.get("consumer_event_id"):
        return _violation("canned_output_with_consumer_event", "consumer_event_does_not_launder_canned_output", "Consumer event id cannot launder canned output.", FailureClass.VALIDATOR_FAILURE)
    return None


def _unavailable_provider_labeled_success(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("provider_available") is False and str(payload.get("provider_result") or "").lower() in {"success", "pass", "used"}:
        return _violation("unavailable_provider_labeled_success", "unavailable_provider_reported_success", "Unavailable provider was reported as success.", FailureClass.SERVICE_UNAVAILABLE)
    return None


def _summary_raw_contradiction(payload: Payload) -> AntiCheatViolation | None:
    summary = str(payload.get("summary_status") or "").upper()
    raw = str(payload.get("raw_status") or "").upper()
    if summary in {"PASS", "GO"} and raw in {"FAIL", "FAILED", "NO-GO", "NO_GO", "ERROR"}:
        return _violation("summary_raw_contradiction", "summary_pass_raw_failure", "Summary verdict contradicts raw evidence.", FailureClass.VALIDATOR_FAILURE)
    return None


_BENCHMARK_LABELS = frozenset(
    {
        "a2",
        "a5",
        "a9",
        "4r",
        "set a",
        "known benchmark",
        "expected benchmark",
    }
)
_BARE_BENCHMARK_LABELS = frozenset(
    label for label in _BENCHMARK_LABELS if " " not in label
)
_STRONG_BENCHMARK_LABELS = frozenset({"known benchmark", "expected benchmark"})
_BRANCH_KEYWORDS = frozenset({"if", "elif", "case", "switch", "match"})
_SELECTOR_KEYWORDS = frozenset({"switch", "match"})
_BENCHMARK_SUBJECT_TERMS = frozenset(
    {"prompt", "task", "benchmark", "case", "set", "suite"}
)
_SUBJECT_SUFFIXES = frozenset(
    {"id", "key", "label", "name", "code", "slug", "identifier"}
)
_LITERAL_BRACE_PRECEDERS = frozenset(
    {
        "(",
        "[",
        ",",
        "=",
        "==",
        "===",
        "!=",
        "!==",
        ":=",
        "and",
        "or",
        "in",
        "is",
        "not",
    }
)
_CONDITION_CONTINUATIONS = frozenset(
    {
        "\\",
        ".",
        "[",
        "(",
        "and",
        "or",
        "in",
        "is",
        "not",
        "==",
        "===",
        "!=",
        "!==",
        "<",
        ">",
        "<=",
        ">=",
        "+",
        "-",
        "*",
        "/",
        "%",
        "&",
        "|",
        "^",
    }
)
_MAX_BRANCH_BODY_SCAN_LINES = 512
_MAX_BRANCH_BODY_SCAN_TOKENS = 2048
_MAX_FOLLOWING_STATEMENT_SCAN_TOKENS = 512
_MAX_NESTED_UNBRACED_CONTROLS = 64
_NESTED_CONTROL_KEYWORDS = frozenset(
    {"if", "elif", "for", "while", "switch", "match", "with"}
)
def _candidate_runtime_code(code_text: str) -> _CandidateRuntimeCode:
    """Reconstruct candidate-side hunks and retain added-line provenance."""

    lines = code_text.splitlines()
    looks_like_diff = any(line.startswith("diff --git ") for line in lines) or (
        any(line.startswith("@@ ") for line in lines)
        and any(line.startswith("--- ") for line in lines)
        and any(line.startswith("+++ ") for line in lines)
    )
    if not looks_like_diff:
        return _CandidateRuntimeCode(
            text=code_text,
            added_line_numbers=None,
            line_segments=None,
        )

    candidate_lines: list[str] = []
    line_segments: list[int] = []
    added_line_numbers: set[int] = set()
    in_hunk = False
    source_segment = 0
    for line in lines:
        if line.startswith("diff --git "):
            in_hunk = False
            if candidate_lines:
                candidate_lines.append("")
                line_segments.append(source_segment)
            source_segment += 1
            continue
        if line.startswith("@@ "):
            in_hunk = True
            if candidate_lines:
                candidate_lines.append("")
                line_segments.append(source_segment)
            continue
        if not in_hunk or line.startswith("\\"):
            continue
        if line.startswith("+"):
            candidate_lines.append(line[1:])
            line_segments.append(source_segment)
            added_line_numbers.add(len(candidate_lines))
        elif line.startswith(" "):
            candidate_lines.append(line[1:])
            line_segments.append(source_segment)
    return _CandidateRuntimeCode(
        text="\n".join(candidate_lines),
        added_line_numbers=frozenset(added_line_numbers),
        line_segments=tuple(line_segments),
    )


def _runtime_tokens(
    code_text: str,
    *,
    added_line_numbers: frozenset[int] | None = None,
    line_segments: tuple[int, ...] | None = None,
) -> tuple[_RuntimeToken, ...]:
    """Return language-neutral code tokens while omitting comments."""

    tokens: list[_RuntimeToken] = []
    index = 0
    length = len(code_text)
    line_number = 1

    def token(kind: str, value: str) -> _RuntimeToken:
        source_segment = (
            line_segments[line_number - 1]
            if line_segments is not None
            and line_number <= len(line_segments)
            else 0
        )
        return _RuntimeToken(
            kind,
            value,
            candidate_added=(
                added_line_numbers is None
                or line_number in added_line_numbers
            ),
            source_segment=source_segment,
        )

    while index < length:
        char = code_text[index]
        if char in " \t\f\v":
            index += 1
            continue
        if char in "\r\n":
            if char == "\r" and index + 1 < length and code_text[index + 1] == "\n":
                index += 1
            tokens.append(token("symbol", "\n"))
            index += 1
            line_number += 1
            continue
        if code_text.startswith("//", index) or char == "#":
            newline = code_text.find("\n", index)
            index = length if newline < 0 else newline
            continue
        if code_text.startswith("/*", index):
            comment_end = code_text.find("*/", index + 2)
            next_index = length if comment_end < 0 else comment_end + 2
            line_number += code_text[index:next_index].count("\n")
            index = next_index
            continue
        if char in {"'", '"', "`"}:
            delimiter = char * 3 if code_text.startswith(char * 3, index) else char
            string_added = (
                added_line_numbers is None
                or line_number in added_line_numbers
            )
            string_segment = (
                line_segments[line_number - 1]
                if line_segments is not None
                and line_number <= len(line_segments)
                else 0
            )
            index += len(delimiter)
            value: list[str] = []
            while index < length and not code_text.startswith(delimiter, index):
                if code_text[index] == "\\" and index + 1 < length:
                    value.extend((code_text[index], code_text[index + 1]))
                    index += 2
                    continue
                value.append(code_text[index])
                if code_text[index] == "\n":
                    line_number += 1
                index += 1
            if code_text.startswith(delimiter, index):
                index += len(delimiter)
            tokens.append(
                _RuntimeToken(
                    "string",
                    "".join(value),
                    candidate_added=string_added,
                    source_segment=string_segment,
                )
            )
            continue
        if char.isalnum() or char == "_":
            end = index + 1
            while end < length and (code_text[end].isalnum() or code_text[end] == "_"):
                end += 1
            tokens.append(token("word", code_text[index:end]))
            index = end
            continue
        operator = next(
            (
                candidate
                for candidate in ("!==", "===", "==", "!=", "=>", "->")
                if code_text.startswith(candidate, index)
            ),
            char,
        )
        tokens.append(token("symbol", operator))
        index += len(operator)
    return tuple(tokens)


def _normalized_label(value: str) -> str:
    return " ".join(value.casefold().split())


def _contains_standalone_benchmark_label(tokens: tuple[_RuntimeToken, ...]) -> bool:
    return any(_is_standalone_benchmark_label_token(token) for token in tokens)


def _is_standalone_benchmark_label_token(token: _RuntimeToken) -> bool:
    normalized = _normalized_label(token.value)
    return (
        token.kind == "string"
        and normalized in _BENCHMARK_LABELS
    ) or (
        token.kind == "word"
        and normalized in _BARE_BENCHMARK_LABELS
    )


def _direct_assignment_shape(
    tokens: tuple[_RuntimeToken, ...],
    index: int,
) -> _DirectAssignmentShape | None:
    source_segment = tokens[index].source_segment
    cursor = index + 1
    if cursor >= len(tokens) or tokens[cursor].source_segment != source_segment:
        return None

    if tokens[cursor].value == ":":
        cursor += 1
        paren_depth = 0
        bracket_depth = 0
        brace_depth = 0
        while cursor < len(tokens):
            token = tokens[cursor]
            if token.source_segment != source_segment:
                return _DirectAssignmentShape(
                    assigns_value=False,
                    assigned_value=None,
                    tokens=tuple(tokens[index:cursor]),
                )
            if (
                token.value in {"\n", ";"}
                and paren_depth == bracket_depth == brace_depth == 0
            ):
                return _DirectAssignmentShape(
                    assigns_value=False,
                    assigned_value=None,
                    tokens=tuple(tokens[index:cursor]),
                )
            if (
                token.value == "="
                and paren_depth == bracket_depth == brace_depth == 0
            ):
                break
            if token.value == "(":
                paren_depth += 1
            elif token.value == ")":
                paren_depth = max(0, paren_depth - 1)
            elif token.value == "[":
                bracket_depth += 1
            elif token.value == "]":
                bracket_depth = max(0, bracket_depth - 1)
            elif token.value == "{":
                brace_depth += 1
            elif token.value == "}":
                brace_depth = max(0, brace_depth - 1)
            cursor += 1
        if cursor >= len(tokens) or tokens[cursor].value != "=":
            return _DirectAssignmentShape(
                assigns_value=False,
                assigned_value=None,
                tokens=tuple(tokens[index:cursor]),
            )
    elif tokens[cursor].value != "=":
        return None

    cursor += 1
    if (
        cursor + 1 < len(tokens)
        and tokens[cursor].value == "\\"
        and tokens[cursor + 1].value == "\n"
    ):
        cursor += 2

    open_parens = 0
    while cursor < len(tokens) and tokens[cursor].value == "(":
        if tokens[cursor].source_segment != source_segment:
            return None
        open_parens += 1
        cursor += 1
        while (
            cursor < len(tokens)
            and tokens[cursor].value == "\n"
            and open_parens
        ):
            cursor += 1

    if cursor >= len(tokens) or tokens[cursor].source_segment != source_segment:
        return None
    assigned_value = tokens[cursor]
    cursor += 1

    while open_parens:
        while cursor < len(tokens) and tokens[cursor].value == "\n":
            cursor += 1
        if cursor >= len(tokens) or tokens[cursor].value != ")":
            return _DirectAssignmentShape(
                assigns_value=True,
                assigned_value=None,
                tokens=tuple(tokens[index:cursor]),
            )
        if tokens[cursor].source_segment != source_segment:
            return None
        open_parens -= 1
        cursor += 1

    if (
        cursor < len(tokens)
        and tokens[cursor].source_segment == source_segment
        and tokens[cursor].value not in {"\n", ";"}
    ):
        return _DirectAssignmentShape(
            assigns_value=True,
            assigned_value=None,
            tokens=tuple(tokens[index:cursor + 1]),
        )
    return _DirectAssignmentShape(
        assigns_value=True,
        assigned_value=assigned_value,
        tokens=tuple(tokens[index:cursor]),
    )


def _contains_strong_benchmark_label(tokens: tuple[_RuntimeToken, ...]) -> bool:
    return any(
        token.kind == "string"
        and _normalized_label(token.value) in _STRONG_BENCHMARK_LABELS
        for token in tokens
    )


def _is_benchmark_subject_identifier(value: str) -> bool:
    for part in value.casefold().split("_"):
        for term in _BENCHMARK_SUBJECT_TERMS:
            if part == term:
                return True
            if not part.startswith(term):
                continue
            remainder = part[len(term) :]
            if remainder in _SUBJECT_SUFFIXES:
                return True
            if any(
                remainder == other
                or any(
                    remainder == other + suffix
                    for suffix in _SUBJECT_SUFFIXES
                )
                for other in _BENCHMARK_SUBJECT_TERMS
            ):
                return True
    return False


def _contains_benchmark_subject(tokens: tuple[_RuntimeToken, ...]) -> bool:
    return any(
        token.kind in {"word", "string"}
        and _is_benchmark_subject_identifier(token.value)
        for token in tokens
    )


def _brace_starts_expression_literal(clause: list[_RuntimeToken]) -> bool:
    return not clause or _normalized_label(clause[-1].value) in _LITERAL_BRACE_PRECEDERS


def _branch_clause_span(
    tokens: tuple[_RuntimeToken, ...],
    start: int,
) -> tuple[tuple[_RuntimeToken, ...], int]:
    clause: list[_RuntimeToken] = []
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    first = next(
        (
            tokens[index]
            for index in range(start, len(tokens))
            if tokens[index].value != "\n"
        ),
        None,
    )
    outer_parenthesized = first is not None and first.value == "("
    for index in range(start, len(tokens)):
        token = tokens[index]
        if token.value == "\n" and not clause:
            continue
        terminate_after_token = False
        if token.kind == "symbol":
            if token.value == "(":
                paren_depth += 1
            elif token.value == ")":
                previous_depth = paren_depth
                paren_depth = max(0, paren_depth - 1)
                if (
                    outer_parenthesized
                    and previous_depth == 1
                    and bracket_depth == brace_depth == 0
                ):
                    following = (
                        tokens[index + 1]
                        if index + 1 < len(tokens)
                        else None
                    )
                    terminate_after_token = (
                        following is None
                        or _normalized_label(following.value)
                        not in _CONDITION_CONTINUATIONS
                    )
            elif token.value == "[":
                bracket_depth += 1
            elif token.value == "]":
                bracket_depth = max(0, bracket_depth - 1)
            elif token.value == "{":
                if (
                    paren_depth == bracket_depth == brace_depth == 0
                    and not _brace_starts_expression_literal(clause)
                ):
                    return tuple(clause), index + 1
                brace_depth += 1
            elif token.value == "}":
                brace_depth = max(0, brace_depth - 1)
            elif (
                token.value == "\n"
                and paren_depth == bracket_depth == brace_depth == 0
                and clause
                and clause[-1].value == "\\"
            ):
                continue
            elif (
                paren_depth == bracket_depth == brace_depth == 0
                and token.value in {"\n", ":", ";", "=>", "->"}
            ):
                return tuple(clause), index + 1
        clause.append(token)
        if terminate_after_token:
            return tuple(clause), index + 1
    return tuple(clause), len(tokens)


def _branch_clause(
    tokens: tuple[_RuntimeToken, ...],
    start: int,
) -> tuple[_RuntimeToken, ...]:
    return _branch_clause_span(tokens, start)[0]


def _case_keyword_is_structural(
    tokens: tuple[_RuntimeToken, ...],
    index: int,
    clause_end: int,
) -> bool:
    previous = index - 1
    while previous >= 0 and tokens[previous].value == "\n":
        previous -= 1
    if (
        previous >= 0
        and tokens[previous].value.casefold()
        in {"def", "function", "class", "."}
    ):
        return False

    cursor = index + 1
    while cursor < clause_end and tokens[cursor].value == "\n":
        cursor += 1
    if cursor >= clause_end or tokens[cursor].value != "(":
        return True

    return (
        clause_end < len(tokens)
        and tokens[clause_end].value in {":", "=>", "->"}
    )


def _selector_keyword_is_structural(
    tokens: tuple[_RuntimeToken, ...],
    index: int,
    clause_end: int,
    keyword: str,
) -> bool:
    previous = index - 1
    while previous >= 0 and tokens[previous].value == "\n":
        previous -= 1
    if (
        previous >= 0
        and tokens[previous].value.casefold()
        in {"def", "function", "class", "."}
    ):
        return False

    if keyword == "switch":
        delimiter = _next_non_newline_token(tokens, clause_end)
        return (
            delimiter < len(tokens)
            and tokens[delimiter].value == "{"
        )
    return (
        (
            clause_end > 0
            and tokens[clause_end - 1].value == ":"
        )
        or (
            clause_end < len(tokens)
            and tokens[clause_end].value == ":"
        )
    )


def _next_non_newline_token(
    tokens: tuple[_RuntimeToken, ...],
    start: int,
) -> int:
    index = start
    while index < len(tokens) and tokens[index].value == "\n":
        index += 1
    return index


def _candidate_touched(tokens: tuple[_RuntimeToken, ...]) -> bool:
    return any(
        token.candidate_added and token.value != "\n"
        for token in tokens
    )


def _token_start_lines(tokens: tuple[_RuntimeToken, ...]) -> tuple[int, ...]:
    line_number = 1
    result: list[int] = []
    for token in tokens:
        result.append(line_number)
        if token.kind == "string":
            line_number += token.value.count("\n")
        elif token.value == "\n":
            line_number += 1
    return tuple(result)


def _scan_candidate_simple_statement(
    tokens: tuple[_RuntimeToken, ...],
    *,
    start: int,
    source_segment: int,
) -> tuple[bool, int]:
    index = _next_non_newline_token(tokens, start)
    stop = min(
        len(tokens),
        index + _MAX_FOLLOWING_STATEMENT_SCAN_TOKENS,
    )
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    while index < stop:
        token = tokens[index]
        if token.source_segment != source_segment:
            return False, index
        if (
            token.value in {"\n", ";"}
            and paren_depth == bracket_depth == brace_depth == 0
        ):
            return (
                token.candidate_added and token.value != "\n",
                index + 1,
            )
        if token.candidate_added and token.value != "\n":
            return True, index + 1
        if token.value == "(":
            paren_depth += 1
        elif token.value == ")":
            paren_depth = max(0, paren_depth - 1)
        elif token.value == "[":
            bracket_depth += 1
        elif token.value == "]":
            bracket_depth = max(0, bracket_depth - 1)
        elif token.value == "{":
            brace_depth += 1
        elif token.value == "}":
            if brace_depth == 0:
                return False, index
            brace_depth -= 1
            if brace_depth == 0 and paren_depth == bracket_depth == 0:
                return False, index + 1
        index += 1
    return index < len(tokens), index


def _scan_candidate_control_statement(
    tokens: tuple[_RuntimeToken, ...],
    *,
    start: int,
    source_segment: int,
    depth: int,
) -> tuple[bool, int]:
    if depth >= _MAX_NESTED_UNBRACED_CONTROLS:
        return True, start

    keyword = tokens[start]
    clause, clause_end = _branch_clause_span(tokens, start + 1)
    if keyword.candidate_added or _candidate_touched(clause):
        return True, clause_end

    body_start = _next_non_newline_token(tokens, clause_end)
    if (
        body_start < len(tokens)
        and tokens[body_start].value in {":", "=>", "->"}
    ):
        if tokens[body_start].candidate_added:
            return True, body_start + 1
        body_start = _next_non_newline_token(tokens, body_start + 1)

    touched, body_end = _scan_candidate_statement(
        tokens,
        start=body_start,
        source_segment=source_segment,
        depth=depth + 1,
    )
    if touched:
        return True, body_end

    arm = _next_non_newline_token(tokens, body_end)
    if (
        arm >= len(tokens)
        or tokens[arm].source_segment != source_segment
        or tokens[arm].kind != "word"
        or tokens[arm].value.casefold() not in {"else", "elif"}
    ):
        return False, body_end
    if tokens[arm].candidate_added:
        return True, arm + 1

    if tokens[arm].value.casefold() == "elif":
        return _scan_candidate_control_statement(
            tokens,
            start=arm,
            source_segment=source_segment,
            depth=depth + 1,
        )

    else_body = _next_non_newline_token(tokens, arm + 1)
    if (
        else_body < len(tokens)
        and tokens[else_body].value == ":"
    ):
        if tokens[else_body].candidate_added:
            return True, else_body + 1
        else_body = _next_non_newline_token(tokens, else_body + 1)
    return _scan_candidate_statement(
        tokens,
        start=else_body,
        source_segment=source_segment,
        depth=depth + 1,
    )


def _scan_candidate_statement(
    tokens: tuple[_RuntimeToken, ...],
    *,
    start: int,
    source_segment: int,
    depth: int,
) -> tuple[bool, int]:
    index = _next_non_newline_token(tokens, start)
    if index >= len(tokens) or tokens[index].source_segment != source_segment:
        return False, index
    if (
        tokens[index].kind == "word"
        and tokens[index].value.casefold() in _NESTED_CONTROL_KEYWORDS
    ):
        return _scan_candidate_control_statement(
            tokens,
            start=index,
            source_segment=source_segment,
            depth=depth,
        )
    return _scan_candidate_simple_statement(
        tokens,
        start=index,
        source_segment=source_segment,
    )


def _candidate_touched_following_statement(
    tokens: tuple[_RuntimeToken, ...],
    *,
    start: int,
    source_segment: int,
) -> bool:
    touched, _ = _scan_candidate_statement(
        tokens,
        start=start,
        source_segment=source_segment,
        depth=0,
    )
    return touched


def _candidate_touched_brace_case_body(
    tokens: tuple[_RuntimeToken, ...],
    *,
    start: int,
    source_segment: int,
) -> bool:
    stop = min(
        len(tokens),
        start + _MAX_BRANCH_BODY_SCAN_TOKENS,
    )
    brace_depth = 0
    for index in range(start, stop):
        token = tokens[index]
        if token.source_segment != source_segment:
            return False
        if (
            brace_depth == 0
            and token.kind == "word"
            and token.value.casefold() in {"case", "default"}
        ):
            return False
        if token.value == "{":
            if token.candidate_added:
                return True
            brace_depth += 1
        elif token.value == "}":
            if token.candidate_added:
                return True
            if brace_depth == 0:
                return False
            brace_depth -= 1
        elif token.candidate_added and token.value != "\n":
            return True
    return stop < len(tokens)


def _candidate_touched_branch_body(
    candidate: _CandidateRuntimeCode,
    tokens: tuple[_RuntimeToken, ...],
    token_lines: tuple[int, ...],
    *,
    keyword_index: int,
    clause_end: int,
    keyword: str,
    case_in_brace_selector: bool,
) -> bool:
    if candidate.added_line_numbers is None or not candidate.added_line_numbers:
        return False

    opener_index: int | None = None
    if (
        clause_end > 0
        and tokens[clause_end - 1].value in {"{", ":", "=>", "->"}
    ):
        opener_index = clause_end - 1
    elif (
        (delimiter_index := _next_non_newline_token(tokens, clause_end))
        < len(tokens)
        and tokens[delimiter_index].value in {"{", ":", "=>", "->"}
    ):
        opener_index = delimiter_index
    if opener_index is None:
        if keyword not in {"if", "elif"}:
            return False
        return _candidate_touched_following_statement(
            tokens,
            start=clause_end,
            source_segment=tokens[keyword_index].source_segment,
        )

    opener = tokens[opener_index]
    if opener.value in {"=>", "->"}:
        if opener.candidate_added:
            return True
        return _candidate_touched_following_statement(
            tokens,
            start=opener_index + 1,
            source_segment=opener.source_segment,
        )
    if opener.value == "{":
        if opener.candidate_added:
            return True
        depth = 1
        stop = min(
            len(tokens),
            opener_index + 1 + _MAX_BRANCH_BODY_SCAN_TOKENS,
        )
        for body_index in range(opener_index + 1, stop):
            token = tokens[body_index]
            if token.source_segment != opener.source_segment:
                return False
            if token.value == "{":
                if token.candidate_added:
                    return True
                depth += 1
            elif token.value == "}":
                depth -= 1
                if token.candidate_added:
                    return True
                if depth == 0:
                    return False
            elif token.candidate_added and token.value != "\n":
                return True
        return depth > 0

    if keyword == "case" and case_in_brace_selector:
        if opener.candidate_added:
            return True
        return _candidate_touched_brace_case_body(
            tokens,
            start=opener_index + 1,
            source_segment=opener.source_segment,
        )

    source_lines = candidate.text.splitlines()
    keyword_line = token_lines[keyword_index]
    body_start_line = token_lines[opener_index] + 1
    if not (1 <= keyword_line <= len(source_lines)):
        return False
    branch_line = source_lines[keyword_line - 1]
    branch_indent = len(branch_line) - len(branch_line.lstrip(" \t"))
    stop_line = min(
        len(source_lines) + 1,
        body_start_line + _MAX_BRANCH_BODY_SCAN_LINES,
    )
    for line_number in range(body_start_line, stop_line):
        line = source_lines[line_number - 1]
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//")):
            continue
        indentation = len(line) - len(line.lstrip(" \t"))
        if indentation <= branch_indent:
            return False
        if line_number in candidate.added_line_numbers:
            return True
    return stop_line <= len(source_lines)


def _benchmark_specific_runtime_branch(payload: Payload) -> AntiCheatViolation | None:
    code_text = str(payload.get("runtime_code") or payload.get("code_text") or "")
    candidate = _candidate_runtime_code(code_text)
    tokens = _runtime_tokens(
        candidate.text,
        added_line_numbers=candidate.added_line_numbers,
        line_segments=candidate.line_segments,
    )
    token_lines = _token_start_lines(tokens)
    bindings: dict[tuple[int, str], _BenchmarkConstantBinding] = {}
    selector_clauses: dict[int, tuple[_RuntimeToken, ...]] = {}
    brace_selector_segments: dict[int, bool] = {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        assignment = (
            _direct_assignment_shape(tokens, index)
            if token.kind == "word"
            else None
        )
        assignment_end = index + 1
        if assignment is not None:
            assignment_end = max(
                assignment_end,
                index + len(assignment.tokens),
            )
            if not assignment.assigns_value:
                embedded_branch_offset = next(
                    (
                        offset
                        for offset, assignment_token in enumerate(
                            assignment.tokens[1:],
                            start=1,
                        )
                        if assignment_token.kind == "word"
                        and assignment_token.value.casefold()
                        in _BRANCH_KEYWORDS
                    ),
                    None,
                )
                if embedded_branch_offset is not None:
                    assignment_end = index + embedded_branch_offset
            binding_key = (token.source_segment, token.value)
            if assignment.assigns_value:
                if (
                    assignment.assigned_value is not None
                    and _is_standalone_benchmark_label_token(
                        assignment.assigned_value
                    )
                ):
                    bindings[binding_key] = _BenchmarkConstantBinding(
                        token_index=index,
                        candidate_added=_candidate_touched(
                            assignment.tokens
                        ),
                    )
                else:
                    bindings.pop(binding_key, None)
                index = assignment_end
                continue

        keyword = token.value.casefold()
        if token.kind != "word" or keyword not in _BRANCH_KEYWORDS:
            index = assignment_end
            continue
        if index > 0 and tokens[index - 1].value == ".":
            index += 1
            continue

        clause, clause_end = _branch_clause_span(tokens, index + 1)
        next_index = max(index + 1, clause_end)
        if (
            keyword == "case"
            and not _case_keyword_is_structural(
                tokens,
                index,
                clause_end,
            )
        ):
            index = next_index
            continue
        if (
            keyword in _SELECTOR_KEYWORDS
            and not _selector_keyword_is_structural(
                tokens,
                index,
                clause_end,
                keyword,
            )
        ):
            index = next_index
            continue

        if keyword in _SELECTOR_KEYWORDS:
            selector_clauses[token.source_segment] = (
                clause if _contains_benchmark_subject(clause) else ()
            )
            brace_selector_segments[token.source_segment] = (
                keyword == "switch"
            )
        selector_clause = (
            selector_clauses.get(token.source_segment, ())
            if keyword == "case"
            else ()
        )

        bound_labels: list[_BenchmarkConstantBinding] = []
        for clause_token in clause:
            if clause_token.kind != "word":
                continue
            binding = bindings.get(
                (clause_token.source_segment, clause_token.value)
            )
            if binding is not None and binding.token_index <= index:
                bound_labels.append(binding)
        if (
            not _contains_standalone_benchmark_label(clause)
            and not bound_labels
        ):
            index = next_index
            continue

        has_context = (
            _contains_strong_benchmark_label(clause)
            or _contains_benchmark_subject(clause)
            or bool(selector_clause)
        )
        candidate_touched_branch = (
            token.candidate_added
            or _candidate_touched(clause)
            or _candidate_touched(selector_clause)
            or any(binding.candidate_added for binding in bound_labels)
            or _candidate_touched_branch_body(
                candidate,
                tokens,
                token_lines,
                keyword_index=index,
                clause_end=clause_end,
                keyword=keyword,
                case_in_brace_selector=(
                    keyword == "case"
                    and brace_selector_segments.get(
                        token.source_segment,
                        False,
                    )
                ),
            )
        )
        if has_context and candidate_touched_branch:
            return _violation("benchmark_specific_runtime_branch", "benchmark_specific_runtime_branch", "Runtime code contains a benchmark-keyed branch.", FailureClass.VALIDATOR_FAILURE)
        index = next_index
    return None


def _test_only_production_branch(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("runtime_integration") is True and payload.get("implementation_origin") in {"test_only", "fixture", "harness_only"}:
        return _violation("test_only_production_branch", "test_only_path_labeled_production", "Test-only orchestration was labeled production integration.", FailureClass.VALIDATOR_FAILURE)
    return None


DETECTORS: tuple[AntiCheatDetector, ...] = (
    AntiCheatDetector("canned_output", "Detect canned output not derived from behavior.", _canned_output),
    AntiCheatDetector("static_research_labeled_live", "Detect static research labeled live.", _static_research_labeled_live),
    AntiCheatDetector("route_existence_as_integration", "Detect route-only integration proof.", _route_existence_as_integration),
    AntiCheatDetector("status_ping_as_behavior", "Detect status ping counted as behavior.", _status_ping_as_behavior),
    AntiCheatDetector("repo_context_as_internet", "Detect repo context labeled internet research.", _repo_context_as_internet),
    AntiCheatDetector("fixture_mock_labeled_live", "Detect fixture/mock evidence labeled live.", _fixture_mock_labeled_live),
    AntiCheatDetector("preview_advisory_labeled_executed", "Detect preview/advisory labeled executed.", _preview_advisory_labeled_executed),
    AntiCheatDetector("fallback_labeled_primary_success", "Detect fallback success counted as primary.", _fallback_labeled_primary_success),
    AntiCheatDetector("renderer_created_decision", "Detect renderer-created substantive decisions.", _renderer_created_decision),
    AntiCheatDetector("manual_pass_json_manipulation", "Detect manual PASS or JSON flipping.", _manual_pass_json_manipulation),
    AntiCheatDetector("canned_output_with_consumer_event", "Detect canned output carrying consumer event id.", _canned_output_with_consumer_event),
    AntiCheatDetector("unavailable_provider_labeled_success", "Detect unavailable provider reported successful.", _unavailable_provider_labeled_success),
    AntiCheatDetector("summary_raw_contradiction", "Detect summary/raw evidence contradiction.", _summary_raw_contradiction),
    AntiCheatDetector("benchmark_specific_runtime_branch", "Detect benchmark-keyed runtime branch.", _benchmark_specific_runtime_branch),
    AntiCheatDetector("test_only_production_branch", "Detect test-only path labeled production.", _test_only_production_branch),
)
