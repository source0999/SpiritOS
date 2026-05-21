from __future__ import annotations

import os
import re
import json
import shutil
import subprocess
import tempfile
from pathlib import PurePosixPath
from pathlib import Path
from typing import Any

from source_proxy.planning.plan import ArchitectPlan, task_spec_from_plan
from source_proxy.planning.reviewer import (
    review_diff_deterministically,
    review_diff_with_llm,
    reviewer_llm_is_configured,
)
from source_proxy.safety.paths import has_percent_encoded_path_syntax
from source_proxy.verification.deterministic import deterministic_checks_from_preview
from source_proxy.verification.contracts import validate_replacement_content


MAX_DIFF_BYTES = 200_000

# Bridge: diff preview may set limits.file_writes_allowed for local_route when the
# diff is not blocked. Actual writes only happen after human approval via
# POST /v1/tasks/long-running/{task_id}/execute-approved (see main.app.state).
LOCAL_ROUTE_DIFF_FILE_WRITES_AFTER_APPROVAL = True

SECRET_NAME_MARKERS = (
    ".env",
    ".pem",
    ".key",
    "secret",
    "token",
    "credential",
    "id_rsa",
    "id_ed25519",
)

HIGH_RISK_EXACT_NAMES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "requirements.core.txt",
    "requirements.cuda.txt",
    "next.config.ts",
    "next.config.js",
    "middleware.ts",
}

HIGH_RISK_PREFIXES = (
    "source_proxy/main.py",
    "source_proxy/api/",
    "source_proxy/sandbox/",
)


class DiffVerificationError(ValueError):
    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


# LLM / hand-edited hunks often drop the leading SP on context lines. `git apply` then
# dies with ``corrupt patch at line N`` — first bad line is usually bare source text.
_HUNK_HEADER_RE = re.compile(r"^@@\s+-\d+(?:,\d+)?\s+\+\d+(?:,\d+)?\s+@@")
_HUNK_HEADER_PARSE_RE = re.compile(
    r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?(\s+@@.*)$",
)
_CLASS_FRAGMENT_TOKEN_RE = re.compile(
    r"^[A-Za-z0-9_:/[\].()-]+-[A-Za-z0-9_:/[\].()-]+$"
)
_CODE_IDENTIFIER_RE = re.compile(
    r"(?<![A-Za-z0-9_$./-])(?:"
    r"[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+"
    r"|[A-Z][A-Za-z0-9_$]*[a-z0-9_$][A-Za-z0-9_$]*[A-Z][A-Za-z0-9_$]*"
    r"|[a-z][A-Za-z0-9_$]*[A-Z][A-Za-z0-9_$]*"
    r"|[A-Za-z_$][\w$]*_[A-Za-z0-9_$][\w$]*"
    r")(?![A-Za-z0-9_$/-])"
)
_CLASS_UTILITY_PREFIXES = {
    "accent",
    "align",
    "animate",
    "aspect",
    "backdrop",
    "bg",
    "block",
    "border",
    "bottom",
    "col",
    "container",
    "content",
    "cursor",
    "decoration",
    "delay",
    "divide",
    "drop",
    "duration",
    "ease",
    "fill",
    "filter",
    "flex",
    "flow",
    "font",
    "gap",
    "gradient",
    "grid",
    "grow",
    "h",
    "hover",
    "inset",
    "items",
    "justify",
    "left",
    "leading",
    "line",
    "m",
    "max",
    "mb",
    "min",
    "ml",
    "mr",
    "mt",
    "mx",
    "my",
    "object",
    "opacity",
    "order",
    "outline",
    "overflow",
    "p",
    "pb",
    "place",
    "pl",
    "pointer",
    "pr",
    "pt",
    "px",
    "py",
    "relative",
    "resize",
    "right",
    "ring",
    "rotate",
    "rounded",
    "scale",
    "shadow",
    "shrink",
    "skew",
    "space",
    "sr",
    "stroke",
    "table",
    "text",
    "top",
    "tracking",
    "transform",
    "transition",
    "translate",
    "underline",
    "w",
    "z",
}
_FRAGMENT_META_WORDS = {"class", "classname", "classes", "fragment", "fragments", "include", "includes", "target"}
_CODE_FRAGMENT_PATH_SUFFIXES = {
    ".css",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".mdx",
    ".py",
    ".ts",
    ".tsx",
}


def _hunk_body_line_counts(body: list[str]) -> tuple[int, int]:
    """Return (old_file_line_count, new_file_line_count) for lines inside one hunk."""
    old_n = 0
    new_n = 0
    for bl in body:
        if bl == r"\ No newline at end of file":
            continue
        if bl == "":
            old_n += 1
            new_n += 1
            continue
        c0 = bl[0]
        if c0 == " ":
            old_n += 1
            new_n += 1
        elif c0 == "+" and not bl.startswith("+++"):
            new_n += 1
        elif c0 == "-" and not bl.startswith("---"):
            old_n += 1
        else:
            old_n += 1
            new_n += 1
    return old_n, new_n


def repair_unified_diff_hunk_counts(unified_diff: str) -> str:
    """Rewrite ``@@`` old/new line counts so they match hunk body (LLMs lie here constantly)."""
    if not unified_diff.strip():
        return unified_diff
    lines = unified_diff.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    i = 0
    out: list[str] = []
    while i < len(lines):
        line = lines[i]
        m = _HUNK_HEADER_PARSE_RE.match(line)
        if not m:
            out.append(line)
            i += 1
            continue
        old_s_s, old_c_decl, new_s_s, new_c_decl, tail = m.groups()
        old_start = int(old_s_s)
        new_start = int(new_s_s)
        j = i + 1
        while j < len(lines):
            nxt = lines[j]
            if _HUNK_HEADER_RE.match(nxt) or nxt.startswith("diff --git "):
                break
            j += 1
        body = lines[i + 1 : j]
        old_n, new_n = _hunk_body_line_counts(body)
        # ``@@ -1,9 +9 @@`` is almost always ``@@ -1,9 +1,9 @@`` (dropped ``,1``). Only rewrite when
        # the declared old line span is **larger** than the real hunk — otherwise we stomp
        # legitimate ``+N`` start positions and ``git apply`` fails at file line 1.
        if (
            new_c_decl is None
            and old_c_decl is not None
            and old_s_s == "1"
            and new_s_s == old_c_decl
            and int(old_c_decl) > old_n
        ):
            new_start = 1
        # New-from-empty hunks must stay anchored at -0,0 or git apply rejects the hunk.
        only_additions = bool(body) and all(
            (ln.startswith("+") and not ln.startswith("+++"))
            or ln == r"\ No newline at end of file"
            or ln == ""
            for ln in body
        )
        if old_n == 0 and only_additions:
            old_start = 0
        out.append(f"@@ -{old_start},{old_n} +{new_start},{new_n}{tail}")
        out.extend(body)
        i = j
    result = "\n".join(out)
    if not result.endswith("\n"):
        result += "\n"
    return result


def minimal_transport_diff_for_git(unified_diff: str) -> str:
    """LF endings + trailing newline only — never mutates hunk line prefixes."""
    text = unified_diff.replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        return ""
    if not text.endswith("\n"):
        text += "\n"
    return text


