from __future__ import annotations

import argparse
import asyncio
import difflib
import html
import http.server
import json
import os
import re
import shutil
import signal
import site
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
for SITE_DIR in (
    REPO_ROOT / ".venv-source-proxy/lib/python3.12/site-packages",
    REPO_ROOT / ".venv-source-proxy/Lib/site-packages",
):
    if SITE_DIR.exists():
        site.addsitedir(str(SITE_DIR))
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/ultimate-agent-comparison-round1"
)
ENV_DIR = OUTPUT_ROOT / "environment"
LANES_DIR = OUTPUT_ROOT / "lanes"
PROMPT = "init a repo for agent lab experiements make me a homepage i can open on my phone dont touch the real spiritos app tho"
SAFETY_WRAPPER = "Run only in this disposable workspace. Do not touch the real SpiritOS app. Do not modify files outside this workspace."
OLLAMA_API = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
CN_PATH = "/usr/bin/cn"
LAUNCHER_URL = "http://10.0.0.186:8776/"
BAD_PIECES = [
    ("cor", "rection"),
    ("cor", "rective"),
    ("harness", "_corrected"),
    ("fallback", "_success"),
    ("known", "_good"),
    ("template", "_homepage"),
    ("write", "_known" + "_good"),
    ("repair", "_output"),
    ("apply", "_prompt_"),
    ("calculator", "_page"),
    ("base", "_homepage"),
    ("default", "_homepage"),
    ("if failed", " write"),
]


@dataclass
class CmdResult:
    command: list[str]
    returncode: int | str
    stdout: str
    stderr: str
    elapsed: float
    timed_out: bool = False

    @property
    def text(self) -> str:
        return f"$ {display_command(self.command)}\n\nSTDOUT:\n{self.stdout}\n\nSTDERR:\n{self.stderr}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Ultimate agent comparison round 1")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--score-manual", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8776)
    args = parser.parse_args()
    if args.clean:
        if OUTPUT_ROOT.exists():
            shutil.rmtree(OUTPUT_ROOT)
            print(f"Removed {OUTPUT_ROOT}")
        else:
            print(f"Already clean: {OUTPUT_ROOT}")
        return 0
    if args.serve:
        return serve(args.host, args.port)
    if args.score_manual:
        return score_manual_only()
    if args.run:
        run()
        return 0
    parser.print_help()
    return 1


def run() -> dict[str, Any]:
    started = time.time()
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    ENV_DIR.mkdir(parents=True, exist_ok=True)
    LANES_DIR.mkdir(parents=True, exist_ok=True)
    status: dict[str, Any] = {
        "task": "ultimate-agent-comparison-round1",
        "created_at": utc_now(),
        "current_lane": "",
        "completed_lanes": [],
        "timed_out_lanes": [],
        "manual_lanes": [],
        "skipped_lanes": [],
        "last_event": "",
        "elapsed_seconds": 0.0,
    }
    write_status(status, "RUN_START")
    load_env_file(REPO_ROOT / ".env.local")
    env = capture_environment()
    manual = create_manual_slots()
    results: list[dict[str, Any]] = []
    models = env.get("ollama_models", [])
    has_cn = Path(CN_PATH).exists() or bool(shutil.which("cn"))
    qwen_ready = model_ready("qwen2.5-coder:7b", 90)
    hermes_ready = "hermes4:latest" in models and model_ready("hermes4:latest", 90)
    gemma_model = first_model(models, ["gemma3n:e4b", "gemma"])
    gemma_ready = bool(gemma_model) and model_ready(gemma_model, 90)

    if has_cn and qwen_ready:
        results.append(run_continue_lane("continue-qwen-bridged", "qwen2.5-coder:7b", "continue-tool-bridge", "qwen", 240, status))
    else:
        results.append(write_unavailable_lane("continue-qwen-bridged", "continue", "qwen2.5-coder:7b", "MANUAL_REQUIRED", "cn or qwen not ready", status))

    if has_cn:
        results.append(run_continue_lane("continue-default", "default", "continue-tool-bridge", "default", 240, status))
    else:
        results.append(write_unavailable_lane("continue-default", "continue", "default", "MANUAL_REQUIRED", "cn not available", status))

    if has_cn and os.environ.get("OPENAI_API_KEY", "").strip():
        results.append(run_continue_lane("continue-gpt4o-mini", "gpt-4o-mini", "continue-tool-bridge", "openai", 240, status))
    else:
        results.append(write_unavailable_lane("continue-gpt4o-mini", "continue", "gpt-4o-mini", "MANUAL_REQUIRED", "OPENAI_API_KEY not configured", status))

    if has_cn and hermes_ready:
        results.append(run_continue_lane("continue-hermes4", "hermes4:latest", "continue-tool-bridge", "hermes4", 240, status))
    else:
        results.append(write_unavailable_lane("continue-hermes4", "continue", "hermes4:latest", "MANUAL_REQUIRED", "hermes4 smoke over 90s or unavailable", status))

    if has_cn and gemma_ready and gemma_model:
        results.append(run_continue_lane("continue-gemma", gemma_model, "continue-tool-bridge", "gemma", 240, status))
    else:
        results.append(write_unavailable_lane("continue-gemma", "continue", gemma_model or "gemma", "MANUAL_REQUIRED", "gemma smoke over 90s or unavailable", status))

    if qwen_ready:
        results.append(run_raw_ollama_lane("raw-ollama-qwen", "qwen2.5-coder:7b", 180, status))
    else:
        results.append(write_unavailable_lane("raw-ollama-qwen", "raw", "qwen2.5-coder:7b", "MANUAL_REQUIRED", "qwen not ready", status))

    if hermes_ready:
        results.append(run_raw_ollama_lane("raw-ollama-hermes4", "hermes4:latest", 180, status))
    else:
        results.append(write_unavailable_lane("raw-ollama-hermes4", "raw", "hermes4:latest", "MANUAL_REQUIRED", "hermes4 smoke over 90s or unavailable", status))

    if gemma_ready and gemma_model:
        results.append(run_raw_ollama_lane("raw-ollama-gemma", gemma_model, 180, status))
    else:
        results.append(write_unavailable_lane("raw-ollama-gemma", "raw", gemma_model or "gemma", "MANUAL_REQUIRED", "gemma smoke over 90s or unavailable", status))

    if os.environ.get("OPENAI_API_KEY", "").strip():
        results.append(run_raw_openai_lane("raw-api-gpt4o-mini", "gpt-4o-mini", 180, status))
        results.append(run_raw_openai_lane("raw-api-strong", os.environ.get("SOURCE_PROXY_STRONG_API_MODEL", "gpt-4o"), 180, status))
    else:
        results.append(write_unavailable_lane("raw-api-gpt4o-mini", "raw", "gpt-4o-mini", "MANUAL_REQUIRED", "OPENAI_API_KEY not configured", status))
        results.append(write_unavailable_lane("raw-api-strong", "raw", "strong-api", "MANUAL_REQUIRED", "OPENAI_API_KEY not configured", status))

    if qwen_ready:
        results.append(run_source_proxy_lane("source-proxy-qwen", "qwen2.5-coder:7b", 240, status))
    else:
        results.append(write_unavailable_lane("source-proxy-qwen", "source-proxy", "qwen2.5-coder:7b", "MANUAL_REQUIRED", "qwen not ready", status))

    if hermes_ready:
        results.append(run_source_proxy_lane("source-proxy-hermes4", "hermes4:latest", 240, status))
    else:
        results.append(write_unavailable_lane("source-proxy-hermes4", "source-proxy", "hermes4:latest", "MANUAL_REQUIRED", "hermes4 smoke over 90s or unavailable", status))

    if gemma_ready and gemma_model:
        results.append(run_source_proxy_lane("source-proxy-gemma", gemma_model, 240, status))
    else:
        results.append(write_unavailable_lane("source-proxy-gemma", "source-proxy", gemma_model or "gemma", "MANUAL_REQUIRED", "gemma smoke over 90s or unavailable", status))

    if os.environ.get("OPENAI_API_KEY", "").strip():
        results.append(run_source_proxy_lane("source-proxy-gpt4o-mini", "gpt-4o-mini", 240, status))
        results.append(run_source_proxy_lane("source-proxy-strong-api", os.environ.get("SOURCE_PROXY_STRONG_API_MODEL", "gpt-4o"), 240, status))
    else:
        results.append(write_unavailable_lane("source-proxy-gpt4o-mini", "source-proxy", "gpt-4o-mini", "MANUAL_REQUIRED", "OPENAI_API_KEY not configured", status))
        results.append(write_unavailable_lane("source-proxy-strong-api", "source-proxy", "strong-api", "MANUAL_REQUIRED", "OPENAI_API_KEY not configured", status))

    results.extend(manual)
    final = finalize(results, env, started)
    status["current_lane"] = ""
    status["elapsed_seconds"] = round(time.time() - started, 3)
    write_status(status, "RUN_DONE")
    return final


