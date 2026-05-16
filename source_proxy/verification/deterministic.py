from __future__ import annotations

import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal


DeterministicStatus = Literal["passed", "failed", "skipped", "timeout"]


@dataclass(frozen=True)
class DeterministicCheckResult:
    tier: int
    id: str
    status: DeterministicStatus
    duration_ms: int
    output: str
    blocking: bool = True

    def as_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DeterministicVerificationResult:
    checks: list[DeterministicCheckResult]

    @property
    def passed(self) -> bool:
        return all(
            check.status in {"passed", "skipped"} or not check.blocking
            for check in self.checks
        )

    def as_payload(self) -> list[dict[str, Any]]:
        return [check.as_payload() for check in self.checks]


def deterministic_checks_from_preview(
    *,
    apply_ok: bool,
    apply_error: str,
    files: list[dict[str, Any]],
    syntax_check: dict[str, Any],
    unified_diff: str,
) -> DeterministicVerificationResult:
    """Expose the existing preview checks as the Phase 8.3 tiered contract."""
    checks: list[DeterministicCheckResult] = [
        DeterministicCheckResult(
            tier=1,
            id="git_apply_check",
            status="passed" if apply_ok else "failed",
            duration_ms=0,
            output="git apply --check passed." if apply_ok else _cap_output(apply_error),
        ),
        DeterministicCheckResult(
            tier=1,
            id="syntax_parse",
            status=(
                "skipped"
                if syntax_check.get("skipped") is True
                else "passed"
                if syntax_check.get("ok") is True
                else "failed"
            ),
            duration_ms=0,
            output=_cap_output(str(syntax_check.get("summary") or "")),
        ),
    ]
    tier1_passed = all(check.status in {"passed", "skipped"} for check in checks)
    ts_js_changed = _has_ts_js_change(files)
    type_affecting = _diff_touches_type_surface(unified_diff)
    checks.append(
        DeterministicCheckResult(
            tier=2,
            id="eslint_typecheck",
            status="skipped",
            duration_ms=0,
            output=(
                "Skipped because tier 1 failed."
                if not tier1_passed
                else "Skipped because no TS/JS files changed."
                if not ts_js_changed
                else "Use suggested_commands for lint/typecheck until sandboxed tier-2 execution is enabled."
            ),
            blocking=False,
        )
    )
    checks.append(
        DeterministicCheckResult(
            tier=3,
            id="full_project_typecheck",
            status="skipped",
            duration_ms=0,
            output=(
                "Skipped because no exported type/class/function surface changed."
                if not type_affecting
                else "Slow path required; run full project typecheck before approval if this warning appears."
            ),
            blocking=False,
        )
    )
    return DeterministicVerificationResult(checks=checks)


def run_deterministic_checks(
    diff: str,
    target_path: str,
    workspace_root: Path,
) -> DeterministicVerificationResult:
    """Standalone deterministic verification entry point for future orchestrator use.

    The preview endpoint currently reports the same tier shape through
    `deterministic_checks_from_preview` so it can reuse its already-sandboxed apply
    and syntax checks. This function is kept side-effect-free: it never modifies the
    workspace and caps command output.
    """
    checks: list[DeterministicCheckResult] = []
    checks.append(_run_git_apply_check(diff, workspace_root))
    if checks[-1].status != "passed":
        checks.extend(_skipped_upper_tiers("Skipped because git apply --check failed."))
        return DeterministicVerificationResult(checks=checks)

    suffix = Path(target_path).suffix.lower()
    if suffix in {".js", ".jsx", ".ts", ".tsx"}:
        checks.append(_run_node_syntax_check(target_path, workspace_root))
    elif suffix == ".py":
        checks.append(_run_python_syntax_check(target_path, workspace_root))
    else:
        checks.append(
            DeterministicCheckResult(
                tier=1,
                id="syntax_parse",
                status="skipped",
                duration_ms=0,
                output=f"No syntax parser configured for {suffix or 'extensionless'} files.",
            )
        )

    if any(check.status == "failed" for check in checks if check.tier == 1):
        checks.extend(_skipped_upper_tiers("Skipped because tier 1 failed."))
        return DeterministicVerificationResult(checks=checks)

    checks.append(
        DeterministicCheckResult(
            tier=2,
            id="eslint_typecheck",
            status="skipped",
            duration_ms=0,
            output="Use preview suggested_commands for lint/typecheck until sandboxed tier-2 execution is enabled.",
            blocking=False,
        )
    )
    checks.append(
        DeterministicCheckResult(
            tier=3,
            id="full_project_typecheck",
            status="skipped",
            duration_ms=0,
            output="Skipped unless the diff touches exported type/class/function declarations.",
            blocking=False,
        )
    )
    return DeterministicVerificationResult(checks=checks)


