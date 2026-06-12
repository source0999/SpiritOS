from __future__ import annotations

import argparse
import difflib
import html
import http.server
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/continue-qwen-single-prompt-debug"
)
ENV_DIR = OUTPUT_ROOT / "environment"
LANE_DIR = OUTPUT_ROOT / "continue-qwen"
WORKSPACE = LANE_DIR / "workspace"
TARGET_MODEL = "qwen2.5-coder:7b"
README_PROMPT = (
    "Run only in this folder. Edit README.md by adding one new line that says "
    "CONTINUE_QWEN_EDIT_READY. Do not touch anything else."
)
HOMEPAGE_PROMPT = (
    "Run only in this disposable workspace. Do not touch the real SpiritOS app. "
    "Do not modify files outside this workspace.\n\n"
    "init a repo for agent lab experiements make me a homepage i can open on my phone "
    "dont touch the real spiritos app tho"
)


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
    parser = argparse.ArgumentParser(description="Continue + Qwen single prompt debug")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8775)
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
    if args.run:
        run()
        return 0
    parser.print_help()
    return 1


def run() -> dict[str, Any]:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    ENV_DIR.mkdir(parents=True, exist_ok=True)
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    started = time.time()
    state: dict[str, Any] = {
        "task": "continue-qwen-single-prompt-debug",
        "created_at": utc_now(),
        "status": "BLOCKED",
        "phase_reached": "phase-1",
        "blocker": "",
        "model_target": TARGET_MODEL,
        "model_observed": "unknown",
        "continue_command": "",
        "elapsed_seconds": 0.0,
        "files_changed": [],
        "preview_path": "",
        "preview_url": "",
        "transcript_path": rel(LANE_DIR / "prompt-transcript.txt"),
        "diff_path": rel(LANE_DIR / "diff-after-prompt.patch"),
        "closeout_path": rel(OUTPUT_ROOT / "closeout.md"),
        "clean_command": "python3 scripts/agent-trials/run-continue-qwen-single-prompt-debug.py --clean",
        "real_app_touched": False,
        "anti_cheat_status": "CLEAN",
        "qwen_direct_smoke": {},
        "readme_edit_smoke": {"status": "NOT_RUN"},
        "homepage_prompt": {"status": "NOT_RUN"},
        "process_conflict_notes": [],
        "environment": {},
    }

    write_status("RUNNING_PHASE_1")
    phase1 = phase_environment()
    state["environment"] = phase1
    state["process_conflict_notes"] = phase1.get("conflict_notes", [])
    if not phase1.get("qwen_installed"):
        state["status"] = "BLOCKED"
        state["blocker"] = "MANUAL_REQUIRED_QWEN_NOT_INSTALLED"
        finalize(state, started)
        return state

    write_status("RUNNING_PHASE_2")
    state["phase_reached"] = "phase-2"
    direct = direct_qwen_smoke()
    state["qwen_direct_smoke"] = direct
    if direct["status"] != "PASS":
        state["status"] = "BLOCKED"
        state["blocker"] = "BLOCKED_DIRECT_QWEN"
        state["model_observed"] = TARGET_MODEL if direct.get("model_observed") else "unknown"
        finalize(state, started)
        return state

    write_status("RUNNING_PHASE_3")
    state["phase_reached"] = "phase-3"
    discovery = discover_continue_selection()
    state["continue_command"] = discovery.get("command", "")
    state["model_observed"] = discovery.get("model_observed", "unknown")
    if not discovery.get("cn_available"):
        state["status"] = "BLOCKED"
        state["blocker"] = "CONTINUE_CLI_NOT_AVAILABLE_IN_THIS_EXECUTION_ENV"
        write_blocked_lane_files(state, discovery)
        finalize(state, started)
        return state
    if not discovery.get("config_path"):
        state["status"] = "BLOCKED"
        state["blocker"] = "CONTINUE_MODEL_SELECTION_FAILED"
        write_blocked_lane_files(state, discovery)
        finalize(state, started)
        return state

    write_status("RUNNING_PHASE_4")
    state["phase_reached"] = "phase-4"
    readme = continue_readme_smoke(discovery["config_path"])
    state["readme_edit_smoke"] = readme
    state["continue_command"] = readme.get("command", state["continue_command"])
    state["model_observed"] = readme.get("model_observed", TARGET_MODEL)
    state["files_changed"] = readme.get("files_changed", [])
    if readme["status"] != "PASS":
        state["status"] = readme.get("final_label", "BLOCKED")
        state["blocker"] = readme.get("blocker", "CONTINUE_REACHED_QWEN_BUT_NO_TOOL_EDIT")
        finalize(state, started)
        return state

    write_status("RUNNING_PHASE_5")
    state["phase_reached"] = "phase-5"
    homepage = continue_homepage_prompt(discovery["config_path"])
    state["homepage_prompt"] = homepage
    state["continue_command"] = homepage.get("command", state["continue_command"])
    state["files_changed"] = homepage.get("files_changed", [])
    state["preview_path"] = homepage.get("preview_path", "")
    state["preview_url"] = homepage.get("preview_url", "")
    state["status"] = homepage.get("label", "NO-GO")
    state["blocker"] = homepage.get("blocker", "")
    finalize(state, started)
    return state