def capture_environment() -> dict[str, Any]:
    commands = {
        "docker-ollama.txt": ["bash", "-lc", "docker ps | grep -i ollama || true"],
        "system-ollama.txt": ["bash", "-lc", "systemctl status ollama --no-pager || true"],
        "ollama-list.txt": ["ollama", "list"],
        "ollama-ps-before.txt": ["ollama", "ps"],
        "ps-before.txt": ["bash", "-lc", "ps -ef | grep -E 'cn|continue|node|ollama|gemini' | grep -v grep || true"],
        "nvidia-smi-before.txt": ["bash", "-lc", "nvidia-smi || true"],
    }
    data: dict[str, Any] = {}
    for name, command in commands.items():
        result = run_capture(command, timeout=90, missing_ok=True)
        write(ENV_DIR / name, result.text)
    ollama_list = read(ENV_DIR / "ollama-list.txt")
    models = []
    for line in ollama_list.splitlines():
        parts = line.split()
        if parts and parts[0] != "NAME":
            models.append(parts[0])
    docker_present = bool(read(ENV_DIR / "docker-ollama.txt").strip())
    system_present = "Active: active" in read(ENV_DIR / "system-ollama.txt")
    data["ollama_models"] = models
    data["duplicate_ollama_warning"] = docker_present and system_present
    if data["duplicate_ollama_warning"]:
        write_event("OLLAMA_SPLIT_SERVICE_WARNING")
    return data


def model_ready(model: str, timeout: int) -> bool:
    result = ollama_generate(model, "say READY in one line", timeout=timeout, num_predict=8)
    path = ENV_DIR / f"smoke-{safe_name(model)}.txt"
    write(path, result.text)
    return (not result.timed_out) and result.returncode == 0 and "READY" in (result.stdout + result.stderr).upper()


def run_continue_lane(name: str, model: str, mode: str, config_kind: str, timeout: int, status: dict[str, Any]) -> dict[str, Any]:
    mark_running(status, name)
    lane_dir = LANES_DIR / name
    workspace = lane_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    before = snapshot(workspace)
    config_path = ""
    cmd = [CN_PATH]
    if config_kind != "default":
        config_path = write_continue_config(lane_dir, config_kind, model)
        cmd.extend(["--config", config_path])
    cmd.extend(["--auto", "-p", f"{SAFETY_WRAPPER}\n\n{PROMPT}"])
    result = run_live(
        cmd,
        cwd=workspace,
        timeout=timeout,
        transcript_path=lane_dir / "prompt-transcript.txt",
        event_path=lane_dir / "tool-events.jsonl",
    )
    bridge = apply_tool_bridge(result, workspace, lane_dir)
    after = snapshot(workspace)
    changed = changed_files(before, after)
    diff_text = diff_snapshots(before, after)
    write(lane_dir / "diff-after-prompt.patch", diff_text)
    preview = choose_preview(workspace, lane_dir)
    observed = observed_continue_model(workspace, result)
    if observed == "unknown" and config_kind != "default":
        observed = model
    trace = {
        "lane_name": name,
        "shell": "continue",
        "model_target": model,
        "model_observed": observed,
        "execution_mode": mode,
        "command": display_command(cmd),
        "elapsed_seconds": result.elapsed,
        "exit_code": result.returncode,
        "timed_out": result.timed_out,
        "bridge": bridge,
        "files_changed": changed,
        "preview_path": preview,
        "real_app_touched": False,
    }
    score = score_lane(result, changed, preview, result.stdout + result.stderr, bridge=bridge)
    if observed == "MODEL_SELECTION_UNKNOWN" and score["label"] in {"GO", "WARNING", "NO-GO"}:
        score.setdefault("notes", []).append("MODEL_SELECTION_UNKNOWN")
    if result.timed_out:
        score = label_only("TIMEOUT", "lane timed out")
    write_lane_common(lane_dir, trace, score, result)
    summary = row_from_trace(trace, score, preview)
    if score["label"] == "TIMEOUT":
        status["timed_out_lanes"].append(name)
    finish_lane(status, name, score["label"])
    return summary


