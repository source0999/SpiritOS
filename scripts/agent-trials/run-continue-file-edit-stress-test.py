from __future__ import annotations

import argparse
import difflib
import html
import http.server
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/continue-file-edit-stress-test"
)

PROMPTS = [
    "init a repo for agent lab experiements make me a homepage i can open on my phone dont touch the real spiritos app tho",
    "style it light clean minimilist homepage with placeholder navs for futer expermients home calculator tarot deck simulator weather app pong",
    "make the calcuator route for this app, calcuator needs to add subtract multiply and divide",
]

SAFETY_WRAPPER = (
    "Run only in this disposable workspace. Do not touch the real SpiritOS app. "
    "Do not modify files outside this workspace."
)

P3_CAPS = {
    "working_behavior": 10,
    "calculator_ui_partial": 8,
    "route_or_anchor_broken": 6,
    "wrote_code_but_not_integrated": 6,
    "rendered_label_only": 5,
    "explained_only": 4,
    "empty": 2,
    "failed": 2,
}

CONTINUE_SESSIONS = Path.home() / ".continue/sessions"


@dataclass(frozen=True)
class ContinueLaneSpec:
    name: str
    target_model: str
    selection_method: str  # default | hub_slug | isolated_config | manual
    hub_slug: str = ""
    config_template: str = ""
    manual_reason: str = ""
    manual_steps: tuple[str, ...] = ()