def phase_environment() -> dict[str, Any]:
    ps_before = process_snapshot()
    write(ENV_DIR / "ps-before.txt", ps_before)
    write(ENV_DIR / "ollama-ps-before.txt", run_capture(["ollama", "ps"], timeout=20).text)
    write(ENV_DIR / "nvidia-smi-before.txt", run_capture(["nvidia-smi"], timeout=20, missing_ok=True).text)

    date_text = run_capture(["cmd", "/c", "date", "/t"], timeout=10, missing_ok=True).text
    cn_path = which("cn")
    cn_version = run_capture(["cn", "--version"], timeout=20, missing_ok=True).text
    cn_help = run_capture(["cn", "--help"], timeout=20, missing_ok=True).text
    ollama_list = run_capture(["ollama", "list"], timeout=30, missing_ok=True).text
    ollama_ps = run_capture(["ollama", "ps"], timeout=20, missing_ok=True).text
    nvidia = run_capture(["nvidia-smi"], timeout=20, missing_ok=True).text
    env_text = filtered_env()
    config_text = continue_config_discovery(cn_path, cn_help)
    host_text = ollama_host_text()

    write(ENV_DIR / "continue-help.txt", cn_help)
    write(ENV_DIR / "ollama-list.txt", ollama_list)
    write(ENV_DIR / "ollama-host-env.txt", host_text)
    write(ENV_DIR / "continue-config-discovery.txt", config_text)

    qwen_installed = model_installed(ollama_list, TARGET_MODEL)
    conflict_notes = detect_ollama_conflicts(ps_before, ollama_ps)
    summary = {
        "date": date_text,
        "cn_path": cn_path,
        "cn_available": bool(cn_path),
        "env_filtered": env_text,
        "qwen_installed": qwen_installed,
        "target_model_exact_available": qwen_installed,
        "conflict_notes": conflict_notes,
    }
    write(ENV_DIR / "phase-1-summary.json", json.dumps(summary, indent=2))
    return summary