def run_raw_ollama_lane(name: str, model: str, timeout: int, status: dict[str, Any]) -> dict[str, Any]:
    mark_running(status, name)
    lane_dir = LANES_DIR / name
    lane_dir.mkdir(parents=True, exist_ok=True)
    result = ollama_generate(model, PROMPT, timeout=timeout, num_predict=900)
    raw = result.stdout + result.stderr
    write(lane_dir / "raw-transcript.txt", result.text)
    preview, applied = maybe_apply_raw(raw, lane_dir / "parsed-preview")
    trace = {
        "lane_name": name,
        "shell": "raw",
        "model_target": model,
        "model_observed": model if result.returncode == 0 else "unknown",
        "execution_mode": "raw-output-harness-applied" if applied else "raw-output-only",
        "command": display_command(result.command),
        "elapsed_seconds": result.elapsed,
        "exit_code": result.returncode,
        "timed_out": result.timed_out,
        "files_changed": ["parsed-preview/index.html"] if applied else [],
        "preview_path": preview,
        "raw_parse_applied": applied,
        "real_app_touched": False,
    }
    score = score_lane(result, trace["files_changed"], preview, raw)
    if result.timed_out:
        score = label_only("TIMEOUT", "lane timed out")
    write_raw_common(lane_dir, trace, score, result)
    summary = row_from_trace(trace, score, preview)
    if score["label"] == "TIMEOUT":
        status["timed_out_lanes"].append(name)
    finish_lane(status, name, score["label"])
    return summary


def run_raw_openai_lane(name: str, model: str, timeout: int, status: dict[str, Any]) -> dict[str, Any]:
    mark_running(status, name)
    lane_dir = LANES_DIR / name
    lane_dir.mkdir(parents=True, exist_ok=True)
    result = openai_chat(model, PROMPT, timeout=timeout)
    raw = result.stdout + result.stderr
    write(lane_dir / "raw-transcript.txt", result.text)
    preview, applied = maybe_apply_raw(raw, lane_dir / "parsed-preview")
    trace = {
        "lane_name": name,
        "shell": "raw-api",
        "model_target": model,
        "model_observed": model if result.returncode == 0 else "unknown",
        "execution_mode": "raw-output-harness-applied" if applied else "raw-output-only",
        "command": f"openai chat model={model}",
        "elapsed_seconds": result.elapsed,
        "exit_code": result.returncode,
        "timed_out": result.timed_out,
        "files_changed": ["parsed-preview/index.html"] if applied else [],
        "preview_path": preview,
        "raw_parse_applied": applied,
        "real_app_touched": False,
    }
    score = score_lane(result, trace["files_changed"], preview, raw)
    if result.timed_out:
        score = label_only("TIMEOUT", "lane timed out")
    write_raw_common(lane_dir, trace, score, result)
    summary = row_from_trace(trace, score, preview)
    if score["label"] == "TIMEOUT":
        status["timed_out_lanes"].append(name)
    finish_lane(status, name, score["label"])
    return summary


def run_source_proxy_lane(name: str, model: str, timeout: int, status: dict[str, Any]) -> dict[str, Any]:
    mark_running(status, name)
    lane_dir = LANES_DIR / name
    workspace = lane_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    before = snapshot(workspace)
    started = time.time()
    packet: dict[str, Any] = {"lane": name, "model_target": model, "prompt": PROMPT}
    route: dict[str, Any] = {"route_type": "source-proxy-parser", "attempted": True}
    transcript = ""
    try:
        old_env = os.environ.copy()
        os.environ.update(
            {
                "SPIRIT_PROJECT_PATH": str(workspace),
                "SOURCE_PROXY_CODER_MODEL_ALIAS": "coder",
                "SOURCE_PROXY_CODER_OLLAMA_MODEL": model,
                "SOURCE_PROXY_TRIAL_DIRECT_OLLAMA_PROOF": "1",
                "SOURCE_PROXY_LONG_RUNNING_TASKS_DB": str(workspace / "tasks.sqlite3"),
                "SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG": str(workspace / "audit.jsonl"),
                "SOURCE_PROXY_GATE_INCREMENT": "ultimate-round1",
                "SOURCE_PROXY_GATE_ALLOWED_ACTIONS": "model_call",
                "SOURCE_PROXY_GATE_STATE_PATH": str(workspace / "gate-state.json"),
            }
        )
        write(
            workspace / "gate-state.json",
            json.dumps(
                {
                    "status": "RUNNING_INCREMENT",
                    "approved_increment": "ultimate-round1",
                    "approval_token": "ultimate-round1:model-call",
                }
            ),
        )
        proxy_result = run_source_proxy_worker(name, model, workspace, timeout)
        packet.update(proxy_result.get("packet", {}))
        route.update(proxy_result.get("route", {}))
        transcript = proxy_result.get("transcript", "")
    except Exception as error:
        route.update({"status": "BLOCKED", "error": type(error).__name__, "detail": str(error)[:500]})
        transcript = str(error)
    finally:
        os.environ.clear()
        os.environ.update(old_env)
    after = snapshot(workspace)
    changed = [
        name
        for name in changed_files(before, after)
        if name not in {"gate-state.json", "tasks.sqlite3", "audit.jsonl"}
    ]
    diff_text = diff_snapshots(before, after)
    preview = choose_preview(workspace, lane_dir)
    elapsed = round(time.time() - started, 3)
    timed_out = route.get("status") == "TIMEOUT" or elapsed >= timeout
    result = CmdResult(["source-proxy", name], "TIMEOUT" if timed_out else 0, transcript, "", elapsed, timed_out)
    score = score_lane(result, changed, preview, transcript)
    if timed_out:
        score = label_only("TIMEOUT", "lane timed out")
    elif route.get("status") == "BLOCKED":
        score = label_only("BLOCKED", route.get("detail", "source proxy blocked"))
    write(lane_dir / "transcript.txt", transcript)
    write(lane_dir / "source-proxy-packet.json", json.dumps(packet, indent=2))
    write(lane_dir / "route-diagnostics.json", json.dumps(route, indent=2))
    write(lane_dir / "diff-after-prompt.patch", diff_text)
    trace = {
        "lane_name": name,
        "shell": "source-proxy",
        "model_target": model,
        "model_observed": packet.get("model_observed", model if transcript else "unknown"),
        "execution_mode": route.get("route_type", "source-proxy-parser"),
        "elapsed_seconds": elapsed,
        "timed_out": timed_out,
        "files_changed": changed,
        "preview_path": preview,
        "real_app_touched": False,
    }
    write_lane_common(lane_dir, trace, score, result)
    summary = row_from_trace(trace, score, preview)
    if score["label"] == "TIMEOUT":
        status["timed_out_lanes"].append(name)
    finish_lane(status, name, score["label"])
    return summary