def _skipped_upper_tiers(output: str) -> list[DeterministicCheckResult]:
    return [
        DeterministicCheckResult(
            tier=2,
            id="eslint_typecheck",
            status="skipped",
            duration_ms=0,
            output=output,
            blocking=False,
        ),
        DeterministicCheckResult(
            tier=3,
            id="full_project_typecheck",
            status="skipped",
            duration_ms=0,
            output=output,
            blocking=False,
        ),
    ]


def _run_git_apply_check(diff: str, workspace_root: Path) -> DeterministicCheckResult:
    started = time.perf_counter()
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        suffix=".patch",
        delete=False,
    ) as patch_file:
        patch_file.write(diff)
        patch_path = Path(patch_file.name)
    try:
        result = subprocess.run(
            ["git", "apply", "--check", str(patch_path)],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except subprocess.TimeoutExpired as error:
        return _command_result("git_apply_check", 1, "timeout", started, str(error))
    finally:
        patch_path.unlink(missing_ok=True)
    status: DeterministicStatus = "passed" if result.returncode == 0 else "failed"
    output = result.stderr or result.stdout or "git apply --check passed."
    return _command_result("git_apply_check", 1, status, started, output)


def _run_node_syntax_check(target_path: str, workspace_root: Path) -> DeterministicCheckResult:
    target = workspace_root / target_path
    if not target.is_file():
        return DeterministicCheckResult(
            tier=1,
            id="syntax_parse",
            status="skipped",
            duration_ms=0,
            output=f"{target_path} does not exist on disk for standalone syntax parsing.",
        )
    started = time.perf_counter()
    result = subprocess.run(
        ["node", "--check", str(target)],
        cwd=workspace_root,
        capture_output=True,
        text=True,
        timeout=3,
    )
    status: DeterministicStatus = "passed" if result.returncode == 0 else "failed"
    return _command_result(
        "syntax_parse",
        1,
        status,
        started,
        result.stderr or result.stdout or "node --check passed.",
    )


def _run_python_syntax_check(target_path: str, workspace_root: Path) -> DeterministicCheckResult:
    target = workspace_root / target_path
    if not target.is_file():
        return DeterministicCheckResult(
            tier=1,
            id="syntax_parse",
            status="skipped",
            duration_ms=0,
            output=f"{target_path} does not exist on disk for standalone syntax parsing.",
        )
    started = time.perf_counter()
    result = subprocess.run(
        ["python", "-m", "py_compile", str(target)],
        cwd=workspace_root,
        capture_output=True,
        text=True,
        timeout=3,
    )
    status: DeterministicStatus = "passed" if result.returncode == 0 else "failed"
    return _command_result(
        "syntax_parse",
        1,
        status,
        started,
        result.stderr or result.stdout or "py_compile passed.",
    )


def _command_result(
    check_id: str,
    tier: int,
    status: DeterministicStatus,
    started: float,
    output: str,
) -> DeterministicCheckResult:
    return DeterministicCheckResult(
        tier=tier,
        id=check_id,
        status=status,
        duration_ms=max(0, round((time.perf_counter() - started) * 1000)),
        output=_cap_output(output),
    )


def _cap_output(output: str, limit: int = 4096) -> str:
    text = (output or "").strip()
    return text[:limit]


def _has_ts_js_change(files: list[dict[str, Any]]) -> bool:
    return any(
        str(file.get("extension") or "").lower() in {".ts", ".tsx", ".js", ".jsx"}
        and str(file.get("change_type") or "").lower() != "deleted"
        for file in files
    )


def _diff_touches_type_surface(diff: str) -> bool:
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        stripped = line[1:].strip()
        if stripped.startswith(("export ", "interface ", "type ", "class ", "enum ")):
            return True
        if stripped.startswith("function ") and "<" in stripped:
            return True
    return False