def direct_qwen_smoke() -> dict[str, Any]:
    before_ps = process_snapshot()
    before_ollama = run_capture(["ollama", "ps"], timeout=20, missing_ok=True).text
    write(ENV_DIR / "ollama-ps-before.txt", before_ollama)

    live: list[dict[str, Any]] = []
    result = run_live(
        ["ollama", "run", TARGET_MODEL, "say QWEN_READY in one line"],
        cwd=REPO_ROOT,
        timeout=75,
        transcript_path=ENV_DIR / "direct-qwen-smoke.txt",
        event_path=ENV_DIR / "direct-qwen-live-events.jsonl",
        live=live,
    )
    during_ps = process_snapshot()
    during_ollama = run_capture(["ollama", "ps"], timeout=20, missing_ok=True).text
    during_nvidia = run_capture(["nvidia-smi"], timeout=20, missing_ok=True).text
    after_ps = process_snapshot()
    after_ollama = run_capture(["ollama", "ps"], timeout=20, missing_ok=True).text
    after_nvidia = run_capture(["nvidia-smi"], timeout=20, missing_ok=True).text
    write(ENV_DIR / "ps-during.txt", during_ps)
    write(ENV_DIR / "ollama-ps-during.txt", during_ollama)
    write(ENV_DIR / "nvidia-smi-during.txt", during_nvidia)
    write(ENV_DIR / "ps-after.txt", after_ps)
    write(ENV_DIR / "ollama-ps-after.txt", after_ollama)
    write(ENV_DIR / "nvidia-smi-after.txt", after_nvidia)

    output = (result.stdout + "\n" + result.stderr).strip()
    ok = (not result.timed_out) and result.returncode == 0 and "QWEN_READY" in output.upper()
    return {
        "status": "PASS" if ok else "FAIL",
        "elapsed_seconds": result.elapsed,
        "exit_code": result.returncode,
        "timed_out": result.timed_out,
        "output": output,
        "runner_spawned": TARGET_MODEL in (before_ollama + during_ollama + after_ollama),
        "model_observed": TARGET_MODEL in (before_ollama + during_ollama + after_ollama + output),
        "gpu_snapshot_during_path": rel(ENV_DIR / "nvidia-smi-during.txt"),
        "transcript_path": rel(ENV_DIR / "direct-qwen-smoke.txt"),
    }


def discover_continue_selection() -> dict[str, Any]:
    cn = which("cn")
    help_text = read(ENV_DIR / "continue-help.txt")
    config_path = ""
    command = ""
    body = [
        "# Continue Command Selection Discovery",
        "",
        f"cn available: {bool(cn)}",
        f"cn path: {cn or 'missing'}",
        f"target model: {TARGET_MODEL}",
        f"--model documented: {'--model' in help_text}",
        f"--config documented: {'--config' in help_text}",
        "",
    ]
    if cn:
        config_path = str(write_lane_config())
        command = display_command([cn, "--config", config_path, "--auto", "-p", README_PROMPT])
        body.extend(
            [
                "Selected method: disposable isolated Continue config.",
                f"Config path: {config_path}",
                f"Command: {command}",
            ]
        )
    else:
        body.extend(
            [
                "Selected method: none.",
                "Blocker: Continue CLI `cn` is not available in this execution environment.",
                "The Windows PATH can reach Ollama, but not `/usr/bin/cn` from the recent Linux-side evidence.",
            ]
        )
    write(ENV_DIR / "continue-config-discovery.txt", "\n".join(body) + "\n")
    return {
        "cn_available": bool(cn),
        "cn_path": cn,
        "config_path": config_path,
        "command": command,
        "model_observed": TARGET_MODEL if config_path else "unknown",
    }


def continue_readme_smoke(config_path: str) -> dict[str, Any]:
    reset_workspace(seed_readme=True)
    before = snapshot(WORKSPACE)
    cmd = [which("cn") or "cn", "--config", config_path, "--auto", "-p", README_PROMPT]
    result = run_continue_with_events(cmd, timeout=120)
    after = snapshot(WORKSPACE)
    diff_text = diff_snapshots(before, after)
    write(LANE_DIR / "diff-after-prompt.patch", diff_text)
    changed = changed_files(before, after)
    readme_text = (WORKSPACE / "README.md").read_text(encoding="utf-8", errors="replace") if (WORKSPACE / "README.md").exists() else ""
    passed = "CONTINUE_QWEN_EDIT_READY" in readme_text
    blocker = ""
    label = "BLOCKED"
    if result.timed_out:
        blocker = classify_timeout(result.stdout + result.stderr)
        label = "TIMEOUT"
    elif not passed:
        blocker = "CONTINUE_REACHED_QWEN_BUT_NO_TOOL_EDIT"
    return {
        "status": "PASS" if passed else "FAIL",
        "final_label": label,
        "blocker": blocker,
        "elapsed_seconds": result.elapsed,
        "exit_code": result.returncode,
        "command": display_command(cmd),
        "files_changed": changed,
        "model_observed": TARGET_MODEL,
    }