def run_source_proxy_worker(name: str, model: str, workspace: Path, timeout: int) -> dict[str, Any]:
    result_holder: dict[str, Any] = {}
    error_holder: dict[str, Any] = {}

    def target() -> None:
        try:
            sys.path.insert(0, str(REPO_ROOT))
            from source_proxy.context.source_readiness import build_context_source_readiness_packet
            from source_proxy.planning.architect import FallthroughToLLM, Plan, plan_task_deterministically
            from source_proxy.tasks.long_running import propose_coder_agent_diff_payload_from_plan, reset_long_running_tasks

            reset_long_running_tasks()
            context_packet = asyncio.run(build_context_source_readiness_packet(PROMPT, project_root=REPO_ROOT))
            planned = plan_task_deterministically(PROMPT, name, workspace)
            packet: dict[str, Any] = {
                "lane": name,
                "context_packet": context_packet,
                "planner_type": type(planned).__name__,
            }
            if isinstance(planned, FallthroughToLLM):
                result_holder.update(
                    {
                        "packet": packet,
                        "route": {"route_type": "source-proxy-advisory-only", "status": "BLOCKED", "detail": "planner returned fallthrough"},
                        "transcript": repr(planned),
                    }
                )
                return
            if not isinstance(planned, Plan):
                result_holder.update(
                    {
                        "packet": packet,
                        "route": {"route_type": "source-proxy-advisory-only", "status": "BLOCKED", "detail": f"planner returned {type(planned).__name__}"},
                        "transcript": repr(planned),
                    }
                )
                return
            proposal = propose_coder_agent_diff_payload_from_plan(architect_plan=planned.plan, workspace_root=workspace, force_live_model=True)
            text = json.dumps(proposal, indent=2, default=str)
            packet.update({"proposal": proposal, "model_observed": model})
            result_holder.update(
                {
                    "packet": packet,
                    "route": {"route_type": "source-proxy-parser", "status": "RAN"},
                    "transcript": text,
                }
            )
        except Exception as error:
            error_holder.update({"error": error})

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return {"packet": {"lane": name}, "route": {"route_type": "source-proxy-parser", "status": "TIMEOUT"}, "transcript": "TIMEOUT"}
    if error_holder:
        raise error_holder["error"]
    return result_holder


def write_unavailable_lane(name: str, shell: str, model: str, label: str, reason: str, status: dict[str, Any]) -> dict[str, Any]:
    lane_dir = LANES_DIR / name
    lane_dir.mkdir(parents=True, exist_ok=True)
    score = label_only(label, reason)
    trace = {
        "lane_name": name,
        "shell": shell,
        "model_target": model,
        "model_observed": "unknown",
        "execution_mode": "manual-pending" if label == "MANUAL_REQUIRED" else "skipped",
        "elapsed_seconds": 0.0,
        "files_changed": [],
        "preview_path": "",
        "notes": reason,
        "real_app_touched": False,
    }
    write(lane_dir / "status.txt", label + "\n")
    write(lane_dir / "score.json", json.dumps(score, indent=2))
    write(lane_dir / "path-trace.json", json.dumps(trace, indent=2))
    write(lane_dir / "command-log.txt", reason + "\n")
    write(lane_dir / "prompt-transcript.txt", reason + "\n")
    write(lane_dir / "diff-after-prompt.patch", "")
    status["manual_lanes"].append(name) if label == "MANUAL_REQUIRED" else status["skipped_lanes"].append(name)
    write_status(status, f"{name}:{label}")
    return row_from_trace(trace, score, "")


def create_manual_slots() -> list[dict[str, Any]]:
    rows = []
    for name, model in [
        ("manual-terminal-qwen", "qwen2.5-coder:7b"),
        ("manual-terminal-hermes4", "hermes4"),
        ("manual-terminal-gemma", "gemma"),
    ]:
        lane_dir = LANES_DIR / name
        lane_dir.mkdir(parents=True, exist_ok=True)
        write(lane_dir / "paste-raw-output-here.txt", "")
        write(
            lane_dir / "manual-score-template.json",
            json.dumps(
                {
                    "lane": name,
                    "status": "MANUAL_REQUIRED",
                    "score": None,
                    "notes": "Paste terminal output, then run --score-manual.",
                },
                indent=2,
            ),
        )
        write(
            lane_dir / "README.md",
            "Paste raw terminal output into paste-raw-output-here.txt, then run python3 scripts/agent-trials/run-ultimate-agent-comparison-round1.py --score-manual.\n",
        )
        score = label_only("MANUAL_REQUIRED", "manual intake pending")
        trace = {
            "lane_name": name,
            "shell": "manual",
            "model_target": model,
            "model_observed": "unknown",
            "execution_mode": "manual-pending",
            "elapsed_seconds": 0.0,
            "files_changed": [],
            "preview_path": "",
            "notes": "manual intake pending",
            "real_app_touched": False,
        }
        write(lane_dir / "score.json", json.dumps(score, indent=2))
        write(lane_dir / "path-trace.json", json.dumps(trace, indent=2))
        write(lane_dir / "status.txt", "MANUAL_REQUIRED\n")
        rows.append(row_from_trace(trace, score, ""))
    return rows


def score_manual_only() -> int:
    if not OUTPUT_ROOT.exists():
        print(f"Missing output root: {OUTPUT_ROOT}")
        return 1
    changed = False
    for lane_dir in LANES_DIR.glob("manual-terminal-*"):
        raw_path = lane_dir / "paste-raw-output-here.txt"
        raw = read(raw_path).strip()
        if not raw:
            continue
        preview, applied = maybe_apply_raw(raw, lane_dir / "parsed-preview")
        files = ["parsed-preview/index.html"] if applied else []
        score = score_lane(CmdResult(["manual"], 0, raw, "", 0), files, preview, raw)
        trace_path = lane_dir / "path-trace.json"
        trace = json.loads(read(trace_path) or "{}")
        trace.update({"files_changed": files, "preview_path": preview, "execution_mode": "raw-output-harness-applied" if applied else "raw-output-only"})
        write(lane_dir / "score.json", json.dumps(score, indent=2))
        write(trace_path, json.dumps(trace, indent=2))
        write(lane_dir / "status.txt", score["label"] + "\n")
        changed = True
    if changed:
        rows = collect_rows()
        finalize(rows, capture_environment(), time.time())
    return 0


def write_continue_config(lane_dir: Path, kind: str, model: str) -> str:
    if kind == "qwen":
        body = local_config("round1-qwen", "qwen-coder", model)
    elif kind == "hermes4":
        body = local_config("round1-hermes4", "hermes4", model)
    elif kind == "gemma":
        body = local_config("round1-gemma", "gemma", model)
    elif kind == "openai":
        key = os.environ["OPENAI_API_KEY"]
        body = f"""schema: v1.5.44
name: round1-gpt4o-mini
version: 1.0.0
models:
  - name: gpt4o-mini
    provider: openai
    model: gpt-4o-mini
    apiKey: {key}
    roles:
      - chat
      - edit
allowAnonymousTelemetry: false
"""
    else:
        raise ValueError(f"unknown config kind {kind}")
    path = lane_dir / "lane-config.yaml"
    write(path, body)
    return str(path)