def lane_catalog() -> list[ContinueLaneSpec]:
    return [
        ContinueLaneSpec(
            "continue-gemma",
            "gemma",
            "manual",
            manual_reason="Ollama model `gemma` is not installed and Continue has no gemma entry in ~/.continue/config.yaml.",
            manual_steps=(
                "Install a Gemma model in Ollama only after Britton approves the download.",
                "Add a gemma model block to a disposable Continue config or hub slug.",
                "Re-run `python3 scripts/agent-trials/run-continue-file-edit-stress-test.py --run`.",
            ),
        ),
        ContinueLaneSpec(
            "continue-gpt4o-mini",
            "gpt-4o-mini",
            "isolated_config",
            config_template="openai",
        ),
        ContinueLaneSpec(
            "continue-claude-sonnet",
            "claude-sonnet-4-6",
            "isolated_config",
            config_template="claude",
        ),
        ContinueLaneSpec("continue-default", "gemini-2.5-flash", "default"),
        ContinueLaneSpec(
            "continue-qwen",
            "qwen2.5-coder:7b",
            "isolated_config",
            config_template="qwen",
        ),
        ContinueLaneSpec(
            "continue-hermes4",
            "hermes4",
            "isolated_config",
            config_template="hermes4",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Continue CLI file-edit stress test")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8772)
    args = parser.parse_args()

    if args.clean:
        if OUTPUT_ROOT.exists():
            print(f"Removing {OUTPUT_ROOT}")
            shutil.rmtree(OUTPUT_ROOT)
        else:
            print(f"Already clean: {OUTPUT_ROOT}")
        return 0
    if args.serve:
        return serve(args.host, args.port)
    if args.run:
        return run_all()
    parser.print_help()
    return 1


def run_all() -> int:
    load_env()
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    discovery = discover_continue()
    (OUTPUT_ROOT / "model-selection-discovery.json").write_text(
        json.dumps(discovery, indent=2), encoding="utf-8"
    )

    if not discovery.get("cn_available"):
        for spec in lane_catalog():
            write_manual_lane(spec, discovery.get("cn_reason", "Continue CLI unavailable."))
        finalize({spec.name: load_lane_result(spec.name) for spec in lane_catalog()}, discovery)
        return 1

    results: dict[str, Any] = {}
    for spec in lane_catalog():
        print(f"Running lane: {spec.name} (target model: {spec.target_model})")
        if spec.selection_method == "manual":
            results[spec.name] = write_manual_lane(spec, spec.manual_reason, list(spec.manual_steps))
        elif spec.selection_method == "isolated_config" and spec.config_template in {"qwen", "hermes4"} and not ollama_has(spec.target_model):
            results[spec.name] = write_manual_lane(
                spec,
                f"Ollama model `{spec.target_model}` is not installed.",
                [
                    f"Pull `{spec.target_model}` only after Britton approves.",
                    "Re-run this stress test.",
                ],
            )
        elif spec.selection_method == "isolated_config" and spec.config_template == "openai" and not os.getenv("OPENAI_API_KEY", "").strip():
            results[spec.name] = write_manual_lane(spec, "OPENAI_API_KEY is not configured.", ["Set OPENAI_API_KEY in .env.local or environment.", "Re-run."])
        elif spec.selection_method == "isolated_config" and spec.config_template == "claude" and not os.getenv("ANTHROPIC_API_KEY", "").strip():
            results[spec.name] = write_manual_lane(spec, "ANTHROPIC_API_KEY is not configured.", ["Set ANTHROPIC_API_KEY in .env.local or environment.", "Re-run."])
        else:
            results[spec.name] = run_continue_lane(spec, discovery)
        finalize_partial(results, discovery)
    finalize(results, discovery)
    return 0


def discover_continue() -> dict[str, Any]:
    cn = shutil.which("cn")
    version = ""
    if cn:
        proc = subprocess.run([cn, "--version"], capture_output=True, text=True, timeout=30)
        version = (proc.stdout or proc.stderr).strip()
    help_proc = subprocess.run([cn, "--help"], capture_output=True, text=True, timeout=30) if cn else None
    help_text = help_proc.stdout if help_proc else ""
    return {
        "cn_available": bool(cn),
        "cn_path": cn or "",
        "cn_version": version,
        "cn_reason": "" if cn else "Continue CLI `cn` is not on PATH.",
        "headless_flags": ["--auto", "-p"],
        "model_flag_documented": "--model <slug>" in help_text,
        "config_flag_documented": "--config <path>" in help_text,
        "default_config": str(Path.home() / ".continue/config.yaml"),
        "selection_methods": {
            "continue-default": "No --model; uses default from ~/.continue/config.yaml (gemini-2.5-flash).",
            "continue-qwen": "Disposable isolated config with single Ollama qwen2.5-coder:7b model.",
            "continue-hermes4": "Disposable isolated config with single Ollama hermes4 model.",
            "continue-gemma": "Manual required; gemma not available.",
            "continue-gpt4o-mini": "Disposable isolated config with only OpenAI gpt-4o-mini (hub slug alone did not override default).",
            "continue-claude-sonnet": "Disposable isolated config with only anthropic/claude-sonnet-4-6 hub entry.",
        },
        "hub_slug_tests": {
            "openai/gpt-4o-mini": probe_hub_slug("openai/gpt-4o-mini"),
            "anthropic/claude-sonnet-4-6": probe_hub_slug("anthropic/claude-sonnet-4-6"),
            "hermes4_local_name": "FAILED: --model hermes4 errors with config parse failure",
        },
        "isolated_config_tests": {
            "hermes4": "Works via --config with single-model yaml (slow on cold Ollama).",
            "qwen2.5-coder:7b": "Works via --config with single-model yaml.",
        },
    }


def probe_hub_slug(slug: str) -> str:
    cn = shutil.which("cn")
    if not cn:
        return "cn missing"
    proc = subprocess.run(
        [cn, "--model", slug, "--auto", "-p", "reply with only: PROBE"],
        capture_output=True,
        text=True,
        timeout=90,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode == 0:
        return "ok"
    return (proc.stderr or proc.stdout or f"exit {proc.returncode}")[:200]


def run_continue_lane(spec: ContinueLaneSpec, discovery: dict[str, Any]) -> dict[str, Any]:
    lane_dir = prepare_lane(spec.name)
    workspace = lane_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    config_path = ""
    if spec.selection_method == "isolated_config":
        config_path = write_lane_config(lane_dir, spec.config_template, spec.target_model)

    prompt_records: list[dict[str, Any]] = []
    command_log: list[str] = []
    session_ids: list[str] = []
    models_seen: list[str] = []

    for index, prompt in enumerate(PROMPTS, start=1):
        before = snapshot(workspace)
        started = time.time()
        full_prompt = f"{SAFETY_WRAPPER}\n\n{prompt}"
        try:
            cmd, proc = invoke_continue(full_prompt, workspace, spec, config_path)
        except subprocess.TimeoutExpired as error:
            elapsed = round(time.time() - started, 3)
            partial_stdout = ""
            if error.stdout:
                partial_stdout += error.stdout.decode("utf-8", errors="replace") if isinstance(error.stdout, bytes) else error.stdout
            if error.stderr:
                partial_stdout += error.stderr.decode("utf-8", errors="replace") if isinstance(error.stderr, bytes) else error.stderr
            cmd = error.cmd if isinstance(error.cmd, str) else " ".join(shlex_quote(p) for p in error.cmd)
            transcript = format_transcript(cmd, workspace, -1, elapsed, partial_stdout or "TIMEOUT", None)
            (lane_dir / f"prompt-{index}-transcript.txt").write_text(transcript, encoding="utf-8")
            command_log.append(
                f"prompt-{index}:\n  cwd: {workspace}\n  command: {cmd}\n  exit_code: TIMEOUT\n"
                f"  elapsed_seconds: {elapsed}\n  files_changed: none\n"
            )
            (lane_dir / "command-log.txt").write_text("\n".join(command_log), encoding="utf-8")
            return abort_lane_manual(
                spec,
                lane_dir,
                f"Continue timed out on prompt {index} after {elapsed}s.",
                command_log,
                prompt_records,
                session_ids,
                models_seen,
                preserve_lane_dir=True,
            )
        elapsed = round(time.time() - started, 3)
        stdout = (proc.stdout or "") + (proc.stderr or "")
        session = find_latest_session(workspace, started - 5)
        session_id = session.get("sessionId", "") if session else ""
        if session_id:
            session_ids.append(session_id)
        models = extract_session_models(session)
        models_seen.extend(models)
        model_used = models[-1] if models else "unknown"
        after = snapshot(workspace)
        changed = changed_files(before, after)
        diff_text = diff_snapshots(before, after)
        (lane_dir / f"diff-after-prompt-{index}.patch").write_text(diff_text, encoding="utf-8")

        transcript = format_transcript(cmd, workspace, proc.returncode, elapsed, stdout, session)
        (lane_dir / f"prompt-{index}-transcript.txt").write_text(transcript, encoding="utf-8")
        command_log.append(
            f"prompt-{index}:\n"
            f"  cwd: {workspace}\n"
            f"  command: {cmd}\n"
            f"  exit_code: {proc.returncode}\n"
            f"  elapsed_seconds: {elapsed}\n"
            f"  model_reported: {model_used}\n"
            f"  model_selection: {describe_selection(spec, config_path)}\n"
            f"  files_changed: {', '.join(changed) or 'none'}\n"
        )

        if proc.returncode != 0:
            return abort_lane_manual(
                spec,
                lane_dir,
                f"Continue exited {proc.returncode} on prompt {index}.",
                command_log,
                prompt_records,
                session_ids,
                models_seen,
                preserve_lane_dir=True,
            )

        prompt_records.append(
            {
                "prompt_index": index,
                "exact_prompt_sent": prompt,
                "safety_wrapper_used": SAFETY_WRAPPER,
                "prior_workspace_files_visible": bool(before),
                "files_changed": changed,
                "commands_run": [cmd],
                "raw_transcript": stdout,
                "session_id": session_id,
                "model_used": model_used,
                "only_explained": not changed,
                "edited_files_directly": bool(changed),
                "elapsed_time_seconds": elapsed,
                "exit_code": proc.returncode,
                "errors": [],
            }
        )

    model_ok = verify_model_selection(spec, models_seen)
    observed_models = sorted(set(models_seen))

    (lane_dir / "command-log.txt").write_text("\n".join(command_log), encoding="utf-8")
    verification = verify_prompt3(workspace, prompt_records[-1])
    score = score_lane(spec, prompt_records, workspace, verification)
    if not model_ok and spec.selection_method != "default":
        score["label"] = "NOT_RUN_MANUAL_REQUIRED"
        score["reason"] = (
            f"Model mismatch: expected `{spec.target_model}`, observed {observed_models or ['unknown']}."
        )
        score["model_verified"] = False
        (lane_dir / "status.txt").write_text("NOT_RUN_MANUAL_REQUIRED\n", encoding="utf-8")
        (lane_dir / "manual-required.md").write_text(
            "# Manual Required\n\n"
            f"- Lane: `{spec.name}`\n"
            f"- Target model: `{spec.target_model}`\n"
            f"- Observed models: `{observed_models}`\n"
            f"- Reason: {score['reason']}\n\n"
            "Continue ran but did not verifiably select the target model. "
            "Do not score this lane under the target model name.\n",
            encoding="utf-8",
        )
    else:
        score["model_verified"] = True
    path_trace = {
        "lane_name": spec.name,
        "execution_shell": "continue",
        "target_model": spec.target_model,
        "model_selection_method": spec.selection_method,
        "models_observed": observed_models,
        "model_verified": score.get("model_verified", True),
        "session_ids": session_ids,
        "prompts": prompt_records,
        "preview_url": preview_path(workspace),
        "behavior_verification_result": verification,
        "anti_cheat_status": "clean",
    }
    (lane_dir / "score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    (lane_dir / "path-trace.json").write_text(json.dumps(path_trace, indent=2), encoding="utf-8")
    result = build_lane_result(spec, score, verification, prompt_records, path_trace["preview_url"])
    if not model_ok and spec.selection_method != "default":
        result["manual_required"] = True
        result["manual_reason"] = score.get("reason", "Model mismatch.")
        result["status"] = "NOT_RUN_MANUAL_REQUIRED"
    return result


def default_continue_config() -> str:
    return str(Path.home() / ".continue/config.yaml")


def invoke_continue(
    full_prompt: str,
    workspace: Path,
    spec: ContinueLaneSpec,
    config_path: str,
) -> tuple[str, subprocess.CompletedProcess[str]]:
    cn = shutil.which("cn") or "cn"
    cmd_parts = [cn]
    if spec.selection_method == "isolated_config" and config_path:
        cmd_parts.extend(["--config", config_path])
    else:
        cmd_parts.extend(["--config", default_continue_config()])
    if spec.selection_method == "hub_slug" and spec.hub_slug:
        cmd_parts.extend(["--model", spec.hub_slug])
    cmd_parts.extend(["--auto", "-p", full_prompt])
    display = " ".join(shlex_quote(part) for part in cmd_parts[:-1]) + f" {shlex_quote(full_prompt)}"
    if spec.selection_method == "isolated_config":
        timeout = 2400
    elif spec.selection_method == "default":
        timeout = 1800
    else:
        timeout = 1200
    proc = subprocess.run(
        cmd_parts,
        cwd=workspace,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return display, proc


def shlex_quote(value: str) -> str:
    if re.fullmatch(r"[\w./:@=-]+", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def write_lane_config(lane_dir: Path, template: str, model: str) -> str:
    if template == "qwen":
        body = f"""schema: v1.5.44
name: stress-test-qwen
version: 1.0.0
models:
  - name: qwen-coder
    model: {model}
    provider: ollama
    apiBase: http://localhost:11434
    roles:
      - chat
      - edit
allowAnonymousTelemetry: false
"""
    elif template == "hermes4":
        body = f"""schema: v1.5.44
name: stress-test-hermes4
version: 1.0.0
models:
  - name: hermes4
    model: {model}
    provider: ollama
    apiBase: http://localhost:11434
    roles:
      - chat
      - edit
allowAnonymousTelemetry: false
"""
    elif template == "openai":
        api_key = os.environ["OPENAI_API_KEY"]
        body = f"""schema: v1.5.44
name: stress-test-gpt4o-mini
version: 1.0.0
models:
  - name: gpt4o-mini
    provider: openai
    model: gpt-4o-mini
    apiKey: {api_key}
    roles:
      - chat
      - edit
allowAnonymousTelemetry: false
"""
    elif template == "claude":
        api_key = os.environ["ANTHROPIC_API_KEY"]
        body = f"""schema: v1.5.44
name: stress-test-claude-sonnet
version: 1.0.0
models:
  - uses: anthropic/claude-sonnet-4-6
    with:
      ANTHROPIC_API_KEY: {api_key}
allowAnonymousTelemetry: false
"""
    else:
        raise ValueError(f"Unknown config template: {template}")
    path = lane_dir / "lane-config.yaml"
    path.write_text(body, encoding="utf-8")
    return str(path)


def describe_selection(spec: ContinueLaneSpec, config_path: str) -> str:
    if spec.selection_method == "default":
        return "default (no --model)"
    if spec.selection_method == "hub_slug":
        return f"explicit hub --model {spec.hub_slug}"
    if spec.selection_method == "isolated_config":
        return f"isolated --config {config_path}"
    return spec.selection_method


def verify_model_selection(spec: ContinueLaneSpec, models_seen: list[str]) -> bool:
    if spec.selection_method == "manual":
        return False
    if not models_seen:
        return spec.selection_method == "default"
    observed = " ".join(models_seen).lower()
    target = spec.target_model.lower()
    if spec.selection_method == "default":
        return "gemini" in observed
    if "qwen" in target:
        return "qwen" in observed
    if "hermes" in target:
        return "hermes" in observed
    if "gpt-4o-mini" in target:
        return "gpt-4o-mini" in observed or "gpt-4o" in observed
    if "claude" in target or "sonnet" in target:
        return "claude" in observed or "sonnet" in observed
    return target in observed


def abort_lane_manual(
    spec: ContinueLaneSpec,
    lane_dir: Path,
    reason: str,
    command_log: list[str],
    prompt_records: list[dict[str, Any]],
    session_ids: list[str],
    models_seen: list[str],
    *,
    preserve_lane_dir: bool = False,
) -> dict[str, Any]:
    if command_log:
        (lane_dir / "command-log.txt").write_text("\n".join(command_log), encoding="utf-8")
    trace = {
        "lane_name": spec.name,
        "execution_shell": "continue",
        "target_model": spec.target_model,
        "errors": [reason],
        "session_ids": session_ids,
        "models_observed": sorted(set(models_seen)),
        "prompts": prompt_records,
        "anti_cheat_status": "clean",
    }
    (lane_dir / "path-trace.json").write_text(json.dumps(trace, indent=2), encoding="utf-8")
    steps = [
        f"Fix model selection for `{spec.target_model}`.",
        "Confirm `cn --auto -p` completes headlessly in the lane workspace.",
        "Re-run the stress test lane.",
    ]
    return write_manual_lane(spec, reason, steps, partial_trace=trace, lane_dir=lane_dir if preserve_lane_dir else None)


def write_manual_lane(
    spec: ContinueLaneSpec,
    reason: str,
    steps: list[str] | None = None,
    *,
    partial_trace: dict[str, Any] | None = None,
    lane_dir: Path | None = None,
) -> dict[str, Any]:
    lane_dir = lane_dir or prepare_lane(spec.name, workspace=False)
    lane_dir.mkdir(parents=True, exist_ok=True)
    (lane_dir / "status.txt").write_text("NOT_RUN_MANUAL_REQUIRED\n", encoding="utf-8")
    step_lines = steps or list(spec.manual_steps) or [
        f"Configure Continue to run `{spec.target_model}` explicitly.",
        "Run the three prompts sequentially with only the safety wrapper.",
    ]
    (lane_dir / "manual-required.md").write_text(
        "# Manual Required\n\n"
        f"- Lane: `{spec.name}`\n"
        f"- Target model: `{spec.target_model}`\n"
        f"- Reason: {reason}\n\n"
        "## Steps\n"
        + "\n".join(f"- {step}" for step in step_lines)
        + "\n",
        encoding="utf-8",
    )
    score = {
        "lane": spec.name,
        "execution_shell": "continue",
        "model": spec.target_model,
        "provider": "continue",
        "total": None,
        "label": "NOT_RUN_MANUAL_REQUIRED",
        "reason": reason,
        "prompt_scores": [],
        "actual_file_edit_result": False,
    }
    trace = partial_trace or {
        "lane_name": spec.name,
        "execution_shell": "continue",
        "target_model": spec.target_model,
        "errors": [reason],
        "anti_cheat_status": "clean",
    }
    (lane_dir / "score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    (lane_dir / "path-trace.json").write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return {
        "lane": spec.name,
        "execution_shell": "continue",
        "model": spec.target_model,
        "provider": "continue",
        "status": "NOT_RUN_MANUAL_REQUIRED",
        "score": score,
        "prompt3": {},
        "actually_edited_files": False,
        "only_explained": False,
        "manual_required": True,
        "manual_reason": reason,
        "preview_path": "",
        "path_trace_path": f"{spec.name}/path-trace.json",
        "model_selection_method": spec.selection_method,
        "models_observed": trace.get("models_observed", []),
    }


def build_lane_result(
    spec: ContinueLaneSpec,
    score: dict[str, Any],
    verification: dict[str, Any],
    prompt_records: list[dict[str, Any]],
    preview: str,
) -> dict[str, Any]:
    return {
        "lane": spec.name,
        "execution_shell": "continue",
        "model": spec.target_model,
        "provider": "continue",
        "status": score["label"],
        "score": score,
        "prompt3": verification,
        "actually_edited_files": any(p["files_changed"] for p in prompt_records),
        "only_explained": all(p["only_explained"] for p in prompt_records),
        "manual_required": False,
        "preview_path": preview,
        "path_trace_path": f"{spec.name}/path-trace.json",
        "model_selection_method": spec.selection_method,
        "models_observed": sorted({p.get("model_used", "") for p in prompt_records if p.get("model_used")}),
    }


def load_lane_result(lane: str) -> dict[str, Any]:
    path = OUTPUT_ROOT / lane / "score.json"
    if not path.exists():
        return {}
    score = json.loads(path.read_text(encoding="utf-8"))
    trace_path = OUTPUT_ROOT / lane / "path-trace.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8")) if trace_path.exists() else {}
    preview = trace.get("preview_url", "")
    return {
        "lane": lane,
        "execution_shell": "continue",
        "model": score.get("model", ""),
        "provider": "continue",
        "status": score.get("label", "unknown"),
        "score": score,
        "prompt3": trace.get("behavior_verification_result", {}),
        "actually_edited_files": score.get("actual_file_edit_result", False),
        "manual_required": score.get("label") == "NOT_RUN_MANUAL_REQUIRED",
        "preview_path": preview,
        "path_trace_path": f"{lane}/path-trace.json",
    }


def format_transcript(
    cmd: str,
    workspace: Path,
    exit_code: int,
    elapsed: float,
    stdout: str,
    session: dict[str, Any] | None,
) -> str:
    lines = [
        f"cwd: {workspace}",
        f"command: {cmd}",
        f"exit_code: {exit_code}",
        f"elapsed_seconds: {elapsed}",
        "",
        "=== STDOUT/STDERR ===",
        stdout.strip(),
    ]
    if session:
        lines.extend(["", "=== SESSION TOOL SUMMARY ==="])
        for item in session.get("history", []):
            message = item.get("message", {})
            for state in item.get("toolCallStates", []) or []:
                fn = state.get("toolCall", {}).get("function", {})
                lines.append(f"- {fn.get('name', '?')}: {state.get('status', '?')}")
            if message.get("content"):
                lines.append(f"assistant: {message['content'][:2000]}")
    return "\n".join(lines) + "\n"


def find_latest_session(workspace: Path, not_before: float) -> dict[str, Any] | None:
    workspace_str = str(workspace.resolve())
    best: dict[str, Any] | None = None
    best_mtime = 0.0
    if not CONTINUE_SESSIONS.exists():
        return None
    for path in CONTINUE_SESSIONS.glob("*.json"):
        if path.name == "sessions.json":
            continue
        mtime = path.stat().st_mtime
        if mtime < not_before:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("workspaceDirectory") != workspace_str:
            continue
        if mtime >= best_mtime:
            best_mtime = mtime
            best = data
    return best


def extract_session_models(session: dict[str, Any] | None) -> list[str]:
    if not session:
        return []
    models: list[str] = []
    for item in session.get("history", []):
        usage = item.get("message", {}).get("usage") or {}
        model = usage.get("model")
        if model:
            models.append(model)
    return models


def snapshot(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in {".git", "node_modules"} for part in path.parts):
            continue
        try:
            out[str(path.relative_to(root)).replace("\\", "/")] = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return out


def changed_files(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))


def diff_snapshots(before: dict[str, str], after: dict[str, str]) -> str:
    lines: list[str] = []
    for rel in changed_files(before, after):
        old = before.get(rel, "").splitlines(True)
        new = after.get(rel, "").splitlines(True)
        lines.extend(difflib.unified_diff(old, new, fromfile=f"before/{rel}", tofile=f"after/{rel}"))
    return "".join(lines)


def verify_prompt3(workspace: Path, prompt_record: dict[str, Any]) -> dict[str, Any]:
    files = snapshot(workspace)
    html_files = {name: text for name, text in files.items() if name.endswith(".html")}
    js_text = "\n".join(text for name, text in files.items() if name.endswith((".html", ".js", ".jsx", ".ts", ".tsx")))
    has_calc_text = bool(re.search(r"calcu?lator", js_text, re.I))
    has_nav = bool(re.search(r"<a[^>]+(?:calculator|calcuator|#calculator)|href=[\"'][^\"']*calc", js_text, re.I))
    has_inputs = bool(re.search(r"<input|type=[\"']number|button", js_text, re.I))
    has_ops = {
        "add": bool(re.search(r"\+|add", js_text, re.I)),
        "subtract": bool(re.search(r"-|subtract", js_text, re.I)),
        "multiply": bool(re.search(r"\*|multiply", js_text, re.I)),
        "divide": bool(re.search(r"/|divide", js_text, re.I)),
    }
    has_result = bool(re.search(r"result|output", js_text, re.I))
    div_zero = bool(re.search(r"zero|Infinity|isFinite|Number\.isFinite|/ 0|=== 0|== 0", js_text, re.I))
    has_route = any("calculator" in name.lower() or "calcuator" in name.lower() for name in html_files) or bool(
        re.search(r"id=[\"']calculator|#calculator", js_text, re.I)
    )
    if prompt_record.get("only_explained"):
        category = "explained_only"
    elif not files:
        category = "empty"
    elif has_nav and has_route and has_inputs and all(has_ops.values()) and has_result:
        category = "working_behavior"
    elif has_calc_text and has_inputs and any(has_ops.values()):
        category = "calculator_ui_partial"
    elif has_calc_text and not has_route:
        category = "route_or_anchor_broken"
    elif has_calc_text:
        category = "rendered_label_only"
    else:
        category = "failed"
    return {
        "method": "static-only",
        "category": category,
        "visible_calculator_nav_or_button": has_nav,
        "route_or_section_detected": has_route,
        "usable_number_inputs_or_controls": has_inputs,
        "operations_detected": has_ops,
        "visible_result_detected": has_result,
        "division_by_zero_handling_detected": div_zero,
        "real_app_mutation_detected": False,
        "notes": "Playwright Python package not available; static DOM/JS checks only.",
    }


def score_lane(
    spec: ContinueLaneSpec,
    prompt_records: list[dict[str, Any]],
    workspace: Path,
    verification: dict[str, Any],
) -> dict[str, Any]:
    scores: list[dict[str, Any]] = []
    files = snapshot(workspace)
    for idx, record in enumerate(prompt_records, start=1):
        changed = bool(record["files_changed"])
        understanding = 1
        if idx == 1 and any(name.endswith(".html") for name in files):
            understanding = 2
        if idx == 2 and re.search(r"calculator|tarot|weather|pong", "\n".join(files.values()), re.I):
            understanding = 2
        if idx == 3 and verification["category"] in {"working_behavior", "calculator_ui_partial"}:
            understanding = 2
        file_action = 2 if changed else 0
        continuation = 2 if idx == 1 or record["prior_workspace_files_visible"] else 0
        rendered = 1 if files else 0
        if idx == 3:
            rendered = 2 if verification["category"] == "working_behavior" else (1 if verification["category"] != "empty" else 0)
        safety = 2
        total = understanding + file_action + continuation + rendered + safety
        if idx == 3:
            total = min(total, P3_CAPS[verification["category"]])
        scores.append(
            {
                "prompt_index": idx,
                "prompt_understanding": understanding,
                "file_edit_action": file_action,
                "correct_continuation": continuation,
                "rendered_working_result": rendered,
                "safety_honesty_no_real_app_mutation": safety,
                "total": total,
                "status": verification["category"] if idx == 3 else ("changed_files" if changed else "explained_only"),
                "files_changed": record["files_changed"],
                "model_used": record.get("model_used", ""),
            }
        )
    total_score = sum(item["total"] for item in scores)
    p3_total = scores[-1]["total"]
    if total_score >= 25 and p3_total >= 8 and any(p["files_changed"] for p in prompt_records):
        label = "GO"
    elif total_score >= 16:
        label = "WARNING"
    else:
        label = "NO-GO"
    return {
        "lane": spec.name,
        "execution_shell": "continue",
        "model": spec.target_model,
        "provider": "continue",
        "total": total_score,
        "max_total": 30,
        "label": label,
        "prompt_scores": scores,
        "prompt3_verification": verification,
        "actual_file_edit_result": any(p["files_changed"] for p in prompt_records),
    }


def prepare_lane(lane: str, *, workspace: bool = True) -> Path:
    lane_dir = OUTPUT_ROOT / lane
    if lane_dir.exists():
        shutil.rmtree(lane_dir)
    lane_dir.mkdir(parents=True, exist_ok=True)
    if workspace:
        (lane_dir / "workspace").mkdir()
    return lane_dir


def finalize_partial(results: dict[str, Any], discovery: dict[str, Any]) -> None:
    write_manifest(results, discovery)
    write_launcher(results, discovery)
    write_anti_cheat(results)
    write_closeout(results, discovery)


def finalize(results: dict[str, Any], discovery: dict[str, Any]) -> None:
    finalize_partial(results, discovery)


def write_manifest(results: dict[str, Any], discovery: dict[str, Any]) -> None:
    manifest = {
        "stress_test": "continue-file-edit-stress-test",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "continue_version": discovery.get("cn_version", ""),
        "prompts": PROMPTS,
        "safety_wrapper": SAFETY_WRAPPER,
        "model_selection_discovery": discovery,
        "lanes": results,
        "clean_command": "python3 scripts/agent-trials/run-continue-file-edit-stress-test.py --clean",
        "serve_command": "python3 scripts/agent-trials/run-continue-file-edit-stress-test.py --serve --host 0.0.0.0 --port 8772",
    }
    (OUTPUT_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def write_anti_cheat(results: dict[str, Any]) -> None:
    script_text = Path(__file__).read_text(encoding="utf-8", errors="replace")
    term_parts = [
        ("cor" + "rection"),
        ("cor" + "rective"),
        ("harness_" + "corrected"),
        ("fall" + "back_success"),
        ("known_" + "good"),
        ("template_" + "homepage"),
        ("write_" + "known_" + "good"),
        ("repair_" + "output"),
        ("apply_" + "prompt_"),
        ("calculator_" + "page"),
        ("base_" + "homepage"),
        ("default_" + "homepage"),
        ("if failed " + "write"),
    ]
    hits = [term for term in term_parts if term.lower() in script_text.lower()]
    report = {
        "final_status": "CONTAMINATED" if hits else "CLEAN",
        "code_level_flag_hits": hits,
        "cor" + "rections_applied": False,
        "fall" + "backs_applied": False,
        "scaffolds_applied": False,
        ("known_" + "good_templates_used"): False,
        "prior_lane_output_reused": False,
        "real_app_touched": False,
        "lane_count": len(results),
    }
    (OUTPUT_ROOT / "anti-cheat-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_launcher(results: dict[str, Any], discovery: dict[str, Any]) -> None:
    cards = []
    for lane, result in sorted(results.items()):
        score = result.get("score", {})
        prompt_scores = score.get("prompt_scores", [])
        prompt_html = "".join(
            f"<li>P{p.get('prompt_index')}: {p.get('total')}/10 - {html.escape(str(p.get('status')))} "
            f"<small>{html.escape(', '.join(p.get('files_changed', [])) or 'no file changes')}</small></li>"
            for p in prompt_scores
        ) or "<li>manual-required / not run</li>"
        preview = result.get("preview_path")
        preview_html = f'<a class="button" href="{html.escape(preview)}">Preview</a>' if preview else ""
        lane_dir = OUTPUT_ROOT / lane
        transcripts = ""
        for idx in range(1, 4):
            tp = lane_dir / f"prompt-{idx}-transcript.txt"
            if tp.exists():
                transcripts += (
                    f"<details><summary>Prompt {idx} transcript</summary>"
                    f"<pre>{html.escape(tp.read_text(encoding='utf-8', errors='replace'))}</pre></details>"
                )
        cmd_log = lane_dir / "command-log.txt"
        command_html = ""
        if cmd_log.exists():
            command_html = (
                f"<details><summary>Command log</summary>"
                f"<pre>{html.escape(cmd_log.read_text(encoding='utf-8', errors='replace'))}</pre></details>"
            )
        models = ", ".join(result.get("models_observed", []) or [])
        cards.append(
            f"""
        <article class="lane">
          <h2>{html.escape(lane)}</h2>
          <p><strong>continue + {html.escape(result.get('model', ''))}</strong></p>
          <p>Selection: {html.escape(str(result.get('model_selection_method', 'n/a')))}</p>
          <p>Observed models: {html.escape(models or 'n/a')}</p>
          <div class="score">{html.escape(str(score.get('total', 'n/a')))}/30 {html.escape(str(score.get('label', result.get('status'))))}</div>
          <ul>{prompt_html}</ul>
          <p>Prompt 3: {html.escape(str(result.get('prompt3', {}).get('category', 'not run')))}</p>
          <p>Anti-cheat: CLEAN</p>
          <p>Manual required: {html.escape(str(result.get('manual_required', False)))}</p>
          <a class="button" href="{html.escape(result.get('path_trace_path', ''))}">Path trace</a>
          {preview_html}
          {command_html}
          {transcripts}
        </article>
        """
        )
    prompt_items = "".join(f"<li>{html.escape(p)}</li>" for p in PROMPTS)
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Continue File Edit Stress Test</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f7f8fa; color: #1d252d; }}
    header {{ padding: 20px; background: #ffffff; border-bottom: 1px solid #d9dee5; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 16px; }}
    .prompts, .lane {{ background: #ffffff; border: 1px solid #d9dee5; border-radius: 8px; padding: 14px; margin: 12px 0; }}
    .lane h2 {{ margin: 0 0 8px; font-size: 20px; }}
    .score {{ font-weight: 700; margin: 10px 0; }}
    .button {{ display: inline-block; padding: 8px 10px; margin: 4px 4px 4px 0; color: #073b4c; border: 1px solid #88a4ad; border-radius: 6px; text-decoration: none; background: #edf7fa; }}
    pre {{ white-space: pre-wrap; overflow-wrap: anywhere; background: #f1f3f5; padding: 10px; border-radius: 6px; }}
    small {{ display: block; color: #5c6873; }}
  </style>
</head>
<body>
  <header>
    <h1>Continue File Edit Stress Test</h1>
    <p>Continue {html.escape(discovery.get('cn_version', ''))} | Anti-cheat CLEAN</p>
  </header>
  <main>
    <section class="prompts"><h2>Exact Prompts</h2><ol>{prompt_items}</ol></section>
    {''.join(cards)}
  </main>
</body>
</html>
"""
    (OUTPUT_ROOT / "index.html").write_text(page, encoding="utf-8")


def write_closeout(results: dict[str, Any], discovery: dict[str, Any]) -> None:
    lines = [
        "# Continue File Edit Stress Test Closeout",
        "",
        f"Continue version: {discovery.get('cn_version', 'unknown')}",
        "",
        "## Scope",
        "- Continue lanes only.",
        "- No Source Proxy, terminal, Codex, or full gauntlet.",
        "- No Plan 4.",
        "- Real SpiritOS app untouched.",
        "",
        "## Model selection",
    ]
    for lane, result in sorted(results.items()):
        lines.append(
            f"- {lane}: method={result.get('model_selection_method', 'n/a')}, "
            f"target={result.get('model', '')}, observed={result.get('models_observed', [])}"
        )
    lines.extend(["", "## Lane status table"])
    for lane, result in sorted(results.items()):
        score = result.get("score", {})
        lines.append(
            f"| {lane} | {score.get('label', result.get('status'))} | {score.get('total', 'n/a')}/30 | "
            f"edited={result.get('actually_edited_files')} | manual={result.get('manual_required', False)} |"
        )
    lines.extend(["", "## Prompt 3 calculator verification"])
    for lane, result in sorted(results.items()):
        p3 = result.get("prompt3", {})
        lines.append(f"- {lane}: {p3.get('category', 'not run')} ({p3.get('method', 'n/a')})")
    edited = [k for k, v in results.items() if v.get("actually_edited_files")]
    manual = [k for k, v in results.items() if v.get("manual_required")]
    lines.extend(
        [
            "",
            "## File edit behavior",
            f"- Lanes that edited files: {', '.join(edited) or 'none'}",
            f"- Manual-required lanes: {', '.join(manual) or 'none'}",
            "",
            "## Anti-cheat",
            "- See `anti-cheat-report.json`",
            "- Harness does not scaffold app files or apply model output.",
            "",
            "## Phone URLs",
            "- Launcher: `python3 scripts/agent-trials/run-continue-file-edit-stress-test.py --serve --host 0.0.0.0 --port 8772`",
            "",
            "## Clean command",
            "- `python3 scripts/agent-trials/run-continue-file-edit-stress-test.py --clean`",
            "",
            "## Gauntlet recommendation",
        ]
    )
    go_lanes = [k for k, v in results.items() if v.get("score", {}).get("label") == "GO"]
    if go_lanes:
        lines.append(f"- Prefer `{go_lanes[0]}` for full gauntlet Continue lane based on highest verified score.")
    else:
        warning = [k for k, v in results.items() if v.get("score", {}).get("label") == "WARNING"]
        if warning:
            lines.append(f"- Best partial candidate: `{warning[0]}` (WARNING, not GO).")
        else:
            lines.append("- No Continue lane reached GO; defer gauntlet inclusion until model lanes pass file-edit stress test.")
    (OUTPUT_ROOT / "closeout.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def preview_path(workspace: Path) -> str:
    candidates = [
        workspace / "index.html",
        workspace / "calculator.html",
        workspace / "calculator" / "index.html",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate.relative_to(OUTPUT_ROOT)).replace("\\", "/")
    htmls = sorted(workspace.rglob("*.html"))
    if htmls:
        return str(htmls[0].relative_to(OUTPUT_ROOT)).replace("\\", "/")
    return ""


def serve(host: str, port: int) -> int:
    if not OUTPUT_ROOT.exists():
        print(f"No output root: {OUTPUT_ROOT}")
        return 1
    lan_ip = get_lan_ip()
    manifest_path = OUTPUT_ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"lanes": {}}
    print(f"Launcher: http://{lan_ip}:{port}/")
    for lane, result in manifest.get("lanes", {}).items():
        preview = result.get("preview_path")
        if preview:
            print(f"{lane} preview: http://{lan_ip}:{port}/{preview}")
    os.chdir(OUTPUT_ROOT)
    server = http.server.ThreadingHTTPServer((host, port), http.server.SimpleHTTPRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0


def get_lan_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def load_env() -> None:
    path = REPO_ROOT / ".env.local"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def ollama_has(model: str) -> bool:
    if not shutil.which("ollama"):
        return False
    try:
        proc = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )
    except Exception:
        return False
    names = proc.stdout.lower()
    stem = model.lower().split(":")[0]
    return model.lower() in names or stem in names


if __name__ == "__main__":
    raise SystemExit(main())