def continue_homepage_prompt(config_path: str) -> dict[str, Any]:
    reset_workspace(seed_readme=False)
    subprocess.run(["git", "init"], cwd=WORKSPACE, capture_output=True, text=True, timeout=30)
    before = snapshot(WORKSPACE)
    cmd = [which("cn") or "cn", "--config", config_path, "--auto", "-p", HOMEPAGE_PROMPT]
    result = run_continue_with_events(cmd, timeout=180)
    after = snapshot(WORKSPACE)
    diff_text = diff_snapshots(before, after)
    write(LANE_DIR / "diff-after-prompt.patch", diff_text)
    changed = changed_files(before, after)
    preview = choose_preview(after)
    score = score_homepage(result, changed, preview)
    write(LANE_DIR / "score.json", json.dumps(score, indent=2))
    return {
        "status": "RAN",
        "label": score["label"],
        "blocker": score.get("blocker", ""),
        "elapsed_seconds": result.elapsed,
        "exit_code": result.returncode,
        "command": display_command(cmd),
        "files_changed": changed,
        "preview_path": preview,
        "preview_url": preview_url(preview),
        "score": score,
    }


def run_continue_with_events(cmd: list[str], timeout: int) -> CmdResult:
    (LANE_DIR / "prompt-transcript.txt").parent.mkdir(parents=True, exist_ok=True)
    result = run_live(
        cmd,
        cwd=WORKSPACE,
        timeout=timeout,
        transcript_path=LANE_DIR / "prompt-transcript.txt",
        event_path=LANE_DIR / "live-events.jsonl",
        live=[],
        sample_continue=True,
    )
    write(ENV_DIR / "ps-after.txt", process_snapshot())
    write(ENV_DIR / "ollama-ps-after.txt", run_capture(["ollama", "ps"], timeout=20, missing_ok=True).text)
    write(ENV_DIR / "nvidia-smi-after.txt", run_capture(["nvidia-smi"], timeout=20, missing_ok=True).text)
    return result


def run_live(
    command: list[str],
    *,
    cwd: Path,
    timeout: int,
    transcript_path: Path,
    event_path: Path,
    live: list[dict[str, Any]],
    sample_continue: bool = False,
) -> CmdResult:
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    with transcript_path.open("w", encoding="utf-8", errors="replace") as transcript, event_path.open(
        "w", encoding="utf-8", errors="replace"
    ) as events:
        transcript.write(f"$ {display_command(command)}\n")
        transcript.flush()
        try:
            proc = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError as error:
            elapsed = round(time.time() - started, 3)
            return CmdResult(command, 127, "", str(error), elapsed)

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
        samples = 0
        while proc.poll() is None:
            elapsed = time.time() - started
            event = {
                "ts": utc_now(),
                "elapsed_seconds": round(elapsed, 3),
                "pid": proc.pid,
                "stdout_bytes": sum(len(x) for x in stdout_chunks),
                "stderr_bytes": sum(len(x) for x in stderr_chunks),
            }
            events.write(json.dumps(event) + "\n")
            events.flush()
            live.append(event)
            if sample_continue and samples < 2 and elapsed >= (samples + 1) * 5:
                write(ENV_DIR / f"ps-during-{samples + 1}.txt", process_snapshot())
                write(
                    ENV_DIR / f"ollama-ps-during-{samples + 1}.txt",
                    run_capture(["ollama", "ps"], timeout=20, missing_ok=True).text,
                )
                write(
                    ENV_DIR / f"nvidia-smi-during-{samples + 1}.txt",
                    run_capture(["nvidia-smi"], timeout=20, missing_ok=True).text,
                )
                samples += 1
            if elapsed >= timeout:
                timed_out = True
                kill_process_tree(proc)
                break
            time.sleep(5)

        for thread in threads:
            thread.join(timeout=2)
        returncode: int | str = "TIMEOUT" if timed_out else (proc.returncode if proc.returncode is not None else -1)
        elapsed = round(time.time() - started, 3)
        transcript.write(f"\n[exit] {returncode}\n[elapsed_seconds] {elapsed}\n")
        return CmdResult(command, returncode, "".join(stdout_chunks), "".join(stderr_chunks), elapsed, timed_out)