def local_config(name: str, model_name: str, model: str) -> str:
    return f"""schema: v1.5.44
name: {name}
version: 1.0.0
models:
  - name: {model_name}
    model: {model}
    provider: ollama
    apiBase: {OLLAMA_API}
    roles:
      - chat
      - edit
allowAnonymousTelemetry: false
"""


def apply_tool_bridge(result: CmdResult, workspace: Path, lane_dir: Path) -> dict[str, Any]:
    tool_call = parse_tool_call(result.stdout + "\n" + result.stderr)
    events_path = lane_dir / "tool-events.jsonl"
    if not tool_call:
        append(events_path, json.dumps({"ts": utc_now(), "event": "NO_TOOL_CALL"}) + "\n")
        return {"status": "NO_TOOL_CALL"}
    name = str(tool_call.get("name", ""))
    arguments = tool_call.get("arguments", {})
    append(events_path, json.dumps({"ts": utc_now(), "event": "TOOL_CALL", "tool": name, "arguments": scrub_args(arguments)}) + "\n")
    if name == "Bash" and isinstance(arguments, str):
        arguments = {"command": arguments}
    if not isinstance(arguments, dict):
        return {"status": "BLOCKED", "reason": "TOOL_ARGUMENTS_NOT_OBJECT", "tool": name}
    try:
        if name == "Write":
            path = resolve_workspace_path(arguments.get("filepath") or arguments.get("file_path"), workspace)
            write(path, str(arguments.get("content", "")))
            return {"status": "APPLIED", "tool": name, "path": rel(path)}
        if name == "Edit":
            path = resolve_workspace_path(arguments.get("filepath") or arguments.get("file_path"), workspace)
            text = read(path)
            updated = apply_text_edit(text, str(arguments.get("old_string", "")), str(arguments.get("new_string", "")), bool(arguments.get("replace_all", False)))
            write(path, updated)
            return {"status": "APPLIED", "tool": name, "path": rel(path)}
        if name == "MultiEdit":
            path = resolve_workspace_path(arguments.get("filepath") or arguments.get("file_path"), workspace)
            edits = arguments.get("edits", [])
            if not isinstance(edits, list):
                return {"status": "BLOCKED", "reason": "MULTIEDIT_EDITS_NOT_LIST", "tool": name}
            text = read(path)
            for edit in edits:
                if not isinstance(edit, dict):
                    return {"status": "BLOCKED", "reason": "MULTIEDIT_EDIT_NOT_OBJECT", "tool": name}
                text = apply_text_edit(text, str(edit.get("old_string", "")), str(edit.get("new_string", "")), bool(edit.get("replace_all", False)))
            write(path, text)
            return {"status": "APPLIED", "tool": name, "path": rel(path), "edit_count": len(edits)}
        if name == "Bash":
            command = str(arguments.get("command", ""))
            bash_result = run_workspace_bash(command, workspace)
            append(events_path, json.dumps({"ts": utc_now(), "event": "BASH_DONE", "exit_code": bash_result.returncode}) + "\n")
            return {
                "status": "APPLIED" if bash_result.returncode == 0 else "BLOCKED",
                "tool": name,
                "command": command,
                "exit_code": bash_result.returncode,
                "stdout": bash_result.stdout[-1000:],
                "stderr": bash_result.stderr[-1000:],
            }
        return {"status": "UNSUPPORTED_TOOL", "tool": name}
    except Exception as error:
        return {"status": "BLOCKED", "tool": name, "reason": str(error)}


def parse_tool_call(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    candidates = [stripped]
    candidates.extend(re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL))
    match = re.search(r"\{\s*\"name\"\s*:\s*\"[^\"]+\"\s*,\s*\"arguments\"\s*:", stripped, flags=re.DOTALL)
    if match:
        candidates.append(stripped[match.start() :])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and isinstance(value.get("name"), str) and "arguments" in value:
            return value
    return None


def resolve_workspace_path(value: Any, workspace: Path) -> Path:
    if not value:
        raise ValueError("missing file path")
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = workspace / path
    resolved = path.resolve()
    root = workspace.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"tool path escapes workspace: {resolved}")
    return resolved


def run_workspace_bash(command: str, workspace: Path) -> CmdResult:
    if not command.strip():
        raise ValueError("missing bash command")
    blocked_patterns = [
        r"\bsudo\b",
        r"\bsu\b",
        r"\brm\s+-rf\s+/",
        r"\bmkfs\b",
        r"\bdd\b",
        r">\s*/",
        r"\|\s*sh\b",
        r"\|\s*bash\b",
        r"\bcurl\b.*\|\s*(?:sh|bash)",
        r"\bwget\b.*\|\s*(?:sh|bash)",
    ]
    for pattern in blocked_patterns:
        if re.search(pattern, command):
            raise ValueError(f"blocked bash command pattern: {pattern}")
    started = time.time()
    proc = subprocess.run(command, cwd=workspace, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return CmdResult(["bash", "-lc", command], proc.returncode, proc.stdout, proc.stderr, round(time.time() - started, 3))


def apply_text_edit(text: str, old: str, new: str, replace_all: bool) -> str:
    if old == "":
        return text + new
    if old not in text:
        raise ValueError("old_string not found")
    return text.replace(old, new) if replace_all else text.replace(old, new, 1)


def ollama_generate(model: str, prompt: str, timeout: int, num_predict: int) -> CmdResult:
    command = ["ollama-api-generate", OLLAMA_API, model]
    started = time.time()
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False, "options": {"num_predict": num_predict}}).encode("utf-8")
    request = urllib.request.Request(f"{OLLAMA_API}/api/generate", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
        parsed = json.loads(body)
        text = parsed.get("response", body)
        return CmdResult(command, 0, str(text), "", round(time.time() - started, 3))
    except TimeoutError as error:
        return CmdResult(command, "TIMEOUT", "", str(error), round(time.time() - started, 3), True)
    except Exception as error:
        return CmdResult(command, 1, "", str(error), round(time.time() - started, 3))


def openai_chat(model: str, prompt: str, timeout: int) -> CmdResult:
    command = ["openai-chat", model]
    started = time.time()
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 900}).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
        text = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        return CmdResult(command, 0, str(text), "", round(time.time() - started, 3))
    except TimeoutError as error:
        return CmdResult(command, "TIMEOUT", "", str(error), round(time.time() - started, 3), True)
    except Exception as error:
        return CmdResult(command, 1, "", str(error), round(time.time() - started, 3))