def sanitize_unified_diff_for_git_apply(
    unified_diff: str,
    *,
    force_prefix: bool | None = None,
    repair_hunks: bool = True,
) -> str:
    """Normalize newlines, blank hunk lines, optional bare-line prefix repair, then hunk counts.

    ``force_prefix=None`` uses env ``SOURCE_PROXY_DIFF_PREFIX_BARE_LINES`` (default off).
    ``force_prefix=False`` / ``True`` overrides env for this call only.

    ``repair_hunks=False`` skips ``repair_unified_diff_hunk_counts`` — LLM ``@@`` lines are
    sometimes already correct and recount repair can shift anchors so ``git apply`` dies
    mid-file (e.g. line 338) while line-1 context still matches.
    """
    text = unified_diff.replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        return ""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    out: list[str] = []
    in_hunk_body = False
    if force_prefix is None:
        prefix_bare = os.environ.get("SOURCE_PROXY_DIFF_PREFIX_BARE_LINES", "").lower() in (
            "1",
            "true",
            "yes",
        )
    else:
        prefix_bare = force_prefix

    for line in lines:
        if _HUNK_HEADER_RE.match(line):
            in_hunk_body = True
            out.append(line)
            continue

        if in_hunk_body:
            if line.startswith("diff --git "):
                in_hunk_body = False
                out.append(line)
                continue
            if _HUNK_HEADER_RE.match(line):
                out.append(line)
                continue
            if line.startswith("Binary files ") and " differ" in line:
                in_hunk_body = False
                out.append(line)
                continue
            if line == r"\ No newline at end of file":
                out.append(line)
                continue
            if line == "":
                out.append(" ")
                continue
            if prefix_bare and line[0] not in " +-\\":
                out.append(f" {line}")
                continue

        out.append(line)

    result = "\n".join(out)
    if not result.endswith("\n"):
        result += "\n"
    if repair_hunks:
        return repair_unified_diff_hunk_counts(result)
    return result


def diff_candidates_for_git_apply(unified_diff: str) -> list[str]:
    """Ordered variants to try with ``git apply --check`` (least invasive first).

    1. CRLF + trailing newline only.
    2. Sanitize (blank lines, etc.) **without** ``@@`` recount repair — preserves LLM anchors.
    3. Sanitize + recount repair, no forced bare-line prefix.
    4. Sanitize + repair + forced prefix (fixes ``corrupt patch`` on missing `` `` lines).
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for cand in (
        minimal_transport_diff_for_git(unified_diff),
        sanitize_unified_diff_for_git_apply(unified_diff, force_prefix=False, repair_hunks=False),
        sanitize_unified_diff_for_git_apply(unified_diff, force_prefix=False),
        sanitize_unified_diff_for_git_apply(unified_diff, force_prefix=True),
    ):
        if cand and cand not in seen:
            seen.add(cand)
            ordered.append(cand)
    return ordered


def _typescript_like_files(files: list[dict[str, Any]]) -> list[str]:
    return [
        str(file.get("path") or "").replace("\\", "/")
        for file in files
        if str(file.get("extension") or "").lower() in {".ts", ".tsx"}
        and str(file.get("change_type") or "").lower() != "deleted"
    ]


def _pick_syntax_workspace_root(roots: list[Path], files: list[dict[str, Any]]) -> Path | None:
    rels = [
        str(file.get("path") or "").strip().replace("\\", "/")
        for file in files
        if str(file.get("path") or "").strip()
    ]
    candidate_roots = [Path.cwd(), *roots]
    for root in candidate_roots:
        resolved = root.resolve()
        if not resolved.is_dir():
            continue
        if any((resolved / rel).exists() for rel in rels):
            return resolved
    for root in candidate_roots:
        resolved = root.resolve()
        if resolved.is_dir():
            return resolved
    return None


def _copy_changed_existing_files(root: Path, temp_root: Path, files: list[dict[str, Any]]) -> None:
    for file in files:
        if str(file.get("change_type") or "").lower() == "added":
            continue
        rel = str(file.get("path") or "").strip().replace("\\", "/")
        if not rel:
            continue
        src = (root / rel).resolve()
        try:
            src.relative_to(root)
        except ValueError:
            continue
        if not src.is_file():
            continue
        dst = temp_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)


def _apply_diff_to_temp_tree(unified_diff: str, temp_root: Path) -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        suffix=".patch",
        delete=False,
    ) as patch_file:
        patch_file.write(unified_diff)
        patch_path = Path(patch_file.name)
    try:
        result = subprocess.run(
            ["git", "apply", "--recount", str(patch_path)],
            cwd=temp_root,
            capture_output=True,
            text=True,
            timeout=15,
        )
    finally:
        patch_path.unlink(missing_ok=True)
    if result.returncode == 0:
        return True, ""
    return False, (result.stderr or result.stdout or "git apply failed").strip()


def _run_typescript_parse_check(
    *,
    workspace_root: Path,
    temp_root: Path,
    rel_paths: list[str],
) -> dict[str, Any]:
    node_script = r"""