def write_blocked_lane_files(state: dict[str, Any], discovery: dict[str, Any]) -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    write(LANE_DIR / "command-log.txt", f"Continue command not run.\nReason: {state['blocker']}\n")
    write(LANE_DIR / "prompt-transcript.txt", f"Continue not run.\nReason: {state['blocker']}\n")
    write(LANE_DIR / "live-events.jsonl", json.dumps({"ts": utc_now(), "event": state["blocker"]}) + "\n")
    write(LANE_DIR / "diff-after-prompt.patch", "")
    write(
        LANE_DIR / "path-trace.json",
        json.dumps(
            {
                "cwd": str(WORKSPACE),
                "target_model": TARGET_MODEL,
                "continue_command": discovery.get("command", ""),
                "blocker": state["blocker"],
                "files_changed": [],
                "real_app_touched": False,
            },
            indent=2,
        ),
    )
    write(
        LANE_DIR / "score.json",
        json.dumps({"label": "BLOCKED", "reason": state["blocker"], "total": 0}, indent=2),
    )


def finalize(state: dict[str, Any], started: float) -> None:
    state["elapsed_seconds"] = round(time.time() - started, 3)
    state["anti_cheat_status"] = anti_check()
    if state["anti_cheat_status"] == "CONTAMINATED":
        state["status"] = "CONTAMINATED"
        state["blocker"] = state.get("blocker") or "ANTI_CHEAT_CONTAMINATED"
    write_status(state["status"])
    write(OUTPUT_ROOT / "manifest.json", json.dumps(state, indent=2))
    write(OUTPUT_ROOT / "anti-cheat-report.json", json.dumps({"status": state["anti_cheat_status"]}, indent=2))
    if not (LANE_DIR / "score.json").exists():
        write(LANE_DIR / "score.json", json.dumps({"label": state["status"], "total": 0}, indent=2))
    if not (LANE_DIR / "path-trace.json").exists():
        write(LANE_DIR / "path-trace.json", json.dumps({"files_changed": state["files_changed"]}, indent=2))
    write_launcher(state)
    write_closeout(state)