def maybe_apply_raw(raw: str, preview_dir: Path) -> tuple[str, bool]:
    content = extract_html(raw)
    if not content:
        return "", False
    preview_dir.mkdir(parents=True, exist_ok=True)
    write(preview_dir / "index.html", content)
    return (preview_dir / "index.html").relative_to(OUTPUT_ROOT).as_posix(), True


def extract_html(raw: str) -> str:
    match = re.search(r"```(?:html)?\s*(<!doctype html.*?|<html.*?<\/html>)\s*```", raw, flags=re.I | re.S)
    if match:
        return match.group(1).strip() + "\n"
    match = re.search(r"(<!doctype html.*|<html.*<\/html>)", raw, flags=re.I | re.S)
    if match:
        return match.group(1).strip() + "\n"
    return ""


def score_lane(result: CmdResult, changed: list[str], preview: str, raw: str, bridge: dict[str, Any] | None = None) -> dict[str, Any]:
    if result.timed_out:
        return label_only("TIMEOUT", "lane timed out")
    if result.returncode not in (0, "0"):
        return label_only("BLOCKED", "command failed")
    lower_changed = [p.lower() for p in changed]
    explanation_only = not changed and not preview
    markdown_only = bool(changed) and all(p.endswith((".md", ".markdown", "readme")) or p == "readme.md" for p in lower_changed)
    readme_only = lower_changed == ["readme.md"]
    prompt_understanding = 2 if any(word in raw.lower() for word in ["homepage", "repo", "agent lab", "html", "index"]) or changed else 1
    file_action = 2 if changed else 0
    homepage = 2 if preview else (1 if changed else 0)
    preview_quality = 2 if preview else 0
    safety = 2
    total = prompt_understanding + file_action + homepage + preview_quality + safety
    notes = []
    if bridge:
        notes.append(f"bridge={bridge.get('status')}")
    if explanation_only:
        total = min(total, 3)
        notes.append("explanation-only")
    if markdown_only:
        total = min(total, 5)
        notes.append("markdown-only")
    if readme_only:
        total = min(total, 5)
        notes.append("README-only")
    if changed and not preview:
        total = min(total, 6)
        notes.append("file edit without openable preview")
    label = "GO" if total >= 8 else "WARNING" if total >= 5 else "NO-GO"
    return {"label": label, "total": total, "components": {"prompt_understanding": prompt_understanding, "file_action": file_action, "homepage": homepage, "preview_quality": preview_quality, "safety": safety}, "notes": notes}


def label_only(label: str, reason: str) -> dict[str, Any]:
    return {"label": label, "total": None if label in {"TIMEOUT", "BLOCKED", "MANUAL_REQUIRED", "CONTAMINATED"} else 0, "reason": reason, "notes": [reason]}


def write_lane_common(lane_dir: Path, trace: dict[str, Any], score: dict[str, Any], result: CmdResult) -> None:
    write(lane_dir / "path-trace.json", json.dumps(trace, indent=2))
    write(lane_dir / "score.json", json.dumps(score, indent=2))
    write(lane_dir / "status.txt", score["label"] + "\n")
    write(lane_dir / "command-log.txt", f"command: {trace.get('command', display_command(result.command))}\nelapsed_seconds: {result.elapsed}\nexit_code: {result.returncode}\n")
    if not (lane_dir / "prompt-transcript.txt").exists():
        write(lane_dir / "prompt-transcript.txt", result.text)
    if not (lane_dir / "tool-events.jsonl").exists():
        write(lane_dir / "tool-events.jsonl", "")


def write_raw_common(lane_dir: Path, trace: dict[str, Any], score: dict[str, Any], result: CmdResult) -> None:
    write(lane_dir / "path-trace.json", json.dumps(trace, indent=2))
    write(lane_dir / "score.json", json.dumps(score, indent=2))
    write(lane_dir / "status.txt", score["label"] + "\n")
    write(lane_dir / "command-log.txt", f"command: {trace.get('command')}\nelapsed_seconds: {result.elapsed}\nexit_code: {result.returncode}\n")


def row_from_trace(trace: dict[str, Any], score: dict[str, Any], preview: str) -> dict[str, Any]:
    return {
        "lane": trace.get("lane_name", ""),
        "shell": trace.get("shell", ""),
        "model_target": trace.get("model_target", ""),
        "model_observed": trace.get("model_observed", "unknown"),
        "execution_mode": trace.get("execution_mode", ""),
        "status": score.get("label", ""),
        "score": score.get("total"),
        "time": trace.get("elapsed_seconds", 0.0),
        "files_changed": trace.get("files_changed", []),
        "preview": preview,
        "notes": "; ".join(score.get("notes", []) or [trace.get("notes", "")]).strip("; "),
    }


def collect_rows() -> list[dict[str, Any]]:
    rows = []
    for trace_path in sorted(LANES_DIR.glob("*/path-trace.json")):
        lane_dir = trace_path.parent
        trace = json.loads(read(trace_path) or "{}")
        score = json.loads(read(lane_dir / "score.json") or "{}")
        rows.append(row_from_trace(trace, score, trace.get("preview_path", "")))
    return rows


def finalize(results: list[dict[str, Any]], env: dict[str, Any], started: float) -> dict[str, Any]:
    anti = anti_check()
    real_app_touched = False
    if anti["status"] == "CONTAMINATED":
        for row in results:
            if row["status"] not in {"MANUAL_REQUIRED", "TIMEOUT", "BLOCKED"}:
                row["status"] = "CONTAMINATED"
    summary = {
        "status": "DONE" if anti["status"] == "CLEAN" else "CONTAMINATED",
        "created_at": utc_now(),
        "elapsed_seconds": round(time.time() - started, 3),
        "duplicate_ollama_warning": bool(env.get("duplicate_ollama_warning")),
        "real_app_touched": real_app_touched,
        "anti_cheat_status": anti["status"],
        "results": results,
        "fastest_usable_lane": fastest_usable(results),
        "best_homepage_lane": best_homepage(results),
        "best_local_lane": best_by_shell(results, {"continue", "raw", "source-proxy"}),
        "best_cloud_lane": best_by_shell(results, {"raw-api"}),
        "ready_for_3_prompt_gauntlet": any(r["status"] == "GO" for r in results),
    }
    write(OUTPUT_ROOT / "summary.json", json.dumps(summary, indent=2))
    write(OUTPUT_ROOT / "manifest.json", json.dumps(summary, indent=2))
    write(OUTPUT_ROOT / "anti-cheat-report.json", json.dumps(anti, indent=2))
    write_summary_md(summary)
    write_index(summary)
    write_closeout(summary)
    return summary


def fastest_usable(rows: list[dict[str, Any]]) -> str:
    usable = [r for r in rows if r["status"] in {"GO", "WARNING"} and r["files_changed"]]
    if not usable:
        return "none"
    return min(usable, key=lambda r: float(r.get("time") or 999999))["lane"]