const ts = require("typescript");
const fs = require("fs");
const path = require("path");
const files = process.argv.slice(1);
for (const file of files) {
  const source = fs.readFileSync(file, "utf8");
  const ext = path.extname(file).toLowerCase();
  const kind = ext === ".tsx" ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  const sourceFile = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true, kind);
  if (sourceFile.parseDiagnostics.length > 0) {
    const diagnostic = sourceFile.parseDiagnostics[0];
    const pos = sourceFile.getLineAndCharacterOfPosition(diagnostic.start || 0);
    const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, " ");
    console.log(JSON.stringify({
      ok: false,
      path: file,
      summary: `${path.basename(file)}:${pos.line + 1}:${pos.character + 1} TS${diagnostic.code}: ${message}`,
    }));
    process.exit(0);
  }
}
console.log(JSON.stringify({ ok: true, summary: "TypeScript parser accepted changed TS/TSX files." }));
"""
    abs_paths = [str(temp_root / rel) for rel in rel_paths if (temp_root / rel).is_file()]
    if not abs_paths:
        return {
            "ok": True,
            "skipped": True,
            "summary": "No materialized TS/TSX files required syntax parsing.",
        }
    result = subprocess.run(
        ["node", "-e", node_script, *abs_paths],
        cwd=_typescript_node_cwd(workspace_root),
        capture_output=True,
        text=True,
        timeout=20,
    )
    raw = (result.stdout or "").strip().splitlines()
    if result.returncode != 0:
        summary = (result.stderr or result.stdout or "TypeScript parser check failed.").strip()
        return {"ok": False, "path": "*", "summary": summary[:1000]}
    try:
        parsed = json.loads(raw[-1] if raw else "{}")
    except json.JSONDecodeError:
        return {
            "ok": False,
            "path": "*",
            "summary": "TypeScript parser check returned malformed output.",
        }
    if not isinstance(parsed, dict):
        return {
            "ok": False,
            "path": "*",
            "summary": "TypeScript parser check returned malformed output.",
        }
    if parsed.get("path"):
        abs_path = Path(str(parsed["path"]))
        for rel in rel_paths:
            if abs_path == temp_root / rel:
                parsed["path"] = rel
                break
    return parsed


def _typescript_node_cwd(workspace_root: Path) -> Path:
    if (workspace_root / "node_modules" / "typescript").is_dir():
        return workspace_root
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "node_modules" / "typescript").is_dir():
            return parent
    return workspace_root


def _typescript_syntax_check(
    unified_diff: str,
    files: list[dict[str, Any]],
    roots: list[Path],
) -> dict[str, Any]:
    rel_paths = _typescript_like_files(files)
    if not rel_paths:
        return {
            "ok": True,
            "skipped": True,
            "summary": "No TS/TSX files changed.",
        }
    root = _pick_syntax_workspace_root(roots, files)
    if root is None:
        return {
            "ok": False,
            "path": "*",
            "summary": "No workspace root was available for TypeScript syntax checking.",
        }
    try:
        with tempfile.TemporaryDirectory(prefix="spirit-ts-preview-") as tmp:
            temp_root = Path(tmp)
            _copy_changed_existing_files(root, temp_root, files)
            applied, apply_error = _apply_diff_to_temp_tree(unified_diff, temp_root)
            if not applied:
                return {
                    "ok": True,
                    "skipped": True,
                    "summary": f"Skipped TypeScript parser check because preview materialization failed: {apply_error}",
                }
            return _run_typescript_parse_check(
                workspace_root=root,
                temp_root=temp_root,
                rel_paths=rel_paths,
            )
    except (OSError, subprocess.SubprocessError) as error:
        return {
            "ok": False,
            "path": "*",
            "summary": f"TypeScript syntax check failed to run: {error}",
        }


def _added_diff_text(unified_diff: str) -> str:
    lines: list[str] = []
    for raw_line in unified_diff.splitlines():
        if raw_line.startswith("+++") or not raw_line.startswith("+"):
            continue
        lines.append(raw_line[1:])
    return "\n".join(lines)


def _extract_explicit_target(task_text: str) -> str | None:
    match = re.search(
        r"^\s*Target\s+file\s*:\s*`?([A-Za-z0-9._/@()[\]-]+\.[A-Za-z0-9]+)`?",
        task_text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if match:
        return match.group(1).replace("\\", "/").strip()
    return None


_REQUIREMENT_CONTEXT_MARKER_RE = re.compile(
    r"^\s*(?:"
    r"file\s+content|"
    r"current\s+file|"
    r"repository\s+context|"
    r"preferred\s+output\s+schema|"
    r"legacy\s+accepted\s+schema|"
    r"taskspec|"
    r"portal\s+safety\s+contract|"
    r"non-negotiable\s+portal\s+contract|"
    r"verification\s+plan|"
    r"coder\s+diagnostics|"
    r"local\s+coder\s+failure\s+to\s+avoid|"
    r"ask"
    r")\s*:",
    flags=re.IGNORECASE | re.MULTILINE,
)


def _requirement_source_text(task_text: str) -> str:
    """Keep user requirements, but ignore pasted context/output schemas and proposal JSON envelopes."""
    from source_proxy.decision.proposal_task import effective_planning_task_text

    normalized = effective_planning_task_text(task_text or "")
    match = _REQUIREMENT_CONTEXT_MARKER_RE.search(normalized)
    if not match:
        return normalized
    return normalized[: match.start()].rstrip()


def _route_to_app_router_page(route: str) -> str | None:
    route = route.strip()
    if not route.startswith("/"):
        return None
    segments = [
        segment
        for segment in route.strip("/").split("/")
        if segment and not segment.startswith("_") and not (segment.startswith("(") and segment.endswith(")"))
    ]
    if not segments:
        return "src/app/page.tsx"
    return "src/app/" + "/".join(segments) + "/page.tsx"


_PATH_PREFIX_BEFORE_ROUTE_RE = re.compile(
    r"(?:^|[\s`\"'])(?:src|lib|app|components|pages?)/[\w./-]*$",
    re.IGNORECASE,
)

_NEGATIVE_CONSTRAINT_LINE_RE = re.compile(
    r"(?im)^\s*(?:"
    r"(?:do\s+not|don't|never|not)\s+(?:modify|edit|touch|change|update|alter)\b"
    r"|(?:forbidden|blocked)\b"
    r")"
)


def _line_bounds(task_text: str, index: int) -> tuple[int, int]:
    line_start = task_text.rfind("\n", 0, index) + 1
    line_end = task_text.find("\n", index)
    if line_end == -1:
        line_end = len(task_text)
    return line_start, line_end


def _negative_constraint_route_paths(task_text: str) -> set[str]:
    blocked: set[str] = set()
    for line in task_text.splitlines():
        if not _NEGATIVE_CONSTRAINT_LINE_RE.search(line):
            continue
        for match in re.finditer(r"(?<![A-Za-z0-9_./@<-])(/[A-Za-z0-9_()/.-]+)", line):
            cleaned = match.group(1).rstrip(".,;:")
            if "." in PurePosixPath(cleaned).name:
                continue
            blocked.add(cleaned)
    return blocked


def _extract_route_path(task_text: str) -> str | None:
    negative_routes = _negative_constraint_route_paths(task_text)
    for match in re.finditer(r"(?<![A-Za-z0-9_./@<-])(/[A-Za-z0-9_()/.-]+)", task_text):
        cleaned = match.group(1).rstrip(".,;:")
        if "." in PurePosixPath(cleaned).name:
            continue
        if cleaned.lower() in {"/h1", "/main", "/div", "/section"}:
            continue
        if cleaned in negative_routes:
            continue
        line_start, line_end = _line_bounds(task_text, match.start())
        if _NEGATIVE_CONSTRAINT_LINE_RE.search(task_text[line_start:line_end]):
            continue
        prefix = task_text[max(0, match.start() - 40) : match.start()]
        if _PATH_PREFIX_BEFORE_ROUTE_RE.search(prefix):
            continue
        return cleaned
    return None


_QUOTED_TEXT_RE = re.compile(
    r"(?P<quote>[\"'`])(?P<value>[^\"'`\n]{3,120})(?P=quote)"
)
_TRANSFORMATION_TEXT_PATTERNS = (
    re.compile(
        r"\b(?:change|rename)\s+"
        r"(?P<src_quote>[\"'`])(?P<source>[^\"'`\n]{3,120})(?P=src_quote)\s+"
        r"to\s+"
        r"(?P<final_quote>[\"'`])(?P<final>[^\"'`\n]{3,120})(?P=final_quote)",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\breplace\s+"
        r"(?P<src_quote>[\"'`])(?P<source>[^\"'`\n]{3,120})(?P=src_quote)\s+"
        r"with\s+"
        r"(?P<final_quote>[\"'`])(?P<final>[^\"'`\n]{3,120})(?P=final_quote)",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\bswap\s+"
        r"(?P<src_quote>[\"'`])(?P<source>[^\"'`\n]{3,120})(?P=src_quote)\s+"
        r"for\s+"
        r"(?P<final_quote>[\"'`])(?P<final>[^\"'`\n]{3,120})(?P=final_quote)",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\bfrom\s+"
        r"(?P<src_quote>[\"'`])(?P<source>[^\"'`\n]{3,120})(?P=src_quote)\s+"
        r"to\s+"
        r"(?P<final_quote>[\"'`])(?P<final>[^\"'`\n]{3,120})(?P=final_quote)",
        flags=re.IGNORECASE,
    ),
)


def _dedupe_nonempty(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _is_path_like_text_requirement(value: str) -> bool:
    return "/" in value and value.endswith((".tsx", ".ts", ".js", ".jsx", ".md"))


def _should_skip_quoted_text_requirement(task_text: str, match: re.Match[str]) -> bool:
    value = match.group("value").strip()
    prefix = task_text[max(0, match.start() - 24) : match.start()]
    return bool(re.search(r"(?:className|class)\s*=\s*$", prefix)) or (
        _is_path_like_text_requirement(value)
    )


def _extract_transformation_text_requirements(task_text: str) -> dict[str, list[str]]:
    source_terms: list[str] = []
    required_final_terms: list[str] = []
    for pattern in _TRANSFORMATION_TEXT_PATTERNS:
        for match in pattern.finditer(task_text):
            source = match.group("source").strip()
            final = match.group("final").strip()
            if not _is_path_like_text_requirement(source):
                source_terms.append(source)
            if not _is_path_like_text_requirement(final):
                required_final_terms.append(final)
    source_terms = _dedupe_nonempty(source_terms)
    return {
        "source_terms": source_terms,
        "required_final_terms": _dedupe_nonempty(required_final_terms),
        "optional_absent_terms": source_terms,
    }


def _extract_markdown_append_literal(task_text: str) -> str:
    """Single append literal from quotes or the standalone line after an exact-sentence instruction."""
    normalized = (task_text or "").strip()
    if not re.search(r"\bappend\b", normalized, re.IGNORECASE):
        return ""
    if not re.search(r"\bexact\s+sentence\b", normalized, re.IGNORECASE):
        return ""

    without_target = "\n".join(
        line
        for line in normalized.splitlines()
        if not line.strip().lower().startswith("target file:")
    )
    quoted = [
        match.group(2).strip()
        for match in re.finditer(r"([\"'`])(.+?)\1", without_target)
        if match.group(2).strip() and "\n" not in match.group(2)
    ]
    if len(quoted) == 1:
        literal = quoted[0]
        if 3 <= len(literal) <= 240:
            return literal

    lines = [line.strip() for line in without_target.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if not re.search(r"\bappend\b.*\bexact\s+sentence\b", line, re.IGNORECASE):
            continue
        for candidate in lines[index + 1 :]:
            lowered = candidate.lower()
            if lowered.startswith(("do not", "don't", "never ", "not ")):
                continue
            if candidate.startswith("/") and " " not in candidate.strip("/"):
                continue
            if 3 <= len(candidate) <= 240:
                return candidate
        break
    return ""


def _extract_text_requirements(task_text: str) -> dict[str, list[str]]:
    transformations = _extract_transformation_text_requirements(task_text)
    source_terms = set(transformations["source_terms"])
    found: list[str] = list(transformations["required_final_terms"])

    append_literal = _extract_markdown_append_literal(task_text)
    if append_literal:
        found.append(append_literal)

    for match in _QUOTED_TEXT_RE.finditer(task_text):
        value = match.group("value").strip()
        if value in source_terms or _should_skip_quoted_text_requirement(task_text, match):
            continue
        found.append(value)
    for value in re.findall(
        r"<h1\b[^>]*>([^<\n]{3,160})</h1>",
        task_text,
        flags=re.IGNORECASE,
    ):
        found.append(value.strip())
    lines = task_text.splitlines()
    for index, line in enumerate(lines[:-1]):
        if re.search(r"\b(?:exact\s+h1|h1|title|heading)\b\s*:?\s*$", line, re.IGNORECASE):
            candidate = lines[index + 1].strip(" -`\"'")
            if re.search(r"\b(?:class(?:Name)?|includes?|import|route|target)\b\s*:", candidate, re.IGNORECASE):
                continue
            if 3 <= len(candidate) <= 120:
                found.append(candidate)
    return {
        "source_terms": transformations["source_terms"],
        "required_final_terms": _dedupe_nonempty(found),
        "optional_absent_terms": transformations["optional_absent_terms"],
    }


def _extract_exact_text_requirements(task_text: str) -> list[str]:
    return _extract_text_requirements(task_text)["required_final_terms"]


def _without_quoted_text(text: str) -> str:
    chars = list(text)
    for match in re.finditer(r"([\"'`]).+?\1", text):
        start, end = match.span()
        chars[start:end] = " " * (end - start)
    return "".join(chars)


def _class_utility_like(value: str) -> bool:
    if not _CLASS_FRAGMENT_TOKEN_RE.fullmatch(value):
        return False
    base = value.split(":", 1)[-1]
    prefix = base.split("-", 1)[0]
    return prefix in _CLASS_UTILITY_PREFIXES


def _code_identifier_like(value: str) -> bool:
    return bool(_CODE_IDENTIFIER_RE.fullmatch(value))


def _path_like_code_fragment(value: str) -> bool:
    lowered = value.strip("`'\".;:").lower()
    return any(lowered.endswith(suffix) for suffix in _CODE_FRAGMENT_PATH_SUFFIXES)


def _extract_class_fragments(task_text: str) -> list[str]:
    known = (
        "text-6xl",
        "font-light",
        "tracking-tighter",
        "min-h-screen",
        "min-h-dvh",
        "backdrop-blur",
        "bg-black",
    )
    found = [fragment for fragment in known if re.search(rf"(?<![A-Za-z0-9_-]){re.escape(fragment)}(?![A-Za-z0-9_-])", task_text)]
    searchable = _without_quoted_text(task_text)
    for match in re.findall(r"\b(?:class(?:Name)?(?:\s+fragments?)?|includes?)\s*:\s*([^\n]+)", searchable, flags=re.IGNORECASE):
        for token in re.split(r"[\s,]+", match.strip()):
            cleaned = token.strip("`'\".;:")
            if _path_like_code_fragment(cleaned):
                continue
            if _class_utility_like(cleaned) or _code_identifier_like(cleaned):
                found.append(cleaned)
    for match in _CODE_IDENTIFIER_RE.finditer(searchable):
        value = match.group(0)
        if value.lower() in _FRAGMENT_META_WORDS or value.lower().startswith("target"):
            continue
        if _path_like_code_fragment(value):
            continue
        found.append(value)
    return list(dict.fromkeys(found))


def _extract_import_requirements(task_text: str) -> list[dict[str, str]]:
    requirements: list[dict[str, str]] = []
    for symbol, source in re.findall(
        r"\bimport\s+([A-Za-z_$][\w$]*)\s+from\s+[`\"]([^`\"]+)[`\"]",
        task_text,
        flags=re.IGNORECASE,
    ):
        requirements.append({"symbol": symbol, "source": source})
    if "GlassPanel" in task_text and "@/components/ui/GlassPanel" in task_text:
        requirements.append({"symbol": "GlassPanel", "source": "@/components/ui/GlassPanel"})
    return list({f"{item['symbol']}::{item['source']}": item for item in requirements}.values())


def _resolve_requirement_target(
    task_text: str,
    *,
    architect_plan: ArchitectPlan | None = None,
    task_spec: dict[str, Any] | None = None,
) -> str | None:
    target = _extract_explicit_target(task_text)
    if target:
        return target
    if architect_plan is not None:
        plan_target = str(architect_plan.coder_packet.target_file.path or "").replace("\\", "/").strip()
        if plan_target:
            return plan_target
    if isinstance(task_spec, dict):
        for key in ("target_file", "target", "path"):
            raw = task_spec.get(key)
            if isinstance(raw, str) and raw.strip():
                return raw.replace("\\", "/").strip()
    return None


def _requirement_coverage(
    unified_diff: str,
    files: list[dict[str, Any]],
    task_text: str | None,
    *,
    explicit_target: str | None = None,
) -> dict[str, Any]:
    task = _requirement_source_text(task_text or "").strip()
    if not task:
        return {"ok": True, "skipped": True, "summary": "No task text supplied."}

    added = _added_diff_text(unified_diff)
    diff_text = unified_diff.replace("\\", "/")
    changed_paths = {
        _normalize_task_spec_path(str(file.get("path") or ""))
        for file in files
        if _normalize_task_spec_path(str(file.get("path") or ""))
    }
    missing: list[str] = []

    target = explicit_target or _extract_explicit_target(task)
    if target:
        target = _normalize_task_spec_path(target)
    route = _extract_route_path(task)
    route_target = _route_to_app_router_page(route) if route else None
    if changed_paths and all(path.endswith(".md") for path in changed_paths if path):
        route = None
        route_target = None
    elif target and target.endswith(".md"):
        route = None
        route_target = None
    text_requirements = _extract_text_requirements(task)
    texts = text_requirements["required_final_terms"]
    class_fragments = _extract_class_fragments(task)
    imports = _extract_import_requirements(task)

    if target and target not in changed_paths:
        missing.append(f"missing target file: {target}")
    if route and route_target and target and target != route_target:
        missing.append(f"route {route} maps to {route_target}, not {target}")
    if route and route_target and not target and route_target not in changed_paths:
        missing.append(f"missing route file: {route_target}")

    for text in texts:
        if text not in added and text not in diff_text:
            missing.append(f"missing exact text: {text}")
    for fragment in class_fragments:
        if fragment not in added and fragment not in diff_text:
            missing.append(f"missing className: {fragment}")
    for item in imports:
        symbol = item["symbol"]
        source = item["source"]
        if symbol not in added or source not in added:
            missing.append(f"missing import: {symbol} from {source}")

    has_output_only_policy = bool(
        re.search(r"\bOutput\s+ONLY\b.*\bunified\s+diff\b", task, re.IGNORECASE | re.DOTALL)
    )
    if has_output_only_policy:
        for bad in ("Target file:", "Here is", "```"):
            if bad in added:
                missing.append(f"raw non-code text detected in diff: {bad}")

    required = {
        "target": target,
        "route": route,
        "route_target": route_target,
        "texts": texts,
        "source_terms": text_requirements["source_terms"],
        "optional_absent_terms": text_requirements["optional_absent_terms"],
        "class_fragments": class_fragments,
        "imports": imports,
    }
    has_requirements = any(value for value in required.values()) or has_output_only_policy
    if not has_requirements:
        return {
            "ok": True,
            "skipped": True,
            "required": required,
            "summary": "No exact requirements detected.",
        }
    return {
        "ok": not missing,
        "missing": missing,
        "required": required,
        "summary": "Requirement coverage passed." if not missing else "; ".join(missing[:8]),
    }


def _task_text_for_diff_preview(task_text: str | None) -> str:
    from source_proxy.decision.proposal_task import effective_planning_task_text

    raw = (task_text or "").strip()
    if not raw:
        return ""
    return effective_planning_task_text(raw)


def preview_diff_verification(
    unified_diff: str,
    *,
    test_command: list[str] | None = None,
    route_type: str | None = None,
    next_prompt_action: str | None = None,
    task_text: str | None = None,
    architect_plan: ArchitectPlan | None = None,
    task_spec: dict[str, Any] | None = None,
    reviewer_llm_call=None,
) -> dict[str, Any]:
    preview_task_text = _task_text_for_diff_preview(task_text)
    unified_diff = sanitize_unified_diff_for_git_apply(unified_diff)
    if not unified_diff.strip():
        raise DiffVerificationError("A unified diff is required.", "empty_diff")
    diff_bytes = len(unified_diff.encode("utf-8", errors="replace"))
    if diff_bytes > MAX_DIFF_BYTES:
        raise DiffVerificationError("Unified diff is too large for preview.", "diff_too_large")

    from source_proxy.tasks import long_running as _lr

    roots = _lr._ordered_workspace_roots_for_apply()
    pre_files = _parse_changed_files(unified_diff)
    _, unified_diff, _ = _lr._normalize_next_app_router_diff_targets(
        roots,
        pre_files,
        unified_diff,
    )
    files = _parse_changed_files(unified_diff)
    blocked_reasons = _blocked_reasons(files)
    task_spec_payload = _task_spec_payload_for_preview(
        architect_plan=architect_plan,
        task_spec=task_spec,
    )
    task_spec_check = task_spec_diff_check(task_spec_payload, files)
    if not task_spec_check["ok"]:
        blocked_reasons = [
            *blocked_reasons,
            *[
                {"path": path or "*", "reason_code": reason_code}
                for reason_code, path in _task_spec_blocked_reason_pairs(
                    task_spec_check
                )
            ],
        ]
    syntax_check = _typescript_syntax_check(unified_diff, files, roots)
    if not syntax_check["ok"]:
        blocked_reasons = [
            *blocked_reasons,
            {
                "path": str(syntax_check.get("path") or "*"),
                "reason_code": "typescript_syntax_or_typecheck_failed",
            },
        ]
    resolved_target = _resolve_requirement_target(
        preview_task_text,
        architect_plan=architect_plan,
        task_spec=task_spec_payload if isinstance(task_spec_payload, dict) else None,
    )
    requirement_coverage = _requirement_coverage(
        unified_diff,
        files,
        preview_task_text,
        explicit_target=resolved_target,
    )
    if not requirement_coverage["ok"]:
        path = _extract_explicit_target(preview_task_text) or "*"
        blocked_reasons = [
            *blocked_reasons,
            {
                "path": path,
                "reason_code": "requirement_coverage_failed",
            },
        ]
    review_report = None
    llm_review_report = None
    llm_review_skipped_reason = "no_architect_plan"
    if architect_plan is not None:
        review_report = review_diff_deterministically(architect_plan, unified_diff)
        if not review_report.passed:
            llm_review_skipped_reason = "deterministic_review_failed"
            blocked_reasons = [
                *blocked_reasons,
                *[
                    {
                        "path": finding.path,
                        "reason_code": f"review_{finding.id}",
                    }
                    for finding in review_report.findings
                ],
            ]
        elif architect_plan.classification.task_class not in {"implement", "refactor", "style"}:
            llm_review_skipped_reason = "task_class_not_reviewed"
        elif reviewer_llm_call is None and not reviewer_llm_is_configured():
            llm_review_skipped_reason = "reviewer_model_not_configured"
        else:
            llm_review_report = review_diff_with_llm(
                architect_plan,
                unified_diff,
                llm_call=reviewer_llm_call,
            )
            llm_review_skipped_reason = ""
    suggested_commands = _suggest_commands(files, test_command)
    manual_checks = _manual_checks(files, blocked_reasons)
    risk = _risk_level(files, blocked_reasons)
    status = "blocked" if blocked_reasons else "preview_ready"
    self_correction = _self_correction(status, risk, files, blocked_reasons)
    normalized_route = (route_type or "").strip().lower()
    next_action = (next_prompt_action or "").strip()
    file_writes_allowed = bool(
        LOCAL_ROUTE_DIFF_FILE_WRITES_AFTER_APPROVAL
        and not blocked_reasons
        and (normalized_route == "local_route" or next_action == "run_with_coder_agent")
    )

    payload: dict[str, Any] = {
        "tool": "diff_verification_preview",
        "access_scope": "read_only_diff_preview",
        "status": status,
        "risk": risk,
        "changed_files": files,
        "blocked_reasons": blocked_reasons,
        "self_correction": self_correction,
        "verification_plan": _verification_plan(
            status,
            suggested_commands,
            manual_checks,
            self_correction,
        ),
        "suggested_commands": suggested_commands,
        "manual_checks": manual_checks,
        "typescript_check": syntax_check,
        "task_spec_check": task_spec_check,
        "requirement_coverage": requirement_coverage,
        "review_report": review_report.to_dict()
        if review_report is not None
        else {"passed": True, "findings": [], "skipped": True},
        "llm_review_report": (
            llm_review_report.to_dict()
            if llm_review_report is not None
            else {
                "passed": True,
                "findings": [],
                "skipped": True,
                "reason": llm_review_skipped_reason,
            }
        ),
        "would_apply_diff": False,
        "would_execute": False,
        "requires_human_approval": bool(test_command),
        "limits": {
            "max_diff_bytes": MAX_DIFF_BYTES,
            "file_writes_allowed": file_writes_allowed,
            "terminal_execution_allowed": False,
            "secret_shaped_paths_allowed": False,
        },
    }

    apply_ok, apply_err = _lr.git_apply_check_for_preview(unified_diff, files)
    payload["git_apply_check_ok"] = apply_ok
    payload["git_apply_check_error"] = apply_err
    deterministic_result = deterministic_checks_from_preview(
        apply_ok=apply_ok,
        apply_error=apply_err,
        files=files,
        syntax_check=syntax_check,
        unified_diff=unified_diff,
    )
    payload["deterministic_checks"] = deterministic_result.as_payload()
    checks = list(payload["deterministic_checks"])
    checks.append(
        {
            "tier": 1,
            "id": "task_spec_allowed_files",
            "status": "passed" if task_spec_check["ok"] else "failed",
            "duration_ms": 0,
            "output": _task_spec_check_summary(task_spec_check),
            "blocking": True,
        }
    )
    payload["deterministic_checks"] = checks
    if review_report is not None:
        checks = list(payload["deterministic_checks"])
        checks.append(
            {
                "tier": 1,
                "id": "architect_plan_review",
                "status": "passed" if review_report.passed else "failed",
                "duration_ms": 0,
                "output": "Architect plan reviewer passed."
                if review_report.passed
                else "; ".join(
                    f"{finding.id}: {finding.details}"
                    for finding in review_report.findings[:8]
                ),
                "blocking": True,
            }
        )
        payload["deterministic_checks"] = checks
    if llm_review_report is not None:
        checks = list(payload["deterministic_checks"])
        checks.append(
            {
                "tier": 2,
                "id": "llm_reviewer",
                "status": "passed" if llm_review_report.passed else "advisory",
                "duration_ms": 0,
                "output": "LLM reviewer passed."
                if llm_review_report.passed
                else "; ".join(
                    f"{finding.id}: {finding.details}"
                    for finding in llm_review_report.findings[:8]
                ),
                "blocking": False,
            }
        )
        payload["deterministic_checks"] = checks
    if not apply_ok:
        br = list(payload["blocked_reasons"] or [])
        br.append({"path": "*", "reason_code": "diff_apply_check_failed"})
        payload["blocked_reasons"] = br
        payload["status"] = "blocked"
        lim = dict(payload["limits"])
        lim["file_writes_allowed"] = False
        payload["limits"] = lim

    if payload["status"] == "blocked":
        lim = dict(payload["limits"])
        lim["file_writes_allowed"] = False
        payload["limits"] = lim

    return payload


def _parse_changed_files(unified_diff: str) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    current_path: str | None = None
    old_path_was_dev_null = False

    for raw_line in unified_diff.splitlines():
        line = raw_line.rstrip("\n")
        if line.startswith("diff --git "):
            parts = _diff_git_paths(line)
            if len(parts) >= 2:
                current_path = _normalize_diff_path(parts[1]) or _normalize_diff_path(parts[0])
                old_path_was_dev_null = False
                if current_path:
                    _ensure_record(records, current_path)
            continue

        if line.startswith("+++ "):
            raw_path = line[4:].strip()
            path = _normalize_diff_path(raw_path)
            if path:
                current_path = path
                record = _ensure_record(records, current_path)
                record["change_type"] = "added" if old_path_was_dev_null else "modified"
            elif raw_path == "/dev/null" and current_path:
                records[current_path]["change_type"] = "deleted"
            continue

        if line.startswith("--- "):
            raw_path = line[4:].strip()
            old_path_was_dev_null = raw_path == "/dev/null"
            path = _normalize_diff_path(raw_path)
            if path:
                current_path = path
                _ensure_record(records, current_path)
            continue

        if line.startswith("@@"):
            continue

        if current_path and line.startswith("+") and not line.startswith("+++"):
            records[current_path]["added_lines"] += 1
            if records[current_path]["change_type"] == "unknown":
                records[current_path]["change_type"] = "modified"
            continue

        if current_path and line.startswith("-") and not line.startswith("---"):
            records[current_path]["removed_lines"] += 1
            if records[current_path]["change_type"] == "unknown":
                records[current_path]["change_type"] = "modified"

    for record in records.values():
        path = record["path"]
        if record["change_type"] == "unknown":
            record["change_type"] = "modified"
        if record["added_lines"] > 0 and record["removed_lines"] == 0 and record["change_type"] == "deleted":
            record["change_type"] = "added"
        record["extension"] = PurePosixPath(path).suffix.lower()
        record["risk_flags"] = _file_risk_flags(path)

    return list(records.values())


IMPLEMENTATION_TASK_SPEC_TYPES = {
    "modify_existing_file",
    "create_new_file",
    "delete_file",
}
NON_WRITE_TASK_SPEC_TYPES = {
    "target_unresolved",
    "analyze_only",
    "unsupported",
}


def task_spec_diff_check(
    task_spec: dict[str, Any] | None,
    changed_files: list[dict[str, Any]],
) -> dict[str, Any]:
    changed = _dedupe_paths(
        [
            _normalize_task_spec_path(str(file.get("path") or ""))
            for file in changed_files
            if isinstance(file, dict)
        ]
    )
    if task_spec is None:
        return {
            "ok": True,
            "reason_codes": [],
            "allowed_files": [],
            "forbidden_files": [],
            "changed_files": changed,
            "skipped": True,
            "summary": "No TaskSpec supplied for this legacy preview path.",
        }

    task_type = str(task_spec.get("task_type") or task_spec.get("taskType") or "").strip()
    target = _normalize_task_spec_path(
        str(task_spec.get("target") or "") if task_spec.get("target") is not None else ""
    )
    allowed = _dedupe_paths(
        _normalize_task_spec_path(str(item))
        for item in _task_spec_list(task_spec, "allowed_files", "allowedFiles")
    )
    forbidden = _dedupe_paths(
        _normalize_task_spec_path(str(item))
        for item in _task_spec_list(task_spec, "forbidden_files", "forbiddenFiles")
    )
    reason_codes: list[str] = []

    if task_type == "target_unresolved":
        reason_codes.append("task_spec_target_unresolved")
    elif task_type == "analyze_only":
        reason_codes.append("task_spec_analyze_only")
    elif task_type == "unsupported":
        reason_codes.append("task_spec_unsupported")
    elif task_type in IMPLEMENTATION_TASK_SPEC_TYPES:
        if not allowed:
            reason_codes.append("task_spec_missing_allowed_files")
        outside_allowed = [path for path in changed if allowed and path not in allowed]
        if outside_allowed:
            reason_codes.append("task_spec_allowed_file_violation")
        if target and changed and target not in changed:
            reason_codes.append("task_spec_target_mismatch")
    elif task_type:
        reason_codes.append("task_spec_unsupported")

    forbidden_changed = [path for path in changed if path and path in forbidden]
    if forbidden_changed:
        reason_codes.append("task_spec_forbidden_file_violation")

    reason_codes = list(dict.fromkeys(reason_codes))
    return {
        "ok": not reason_codes,
        "reason_codes": reason_codes,
        "allowed_files": allowed,
        "forbidden_files": forbidden,
        "changed_files": changed,
        "target": target or None,
        "task_type": task_type or None,
        "summary": "TaskSpec check passed." if not reason_codes else "; ".join(reason_codes),
        "violations": {
            "outside_allowed": [path for path in changed if allowed and path not in allowed],
            "forbidden": forbidden_changed,
        },
    }


def _task_spec_payload_for_preview(
    *,
    architect_plan: ArchitectPlan | None,
    task_spec: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if task_spec is not None:
        return task_spec
    if architect_plan is None:
        return None
    return task_spec_from_plan(architect_plan).to_dict()


def _task_spec_blocked_reason_pairs(task_spec_check: dict[str, Any]) -> list[tuple[str, str]]:
    changed = [
        str(path)
        for path in task_spec_check.get("changed_files", [])
        if isinstance(path, str)
    ]
    target = str(task_spec_check.get("target") or "")
    violations = (
        task_spec_check.get("violations")
        if isinstance(task_spec_check.get("violations"), dict)
        else {}
    )
    outside_allowed = [
        str(path)
        for path in violations.get("outside_allowed", [])
        if isinstance(path, str)
    ]
    forbidden = [
        str(path)
        for path in violations.get("forbidden", [])
        if isinstance(path, str)
    ]
    pairs: list[tuple[str, str]] = []
    for code in task_spec_check.get("reason_codes", []):
        reason_code = str(code)
        paths = changed or ["*"]
        if reason_code == "task_spec_allowed_file_violation" and outside_allowed:
            paths = outside_allowed
        elif reason_code == "task_spec_forbidden_file_violation" and forbidden:
            paths = forbidden
        elif reason_code == "task_spec_target_mismatch" and target:
            paths = [target]
        elif reason_code in {
            "task_spec_missing_allowed_files",
            "task_spec_target_unresolved",
            "task_spec_analyze_only",
            "task_spec_unsupported",
        }:
            paths = [target or "*"]
        for path in paths:
            pairs.append((reason_code, path))
    return list(dict.fromkeys(pairs))


def _task_spec_check_summary(task_spec_check: dict[str, Any]) -> str:
    if task_spec_check.get("skipped"):
        return str(task_spec_check.get("summary") or "TaskSpec check skipped.")
    if task_spec_check.get("ok"):
        changed = ", ".join(str(path) for path in task_spec_check.get("changed_files", []))
        allowed = ", ".join(str(path) for path in task_spec_check.get("allowed_files", []))
        return f"TaskSpec allowed-files check passed. changed=[{changed}] allowed=[{allowed}]"
    return (
        "TaskSpec blocked this diff because it touches files outside the allowed list."
        if "task_spec_allowed_file_violation" in task_spec_check.get("reason_codes", [])
        else str(task_spec_check.get("summary") or "TaskSpec check failed.")
    )


def _task_spec_list(
    task_spec: dict[str, Any],
    snake_key: str,
    camel_key: str,
) -> list[str]:
    value = task_spec.get(snake_key)
    if not isinstance(value, list):
        value = task_spec.get(camel_key)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str)]


def _dedupe_paths(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        path = _normalize_task_spec_path(str(value))
        if not path or path in seen:
            continue
        seen.add(path)
        result.append(path)
    return result


def _clean_repo_path(raw_path: str, *, strip_diff_prefix: bool) -> str:
    path = raw_path.strip().strip('"').strip("'").replace("\\", "/")
    if "\t" in path:
        path = path.split("\t", 1)[0].strip()
    path = re.sub(
        r"\s+\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\s+[+-]\d{4})?)?$",
        "",
        path,
    ).strip()
    if path in {"", "/dev/null", "dev/null", "a/dev/null", "b/dev/null"}:
        return ""
    if strip_diff_prefix and (path.startswith("a/") or path.startswith("b/")):
        path = path[2:]
    while path.startswith("./"):
        path = path[2:]
    while path and path[-1] in ".,:;!?":
        candidate = path[:-1]
        if PurePosixPath(candidate).suffix:
            path = candidate
            continue
        break
    return _remove_current_directory_segments(path)


def _remove_current_directory_segments(path: str) -> str:
    from source_proxy.safety.paths import strip_trailing_slash_for_repo_files

    if not path:
        return ""
    absolute = path.startswith("/")
    trailing_slash = path.endswith("/") and path != "/"
    parts = [part for part in path.split("/") if part and part != "."]
    normalized = "/".join(parts)
    if absolute:
        normalized = f"/{normalized}"
    if trailing_slash and normalized and not normalized.endswith("/"):
        normalized = f"{normalized}/"
    return strip_trailing_slash_for_repo_files(normalized)


def _normalize_task_spec_path(raw_path: str) -> str:
    return _clean_repo_path(raw_path, strip_diff_prefix=False)


def _ensure_record(records: dict[str, dict[str, Any]], path: str) -> dict[str, Any]:
    if path not in records:
        records[path] = {
            "path": path,
            "extension": PurePosixPath(path).suffix.lower(),
            "change_type": "unknown",
            "added_lines": 0,
            "removed_lines": 0,
            "risk_flags": _file_risk_flags(path),
        }
    return records[path]


def _normalize_diff_path(raw_path: str) -> str | None:
    path = _clean_repo_path(raw_path, strip_diff_prefix=True)
    if not path:
        return None
    return path or None


def _diff_git_paths(line: str) -> list[str]:
    body = line.removeprefix("diff --git ").strip()
    matches = re.findall(r'"((?:\\.|[^"])*)"', body)
    if len(matches) >= 2:
        return [match.replace(r"\"", '"') for match in matches[:2]]
    return body.split()


def _blocked_reasons(files: list[dict[str, Any]]) -> list[dict[str, str]]:
    reasons: list[dict[str, str]] = []
    for file in files:
        path = str(file["path"])
        flags = set(file["risk_flags"])
        if "path_escape" in flags:
            reasons.append({"path": path, "reason_code": "path_escape"})
            reasons.append({"path": path, "reason_code": "outside_workspace"})
        if "absolute_path" in flags:
            reasons.append({"path": path, "reason_code": "absolute_path"})
            reasons.append({"path": path, "reason_code": "path_escape"})
            reasons.append({"path": path, "reason_code": "outside_workspace"})
        if "encoded_path_not_allowed" in flags:
            reasons.append({"path": path, "reason_code": "encoded_path_not_allowed"})
        if "secret_shaped_path" in flags:
            reasons.append({"path": path, "reason_code": "secret_shaped_path"})
            reasons.append({"path": path, "reason_code": "protected_path"})
    return [dict(item) for item in dict.fromkeys(tuple(item.items()) for item in reasons)]


def _file_risk_flags(path: str) -> list[str]:
    flags: list[str] = []
    normalized = path.replace("\\", "/").lower()
    parts = [part for part in normalized.split("/") if part]

    if path.startswith("/") or (len(path) >= 3 and path[1:3] == ":/"):
        flags.append("absolute_path")
    if has_percent_encoded_path_syntax(path):
        flags.append("encoded_path_not_allowed")
    if ".." in parts:
        flags.append("path_escape")
    if any(part.startswith(".") or any(marker in part for marker in SECRET_NAME_MARKERS) for part in parts):
        flags.append("secret_shaped_path")
    if parts and (parts[-1] in HIGH_RISK_EXACT_NAMES or normalized.startswith(HIGH_RISK_PREFIXES)):
        flags.append("high_impact_file")
    return flags


def _suggest_commands(files: list[dict[str, Any]], test_command: list[str] | None) -> list[dict[str, Any]]:
    paths = [str(file["path"]) for file in files]
    extensions = {str(file["extension"]) for file in files}
    commands: list[dict[str, Any]] = []

    if extensions & {".ts", ".tsx", ".js", ".jsx"}:
        commands.append(
            {
                "command": ["npm", "run", "typecheck"],
                "reason": "TypeScript or JavaScript files changed.",
                "requires_human_approval": True,
            }
        )
        lint_targets = [path for path in paths if PurePosixPath(path).suffix.lower() in {".ts", ".tsx", ".js", ".jsx"}]
        commands.append(
            {
                "command": ["npx", "eslint", *lint_targets[:20]],
                "reason": "Lint changed frontend/source files.",
                "requires_human_approval": True,
            }
        )

    if ".py" in extensions:
        py_targets = [path for path in paths if PurePosixPath(path).suffix.lower() == ".py"]
        commands.append(
            {
                "command": ["python", "-m", "py_compile", *py_targets[:20]],
                "reason": "Python files changed.",
                "requires_human_approval": True,
            }
        )
        if any(path.startswith("source_proxy/tests/") for path in py_targets):
            commands.append(
                {
                    "command": ["python", "-m", "unittest"],
                    "reason": "Python tests changed.",
                    "requires_human_approval": True,
                }
            )

    if any(PurePosixPath(path).name in HIGH_RISK_EXACT_NAMES for path in paths):
        commands.append(
            {
                "command": ["npm", "run", "build"],
                "reason": "Project configuration or dependency files changed.",
                "requires_human_approval": True,
            }
        )

    if test_command:
        commands.append(
            {
                "command": test_command,
                "reason": "Caller requested this verification command.",
                "requires_human_approval": True,
            }
        )

    return commands


def _manual_checks(files: list[dict[str, Any]], blocked_reasons: list[dict[str, str]]) -> list[str]:
    if blocked_reasons:
        return ["Narrow or remove blocked paths before applying the diff."]

    checks = ["Review the changed file list before applying the diff."]
    if any(str(file["path"]).startswith("src/app/") for file in files):
        checks.append("Load the affected Next.js route and check the browser console.")
    if any(str(file["path"]).startswith("source_proxy/") for file in files):
        checks.append("Exercise the affected proxy endpoint with curl after tests pass.")
    if any("high_impact_file" in file["risk_flags"] for file in files):
        checks.append("Confirm configuration or dependency changes are intentional.")
    return checks


def _verification_plan(
    status: str,
    suggested_commands: list[dict[str, Any]],
    manual_checks: list[str],
    self_correction: dict[str, Any],
) -> list[str]:
    if status == "blocked":
        return [
            "Do not apply this diff yet.",
            self_correction["safer_next_action"],
            "Resolve the blocked path findings.",
            *manual_checks,
        ]

    plan = ["Review changed files and risk flags.", "Apply the diff only after approval."]
    if self_correction["triggered"]:
        plan.append(self_correction["safer_next_action"])
    if suggested_commands:
        plan.append("Run suggested commands in an approved sandbox/tool layer.")
    plan.extend(manual_checks)
    return plan


def _risk_level(files: list[dict[str, Any]], blocked_reasons: list[dict[str, str]]) -> str:
    if blocked_reasons:
        return "blocked"
    if any("high_impact_file" in file["risk_flags"] for file in files):
        return "high"
    if len(files) > 8:
        return "medium"
    return "low"


def _self_correction(
    status: str,
    risk: str,
    files: list[dict[str, Any]],
    blocked_reasons: list[dict[str, str]],
) -> dict[str, Any]:
    reasons: list[str] = []
    if status == "blocked":
        reasons.extend(
            f"{reason['path']} was blocked for {reason['reason_code']}."
            for reason in blocked_reasons
        )
    if risk == "high":
        high_impact_paths = [
            str(file["path"])
            for file in files
            if "high_impact_file" in file["risk_flags"]
        ]
        reasons.append(
            "High-impact files changed: "
            + (", ".join(high_impact_paths) if high_impact_paths else "unknown")
            + "."
        )
    if risk == "medium":
        reasons.append("The diff touches more than eight files and should be split.")

    triggered = status == "blocked" or risk in {"high", "medium"}
    if not triggered:
        return {
            "triggered": False,
            "severity": "none",
            "reasons": [],
            "safer_next_action": "Continue with normal review and approved verification commands.",
            "retry_prompt": "",
        }

    severity = "blocked" if status == "blocked" else risk
    reason_codes = {reason["reason_code"] for reason in blocked_reasons}
    safer_next_action = _safer_next_action(status, risk, reason_codes)
    retry_prompt = _retry_prompt(status, risk, reasons)

    return {
        "triggered": True,
        "severity": severity,
        "reasons": reasons,
        "safer_next_action": safer_next_action,
        "retry_prompt": retry_prompt,
    }


def _safer_next_action(status: str, risk: str, reason_codes: set[str] | None = None) -> str:
    reason_codes = reason_codes or set()
    if "requirement_coverage_failed" in reason_codes:
        return "Ask the next agent to regenerate the patch with the missing exact requirements included."
    if "typescript_syntax_or_typecheck_failed" in reason_codes:
        return "Ask the next agent to regenerate syntactically valid TypeScript or TSX."
    if status == "blocked":
        return "Ask the next agent to regenerate the patch without blocked paths or secret-shaped files."
    if risk == "high":
        return "Ask for a smaller patch or explicit approval before touching high-impact configuration or proxy files."
    if risk == "medium":
        return "Split the diff into smaller reviewable patches before applying."
    return "Continue with normal review and approved verification commands."


def _retry_prompt(status: str, risk: str, reasons: list[str]) -> str:
    return "\n".join(
        [
            "Revise the proposed diff before implementation.",
            f"Current status: {status}",
            f"Current risk: {risk}",
            "Reasons:",
            *(f"- {reason}" for reason in reasons),
            "Return a smaller unified diff that avoids blocked paths, preserves existing behavior, and lists the tests to run.",
        ]
    )