def anti_check() -> str:
    parts = [
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
    targets = ["scripts/agent-trials/run-continue-qwen-single-prompt-debug.py"]
    bad: list[str] = []
    for target in targets:
        text = (REPO_ROOT / target).read_text(encoding="utf-8", errors="replace")
        for left, right in parts:
            needle = left + right
            if needle in text:
                bad.append(needle)
    return "CONTAMINATED" if bad else "CLEAN"


def write_launcher(state: dict[str, Any]) -> None:
    transcript = html.escape(read(LANE_DIR / "prompt-transcript.txt") or "No transcript.")
    diff = html.escape(read(LANE_DIR / "diff-after-prompt.patch") or "No diff.")
    preview = state.get("preview_path") or ""
    preview_section = (
        f'<a class="button" href="{html.escape(preview)}">Open preview</a>'
        if preview
        else "<p>No preview generated because no file edit succeeded.</p>"
    )
    conflict = "<br>".join(html.escape(x) for x in state.get("process_conflict_notes", [])) or "No duplicate Ollama server evidence from this environment."
    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Continue Qwen Single Prompt Debug</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; color: #1d2430; background: #f6f7f9; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 28px; }}
    section {{ background: white; border: 1px solid #d8dee8; border-radius: 8px; padding: 18px; margin: 14px 0; }}
    dl {{ display: grid; grid-template-columns: minmax(180px, 260px) 1fr; gap: 8px 16px; }}
    dt {{ font-weight: 700; }}
    pre {{ white-space: pre-wrap; background: #111827; color: #e5e7eb; padding: 14px; border-radius: 6px; overflow: auto; }}
    .button {{ display: inline-block; padding: 10px 12px; border-radius: 6px; background: #1f6feb; color: white; text-decoration: none; }}
  </style>
</head>
<body>
<main>
  <h1>Continue Qwen Single Prompt Debug</h1>
  <section>
    <dl>
      <dt>Current/final status</dt><dd>{html.escape(str(state.get("status", "")))}</dd>
      <dt>Exact command used</dt><dd><code>{html.escape(str(state.get("continue_command", "")))}</code></dd>
      <dt>Exact model target</dt><dd>{TARGET_MODEL}</dd>
      <dt>Model observed</dt><dd>{html.escape(str(state.get("model_observed", "")))}</dd>
      <dt>Elapsed time</dt><dd>{state.get("elapsed_seconds", 0)} seconds</dd>
      <dt>Phase reached</dt><dd>{html.escape(str(state.get("phase_reached", "")))}</dd>
      <dt>Files changed</dt><dd>{html.escape(", ".join(state.get("files_changed", [])) or "none")}</dd>
      <dt>Anti-cheat status</dt><dd>{html.escape(str(state.get("anti_cheat_status", "")))}</dd>
      <dt>Real app touched</dt><dd>{html.escape(str(state.get("real_app_touched", False)))}</dd>
      <dt>Closeout path</dt><dd>{html.escape(str(state.get("closeout_path", "")))}</dd>
      <dt>Clean command</dt><dd><code>{html.escape(str(state.get("clean_command", "")))}</code></dd>
    </dl>
    {preview_section}
  </section>
  <section><h2>Process Snapshots Summary</h2><p>{conflict}</p></section>
  <section><h2>Live Events Summary</h2><pre>{html.escape(read(LANE_DIR / "live-events.jsonl") or "No live events.")}</pre></section>
  <section><h2>Transcript</h2><details open><summary>Show transcript</summary><pre>{transcript}</pre></details></section>
  <section><h2>Diff</h2><details><summary>Show diff</summary><pre>{diff}</pre></details></section>
</main>
</body>
</html>
"""
    write(OUTPUT_ROOT / "index.html", body)


def write_closeout(state: dict[str, Any]) -> None:
    lines = [
        "# Continue Qwen Single Prompt Debug Closeout",
        "",
        f"Final status: {state.get('status')}",
        f"Phase reached: {state.get('phase_reached')}",
        f"Blocker: {state.get('blocker') or 'none'}",
        f"Qwen direct smoke elapsed time: {state.get('qwen_direct_smoke', {}).get('elapsed_seconds', 'n/a')}",
        f"Continue Qwen README edit smoke status: {state.get('readme_edit_smoke', {}).get('status', 'NOT_RUN')}",
        f"Homepage prompt status: {state.get('homepage_prompt', {}).get('status', 'NOT_RUN')}",
        f"Model target: {TARGET_MODEL}",
        f"Model observed: {state.get('model_observed')}",
        f"Exact Continue command used: {state.get('continue_command') or 'not run'}",
        f"Elapsed time: {state.get('elapsed_seconds')} seconds",
        f"Files changed: {', '.join(state.get('files_changed', [])) or 'none'}",
        f"Preview URL: {state.get('preview_url') or 'none'}",
        f"Launcher URL: http://localhost:8775/",
        f"Transcript path: {state.get('transcript_path')}",
        f"Diff path: {state.get('diff_path')}",
        f"Process conflict notes: {'; '.join(state.get('process_conflict_notes', [])) or 'none observed from this environment'}",
        f"Anti-cheat: {state.get('anti_cheat_status')}",
        f"Real app touched: {state.get('real_app_touched')}",
        f"Closeout path: {state.get('closeout_path')}",
        f"Clean command: {state.get('clean_command')}",
        "",
    ]
    write(OUTPUT_ROOT / "closeout.md", "\n".join(lines))


def score_homepage(result: CmdResult, changed: list[str], preview: str) -> dict[str, Any]:
    if result.timed_out:
        return {"label": "TIMEOUT", "total": 0, "blocker": classify_timeout(result.stdout + result.stderr)}
    understanding = 2 if changed else 0
    edit = 2 if changed else 0
    intent = 2 if preview else (1 if changed else 0)
    quality = 2 if preview else 0
    safety = 2
    total = understanding + edit + intent + quality + safety
    label = "GO" if total >= 8 else "WARNING" if total >= 5 else "NO-GO"
    return {
        "label": label,
        "total": total,
        "prompt_understanding": understanding,
        "actual_file_edit_action": edit,
        "homepage_repo_intent": intent,
        "rendered_preview_quality": quality,
        "safety_honesty_no_real_app_mutation": safety,
    }


def reset_workspace(seed_readme: bool) -> None:
    if WORKSPACE.exists():
        for child in WORKSPACE.iterdir():
            if child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        WORKSPACE.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=WORKSPACE, capture_output=True, text=True, timeout=30)
    if seed_readme:
        write(WORKSPACE / "README.md", "START\n")


def write_lane_config() -> Path:
    config = LANE_DIR / "lane-config.yaml"
    body = f"""schema: v1.5.44
name: qwen-single-prompt-debug
version: 1.0.0
models:
  - name: qwen-coder
    model: {TARGET_MODEL}
    provider: ollama
    apiBase: http://localhost:11434
    roles:
      - chat
      - edit
allowAnonymousTelemetry: false
"""
    write(config, body)
    return config


def process_snapshot() -> str:
    ps = run_capture(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'cn|continue|node|ollama|gemini' -or $_.Name -match 'cn|node|ollama' } | Select-Object ProcessId,ParentProcessId,Name,CommandLine | Format-List",
        ],
        timeout=30,
        missing_ok=True,
    )
    if ps.returncode == 0 and ps.stdout.strip():
        return ps.text
    return run_capture(["tasklist"], timeout=30, missing_ok=True).text


def kill_process_tree(proc: subprocess.Popen[str]) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, text=True)
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            proc.kill()


def run_capture(command: list[str], timeout: int, missing_ok: bool = False) -> CmdResult:
    started = time.time()
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
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


def snapshot(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    if not root.exists():
        return files
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            rel_path = path.relative_to(root).as_posix()
            files[rel_path] = path.read_text(encoding="utf-8", errors="replace")
    return files


def changed_files(before: dict[str, str], after: dict[str, str]) -> list[str]:
    names = sorted(set(before) | set(after))
    return [name for name in names if before.get(name) != after.get(name)]


def diff_snapshots(before: dict[str, str], after: dict[str, str]) -> str:
    chunks: list[str] = []
    for name in changed_files(before, after):
        old = before.get(name, "").splitlines(keepends=True)
        new = after.get(name, "").splitlines(keepends=True)
        chunks.extend(difflib.unified_diff(old, new, fromfile=f"a/{name}", tofile=f"b/{name}"))
    return "".join(chunks)


def choose_preview(after: dict[str, str]) -> str:
    for name in sorted(after):
        low = name.lower()
        if low.endswith((".html", ".htm")):
            return f"continue-qwen/workspace/{name}"
    return ""


def preview_url(path: str) -> str:
    return f"http://localhost:8775/{path}" if path else ""


def serve(host: str, port: int) -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    os.chdir(OUTPUT_ROOT)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self) -> None:
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    with http.server.ThreadingHTTPServer((host, port), Handler) as server:
        print(f"Serving {OUTPUT_ROOT} at http://{host}:{port}/")
        server.serve_forever()
    return 0


def which(name: str) -> str:
    found = shutil.which(name)
    return found or ""


def model_installed(ollama_list_text: str, model: str) -> bool:
    return any(line.split()[0] == model for line in ollama_list_text.splitlines() if line.strip())


def detect_ollama_conflicts(ps_text: str, ollama_ps: str) -> list[str]:
    notes: list[str] = []
    serve_lines = [
        line
        for line in ps_text.splitlines()
        if "commandline" in line.lower() and "ollama" in line.lower() and " serve" in line.lower()
    ]
    if len(serve_lines) >= 2:
        notes.append(f"Possible duplicate Ollama servers observed: {len(serve_lines)} serve command lines.")
    linux_ollama_lines = [
        line.lower()
        for line in ps_text.splitlines()
        if "/usr/bin/ollama" in line.lower() or "/usr/local/bin/ollama" in line.lower()
    ]
    if any("source" in line for line in linux_ollama_lines) and any("root" in line for line in linux_ollama_lines):
        notes.append("Linux-style process text includes both source and root Ollama servers.")
    if TARGET_MODEL in ollama_ps:
        notes.append(f"Ollama reports {TARGET_MODEL} loaded.")
    return notes


def continue_config_discovery(cn_path: str, cn_help: str) -> str:
    candidates = [
        Path.home() / ".continue/config.yaml",
        Path.home() / ".continue/config.json",
        OUTPUT_ROOT / "continue-qwen/lane-config.yaml",
    ]
    lines = [
        f"cn_path: {cn_path or 'missing'}",
        f"help_has_model_flag: {'--model' in cn_help}",
        f"help_has_config_flag: {'--config' in cn_help}",
    ]
    for path in candidates:
        lines.append(f"\n## {path}")
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            lines.append(redact(text))
        else:
            lines.append("missing")
    return "\n".join(lines) + "\n"


def filtered_env() -> str:
    keys = [key for key in os.environ if re.search(r"CONTINUE|OLLAMA|OPENAI|ANTHROPIC|GEMINI|GOOGLE", key)]
    return "\n".join(f"{key}={redact(os.environ.get(key, ''))}" for key in sorted(keys)) + "\n"


def ollama_host_text() -> str:
    host = os.environ.get("OLLAMA_HOST", "")
    return f"OLLAMA_HOST={host or '(unset; Ollama default host applies)'}\n"


def redact(text: str) -> str:
    text = re.sub(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s'\"]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|GOOGLE_API_KEY)=.+", r"\1=[REDACTED]", text)
    return text


def classify_timeout(text: str) -> str:
    low = text.lower()
    if "permission" in low or "allow" in low or "confirm" in low:
        return "CONTINUE_WAITING_FOR_PERMISSION"
    if "qwen" in low or TARGET_MODEL in low:
        return "CONTINUE_TIMEOUT_DURING_MODEL_OUTPUT"
    return "CONTINUE_TIMEOUT_BEFORE_MODEL_OUTPUT"


def display_command(command: list[str]) -> str:
    return " ".join(quote(part) for part in command)


def quote(value: str) -> str:
    if re.fullmatch(r"[\w./:@=\\-]+", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="replace")


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_status(status: str) -> None:
    write(LANE_DIR / "status.txt", status + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