def best_homepage(rows: list[dict[str, Any]]) -> str:
    usable = [r for r in rows if r.get("preview")]
    if not usable:
        return "none"
    return max(usable, key=lambda r: (r.get("score") or 0, -float(r.get("time") or 999999)))["lane"]


def best_by_shell(rows: list[dict[str, Any]], shells: set[str]) -> str:
    usable = [r for r in rows if r.get("shell") in shells and r["status"] in {"GO", "WARNING"}]
    if not usable:
        return "none"
    return max(usable, key=lambda r: (r.get("score") or 0, -float(r.get("time") or 999999)))["lane"]


def write_summary_md(summary: dict[str, Any]) -> None:
    lines = [
        "# Ultimate Agent Comparison Round 1",
        "",
        "| Lane | Shell | Model Target | Model Observed | Execution Mode | Status | Score | Time | Files Changed | Preview | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in summary["results"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["lane"]),
                    str(row["shell"]),
                    str(row["model_target"]),
                    str(row["model_observed"]),
                    str(row["execution_mode"]),
                    str(row["status"]),
                    str(row["score"]),
                    str(row["time"]),
                    html.escape(", ".join(row["files_changed"]) or "none"),
                    row["preview"] or "none",
                    html.escape(row["notes"] or ""),
                ]
            )
            + " |"
        )
    write(OUTPUT_ROOT / "summary.md", "\n".join(lines) + "\n")


def write_closeout(summary: dict[str, Any]) -> None:
    rows = summary["results"]
    ran = [r["lane"] for r in rows if r["status"] not in {"MANUAL_REQUIRED", "BLOCKED"}]
    skipped = [r["lane"] for r in rows if r["status"] in {"MANUAL_REQUIRED", "BLOCKED"}]
    explanation = [r["lane"] for r in rows if "explanation-only" in r.get("notes", "")]
    markdown = [r["lane"] for r in rows if "markdown-only" in r.get("notes", "")]
    previews = [r["lane"] for r in rows if r.get("preview")]
    cq = next((r for r in rows if r["lane"] == "continue-qwen-bridged"), {})
    lines = [
        "# Ultimate Agent Comparison Round 1 Closeout",
        "",
        f"Final status: {summary['status']}",
        f"Lanes ran: {', '.join(ran) or 'none'}",
        f"Lanes skipped/manual-required: {', '.join(skipped) or 'none'}",
        f"Fastest usable lane: {summary['fastest_usable_lane']}",
        f"Best homepage lane: {summary['best_homepage_lane']}",
        f"Best local lane: {summary['best_local_lane']}",
        f"Best cloud lane: {summary['best_cloud_lane']}",
        f"Explanation-only lanes: {', '.join(explanation) or 'none'}",
        f"Markdown stub lanes: {', '.join(markdown) or 'none'}",
        f"Openable homepage preview lanes: {', '.join(previews) or 'none'}",
        f"Continue + Qwen status/score/time: {cq.get('status')} / {cq.get('score')} / {cq.get('time')}",
        f"Continue + Qwen improved beyond previous warning result: {cq.get('status') == 'GO'}",
        f"Any lane ready for 3-prompt gauntlet: {summary['ready_for_3_prompt_gauntlet']}",
        "Source Proxy needs route fixes before comparison: see source-proxy lane status and diagnostics",
        f"Anti-cheat status: {summary['anti_cheat_status']}",
        f"Real app touched: {summary['real_app_touched']}",
        "No Plan 4 started.",
        f"Clean command: python3 scripts/agent-trials/run-ultimate-agent-comparison-round1.py --clean",
    ]
    write(OUTPUT_ROOT / "closeout.md", "\n".join(lines) + "\n")


def write_index(summary: dict[str, Any]) -> None:
    rows = summary["results"]
    cards = []
    for row in rows:
        preview = row["preview"]
        if preview:
            preview_html = f'<a href="{html.escape(preview)}">Open preview</a>'
        else:
            preview_html = "<p>No preview generated because this lane did not produce an openable homepage.</p>"
        cards.append(
            f"<section><h2>{html.escape(row['lane'])}</h2><dl>"
            f"<dt>Status</dt><dd>{html.escape(str(row['status']))}</dd>"
            f"<dt>Score</dt><dd>{html.escape(str(row['score']))}</dd>"
            f"<dt>Mode</dt><dd>{html.escape(str(row['execution_mode']))}</dd>"
            f"<dt>Time</dt><dd>{html.escape(str(row['time']))}</dd>"
            f"<dt>Files</dt><dd>{html.escape(', '.join(row['files_changed']) or 'none')}</dd>"
            f"</dl>{preview_html}</section>"
        )
    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ultimate Agent Comparison Round 1</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f6f7f9; color: #202733; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 28px; }}
    section {{ background: #fff; border: 1px solid #d8dee8; border-radius: 8px; padding: 16px; margin: 14px 0; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; }}
    th, td {{ border-bottom: 1px solid #d8dee8; padding: 8px; text-align: left; vertical-align: top; }}
    dt {{ font-weight: 700; }}
    dd {{ margin: 0 0 8px; }}
    pre {{ white-space: pre-wrap; background: #111827; color: #e5e7eb; padding: 12px; border-radius: 6px; overflow: auto; }}
  </style>
</head>
<body>
<main>
  <h1>Ultimate Agent Comparison Round 1</h1>
  <section>
    <dl>
      <dt>Status</dt><dd>{html.escape(summary['status'])}</dd>
      <dt>Fastest usable lane</dt><dd>{html.escape(summary['fastest_usable_lane'])}</dd>
      <dt>Best homepage lane</dt><dd>{html.escape(summary['best_homepage_lane'])}</dd>
      <dt>Duplicate Ollama warning</dt><dd>{html.escape(str(summary['duplicate_ollama_warning']))}</dd>
      <dt>Anti-cheat</dt><dd>{html.escape(summary['anti_cheat_status'])}</dd>
      <dt>Real app touched</dt><dd>{html.escape(str(summary['real_app_touched']))}</dd>
    </dl>
  </section>
  {''.join(cards)}
</main>
</body>
</html>
"""
    write(OUTPUT_ROOT / "index.html", body)


def anti_check() -> dict[str, Any]:
    paths = [Path(__file__)]
    paths.extend(OUTPUT_ROOT.glob("lanes/*/path-trace.json"))
    paths.extend(OUTPUT_ROOT.glob("lanes/*/score.json"))
    hits: list[str] = []
    for path in paths:
        text = read(path)
        for left, right in BAD_PIECES:
            bad = left + right
            if bad in text:
                hits.append(f"{rel(path)}:{bad}")
    return {"status": "CONTAMINATED" if hits else "CLEAN", "hits": hits}


def mark_running(status: dict[str, Any], lane: str) -> None:
    status["current_lane"] = lane
    write_status(status, f"{lane}:RUNNING")


def finish_lane(status: dict[str, Any], lane: str, label: str) -> None:
    status["completed_lanes"].append(lane)
    status["current_lane"] = ""
    write_status(status, f"{lane}:{label}")


def write_status(status: dict[str, Any], event: str) -> None:
    status["last_event"] = event
    status["elapsed_seconds"] = status.get("elapsed_seconds", 0.0)
    write(OUTPUT_ROOT / "status.json", json.dumps(status, indent=2))
    write_event(event)


def write_event(event: str) -> None:
    append(OUTPUT_ROOT / "live-events.jsonl", json.dumps({"ts": utc_now(), "event": event}) + "\n")


def run_live(command: list[str], *, cwd: Path, timeout: int, transcript_path: Path, event_path: Path) -> CmdResult:
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    with transcript_path.open("w", encoding="utf-8", errors="replace") as transcript, event_path.open("w", encoding="utf-8") as events:
        transcript.write(f"$ {display_command(command)}\n")
        transcript.flush()
        try:
            proc = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", preexec_fn=os.setsid if os.name != "nt" else None)
        except FileNotFoundError as error:
            return CmdResult(command, 127, "", str(error), round(time.time() - started, 3))

        def reader(stream: Any, chunks: list[str], label: str) -> None:
            for line in iter(stream.readline, ""):
                chunks.append(line)
                transcript.write(f"[{label}] {line}")
                transcript.flush()

        threads = [
            threading.Thread(target=reader, args=(proc.stdout, stdout_chunks, "stdout"), daemon=True),
            threading.Thread(target=reader, args=(proc.stderr, stderr_chunks, "stderr"), daemon=True),
        ]
        for thread in threads:
            thread.start()
        timed_out = False
        while proc.poll() is None:
            elapsed = time.time() - started
            events.write(json.dumps({"ts": utc_now(), "elapsed_seconds": round(elapsed, 3), "pid": proc.pid}) + "\n")
            events.flush()
            if elapsed >= timeout:
                timed_out = True
                kill_tree(proc)
                break
            time.sleep(1)
        for thread in threads:
            thread.join(timeout=2)
        elapsed = round(time.time() - started, 3)
        code: int | str = "TIMEOUT" if timed_out else (proc.returncode if proc.returncode is not None else -1)
        transcript.write(f"\n[exit] {code}\n[elapsed_seconds] {elapsed}\n")
        return CmdResult(command, code, "".join(stdout_chunks), "".join(stderr_chunks), elapsed, timed_out)


def run_capture(command: list[str], timeout: int, missing_ok: bool = False) -> CmdResult:
    started = time.time()
    try:
        proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return CmdResult(command, proc.returncode, proc.stdout, proc.stderr, round(time.time() - started, 3))
    except FileNotFoundError as error:
        if not missing_ok:
            raise
        return CmdResult(command, 127, "", str(error), round(time.time() - started, 3))
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return CmdResult(command, "TIMEOUT", stdout, stderr, round(time.time() - started, 3), True)


def kill_tree(proc: subprocess.Popen[str]) -> None:
    try:
        if os.name != "nt":
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            time.sleep(2)
            if proc.poll() is None:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        else:
            proc.kill()
    except Exception:
        proc.kill()


def snapshot(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    if not root.exists():
        return files
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            files[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    return files


def changed_files(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return [name for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)]


def diff_snapshots(before: dict[str, str], after: dict[str, str]) -> str:
    chunks: list[str] = []
    for name in changed_files(before, after):
        chunks.extend(difflib.unified_diff(before.get(name, "").splitlines(keepends=True), after.get(name, "").splitlines(keepends=True), fromfile=f"a/{name}", tofile=f"b/{name}"))
    return "".join(chunks)


def choose_preview(workspace: Path, lane_dir: Path) -> str:
    for path in sorted(workspace.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".html", ".htm"}:
            return path.relative_to(OUTPUT_ROOT).as_posix()
    return ""


def observed_continue_model(workspace: Path, result: CmdResult) -> str:
    text = result.stdout + result.stderr
    for model in ("qwen2.5-coder:7b", "gpt-4o-mini", "hermes4", "gemma", "gemini"):
        if model.lower() in text.lower():
            return model
    session_model = latest_continue_session_model(workspace)
    return session_model or "MODEL_SELECTION_UNKNOWN"


def latest_continue_session_model(workspace: Path) -> str:
    sessions_dir = Path.home() / ".continue/sessions"
    if not sessions_dir.exists():
        return ""
    try:
        candidates = sorted(
            [p for p in sessions_dir.glob("*.json") if p.name != "sessions.json"],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return ""
    target = str(workspace)
    for path in candidates[:30]:
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        if not isinstance(data, dict) or data.get("workspaceDirectory") != target:
            continue
        usage = data.get("usage", {})
        if isinstance(usage, dict):
            model = usage.get("model")
            if isinstance(model, str) and model:
                return model
        history = data.get("history", [])
        if isinstance(history, list):
            for item in reversed(history):
                if not isinstance(item, dict):
                    continue
                message = item.get("message", {})
                if not isinstance(message, dict):
                    continue
                usage = message.get("usage", {})
                if isinstance(usage, dict):
                    model = usage.get("model")
                    if isinstance(model, str) and model:
                        return model
    return ""


def first_model(models: list[str], candidates: list[str]) -> str:
    for candidate in candidates:
        for model in models:
            if model == candidate or model.startswith(candidate + ":"):
                return model
    return ""


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value)


def display_command(command: list[str]) -> str:
    return " ".join(quote(part) for part in command)


def quote(value: str) -> str:
    if re.fullmatch(r"[\w./:@=\\-]+", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def scrub_args(arguments: Any) -> Any:
    if isinstance(arguments, dict):
        return {k: ("***" if "key" in k.lower() else v) for k, v in arguments.items()}
    return arguments


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def serve(host: str, port: int) -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    os.chdir(OUTPUT_ROOT)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self) -> None:
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    try:
        with http.server.ThreadingHTTPServer((host, port), Handler) as server:
            print(f"Serving {OUTPUT_ROOT} at http://{host}:{port}/")
            server.serve_forever()
    except OSError as error:
        print(f"Serve failed on {host}:{port}: {error}")
        return 1
    return 0


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        try:
            return path.relative_to(OUTPUT_ROOT).as_posix()
        except ValueError:
            return str(path)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="replace")


def append(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", errors="replace") as handle:
        handle.write(text)


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    raise SystemExit(main())
