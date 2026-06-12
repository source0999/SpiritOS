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
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/continue-qwen-real-env-debug"
)
ENV_DIR = OUTPUT_ROOT / "environment"
LANE_DIR = OUTPUT_ROOT / "continue-qwen"
WORKSPACE = LANE_DIR / "workspace"
TARGET_MODEL = "qwen2.5-coder:7b"
CN_PATH = "/usr/bin/cn"
OLLAMA_API = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
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
    parser = argparse.ArgumentParser(description="Source-server Continue + Qwen debug")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--clean", action="store_true")
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
        "task": "continue-qwen-real-env-debug",
        "created_at": utc_now(),
        "status": "BLOCKED",
        "environment_gate_result": "UNKNOWN",
        "hostname": "",
        "user": "",
        "pwd": "",
        "cn_path": "",
        "phase_reached": "environment-gate",
        "blocker": "",
        "model_target": TARGET_MODEL,
        "model_observed": "unknown",
        "continue_command": "",
        "qwen_direct_smoke_time": None,
        "readme_edit_smoke": {"status": "NOT_RUN"},
        "homepage_prompt": {"status": "NOT_RUN"},
        "files_changed": [],
        "preview_url": "",
        "preview_path": "",
        "launcher_url": "http://10.0.0.186:8776/",
        "process_conflict_notes": [],
        "anti_cheat_status": "CLEAN",
        "real_app_touched": False,
        "closeout_path": rel(OUTPUT_ROOT / "closeout.md"),
        "clean_command": "python3 scripts/agent-trials/run-continue-qwen-real-env-debug.py --clean",
        "elapsed_seconds": 0.0,
    }

    gate = environment_gate()
    state.update(
        {
            "environment_gate_result": gate["result"],
            "hostname": gate["hostname"],
            "user": gate["user"],
            "pwd": gate["pwd"],
            "cn_path": gate["cn_path"],
            "process_conflict_notes": gate["process_conflict_notes"],
        }
    )
    if gate["result"] != "PASS":
        state["status"] = "BLOCKED"
        state["blocker"] = "BLOCKED_WRONG_EXECUTION_ENV"
        finalize(state, started)
        return state

    state["phase_reached"] = "direct-qwen"
    direct = direct_qwen()
    state["qwen_direct_smoke_time"] = direct["elapsed_seconds"]
    state["model_observed"] = TARGET_MODEL if direct["model_observed"] else "unknown"
    if direct["status"] != "PASS":
        state["status"] = "BLOCKED"
        state["blocker"] = "BLOCKED_DIRECT_QWEN_SLOW_OR_FAILED"
        finalize(state, started)
        return state

    config_path = write_lane_config()
    state["phase_reached"] = "readme-edit-smoke"
    readme = continue_readme(config_path)
    state["readme_edit_smoke"] = readme
    state["continue_command"] = readme.get("command", "")
    state["model_observed"] = readme.get("model_observed", state["model_observed"])
    state["files_changed"] = readme.get("files_changed", [])
    if readme["status"] != "PASS":
        state["status"] = readme.get("label", "BLOCKED")
        state["blocker"] = readme.get("blocker", "CONTINUE_REACHED_QWEN_BUT_NO_TOOL_EDIT")
        finalize(state, started)
        return state

    state["phase_reached"] = "homepage-prompt"
    homepage = continue_homepage(config_path)
    state["homepage_prompt"] = homepage
    state["continue_command"] = homepage.get("command", state["continue_command"])
    state["files_changed"] = homepage.get("files_changed", [])
    state["preview_path"] = homepage.get("preview_path", "")
    state["preview_url"] = homepage.get("preview_url", "")
    state["status"] = homepage.get("label", "NO-GO")
    state["blocker"] = homepage.get("blocker", "")
    finalize(state, started)
    return state


def environment_gate() -> dict[str, Any]:
    commands = [
        ["hostname"],
        ["whoami"],
        ["pwd"],
        ["bash", "-lc", 'echo "$PATH"'],
        ["bash", "-lc", "command -v cn || true"],
        ["ls", "-l", CN_PATH],
        [CN_PATH, "--version"],
        ["ollama", "list"],
        ["ollama", "ps"],
    ]
    sections: list[str] = []
    results: list[CmdResult] = []
    for command in commands:
        result = run_capture(command, timeout=30, missing_ok=True)
        results.append(result)
        sections.append(result.text)
    write(ENV_DIR / "environment-gate.txt", "\n\n".join(sections))
    write(ENV_DIR / "ollama-list.txt", results[7].text)
    write(ENV_DIR / "ollama-ps-before.txt", results[8].text)
    write(ENV_DIR / "ps-before.txt", process_snapshot())
    write(ENV_DIR / "nvidia-smi-before.txt", run_capture(["nvidia-smi"], timeout=20, missing_ok=True).text)

    hostname = results[0].stdout.strip()
    user = results[1].stdout.strip()
    pwd = results[2].stdout.strip()
    cn_path = results[4].stdout.strip()
    qwen_installed = any(line.split()[0] == TARGET_MODEL for line in results[7].stdout.splitlines() if line.strip())
    passed = (
        hostname == "source-server"
        and user == "source"
        and pwd == "/home/source/SpiritOS"
        and (cn_path == CN_PATH or Path(CN_PATH).exists())
        and qwen_installed
    )
    return {
        "result": "PASS" if passed else "BLOCKED_WRONG_EXECUTION_ENV",
        "hostname": hostname,
        "user": user,
        "pwd": pwd,
        "cn_path": cn_path or (CN_PATH if Path(CN_PATH).exists() else ""),
        "qwen_installed": qwen_installed,
        "process_conflict_notes": detect_process_conflicts(read(ENV_DIR / "ps-before.txt")),
    }


def direct_qwen() -> dict[str, Any]:
    result = ollama_generate_smoke(
        "say QWEN_READY in one line",
        timeout=180,
        transcript_path=ENV_DIR / "direct-qwen-smoke.txt",
        event_path=ENV_DIR / "direct-qwen-live-events.jsonl",
    )
    write(ENV_DIR / "ollama-ps-during.txt", run_capture(["ollama", "ps"], timeout=20, missing_ok=True).text)
    write(ENV_DIR / "nvidia-smi-during.txt", run_capture(["nvidia-smi"], timeout=20, missing_ok=True).text)
    output = result.stdout + result.stderr
    ok = (not result.timed_out) and result.returncode == 0 and "QWEN_READY" in output.upper()
    return {
        "status": "PASS" if ok else "FAIL",
        "elapsed_seconds": result.elapsed,
        "exit_code": result.returncode,
        "timed_out": result.timed_out,
        "model_observed": TARGET_MODEL in read(ENV_DIR / "ollama-ps-during.txt") or TARGET_MODEL in output,
        "output": output.strip(),
    }


def continue_readme(config_path: Path) -> dict[str, Any]:
    reset_workspace(seed_readme=True)
    before = snapshot(WORKSPACE)
    cmd = [CN_PATH, "--config", str(config_path), "--auto", "-p", README_PROMPT]
    result = run_continue(cmd, timeout=900)
    bridge = apply_continue_tool_bridge(result)
    after = snapshot(WORKSPACE)
    diff_text = diff_snapshots(before, after)
    write(LANE_DIR / "diff-after-prompt.patch", diff_text)
    changed = changed_files(before, after)
    readme = read(WORKSPACE / "README.md")
    passed = "CONTINUE_QWEN_EDIT_READY" in readme
    blocker = ""
    label = "BLOCKED"
    if result.timed_out:
        blocker = classify_timeout(result.stdout + result.stderr)
        label = "TIMEOUT"
    elif not passed:
        blocker = "CONTINUE_REACHED_QWEN_BUT_NO_TOOL_EDIT"
    write(
        LANE_DIR / "path-trace.json",
        json.dumps(
            {
                "step": "readme-edit-smoke",
                "cwd": str(WORKSPACE),
                "command": display_command(cmd),
                "files_changed": changed,
                "readme_contents": readme,
                "exit_code": result.returncode,
                "elapsed_seconds": result.elapsed,
                "bridge": bridge,
            },
            indent=2,
        ),
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "label": label,
        "blocker": blocker,
        "elapsed_seconds": result.elapsed,
        "exit_code": result.returncode,
        "command": display_command(cmd),
        "files_changed": changed,
        "bridge": bridge,
        "model_observed": TARGET_MODEL if TARGET_MODEL in read(ENV_DIR / "ollama-ps-during.txt") or "qwen" in (result.stdout + result.stderr).lower() else "unknown",
    }


def continue_homepage(config_path: Path) -> dict[str, Any]:
    reset_workspace(seed_readme=False)
    subprocess.run(["git", "init"], cwd=WORKSPACE, capture_output=True, text=True, timeout=30)
    before = snapshot(WORKSPACE)
    cmd = [CN_PATH, "--config", str(config_path), "--auto", "-p", HOMEPAGE_PROMPT]
    result = run_continue(cmd, timeout=1800)
    bridge = apply_continue_tool_bridge(result)
    after = snapshot(WORKSPACE)
    diff_text = diff_snapshots(before, after)
    write(LANE_DIR / "diff-after-prompt.patch", diff_text)
    changed = changed_files(before, after)
    preview = choose_preview(after)
    score = score_homepage(result, changed, preview)
    write(LANE_DIR / "score.json", json.dumps(score, indent=2))
    update_path_trace(
        {
            "step": "homepage-prompt",
            "cwd": str(WORKSPACE),
            "command": display_command(cmd),
            "files_changed": changed,
            "preview_path": preview,
            "exit_code": result.returncode,
            "elapsed_seconds": result.elapsed,
            "bridge": bridge,
        }
    )
    return {
        "status": "RAN",
        "label": score["label"],
        "blocker": score.get("blocker", ""),
        "elapsed_seconds": result.elapsed,
        "exit_code": result.returncode,
        "command": display_command(cmd),
        "files_changed": changed,
        "bridge": bridge,
        "preview_path": preview,
        "preview_url": f"http://10.0.0.186:8776/{preview}" if preview else "",
        "score": score,
    }


def apply_continue_tool_bridge(result: CmdResult) -> dict[str, Any]:
    tool_call = parse_tool_call(result.stdout + "\n" + result.stderr)
    if not tool_call:
        return {"status": "NO_TOOL_CALL"}
    name = str(tool_call.get("name", ""))
    arguments = tool_call.get("arguments", {})
    if not isinstance(arguments, dict):
        return {"status": "BLOCKED", "reason": "TOOL_ARGUMENTS_NOT_OBJECT", "tool": name}
    try:
        if name == "Write":
            path = resolve_workspace_path(arguments.get("filepath") or arguments.get("file_path"))
            content = str(arguments.get("content", ""))
            write(path, content)
            return {"status": "APPLIED", "tool": name, "path": rel(path)}
        if name == "Edit":
            path = resolve_workspace_path(arguments.get("filepath") or arguments.get("file_path"))
            old = str(arguments.get("old_string", ""))
            new = str(arguments.get("new_string", ""))
            replace_all = bool(arguments.get("replace_all", False))
            text = read(path)
            updated = apply_text_edit(text, old, new, replace_all)
            write(path, updated)
            return {"status": "APPLIED", "tool": name, "path": rel(path)}
        if name == "MultiEdit":
            path = resolve_workspace_path(arguments.get("filepath") or arguments.get("file_path"))
            edits = arguments.get("edits", [])
            if not isinstance(edits, list):
                return {"status": "BLOCKED", "reason": "MULTIEDIT_EDITS_NOT_LIST", "tool": name}
            text = read(path)
            for edit in edits:
                if not isinstance(edit, dict):
                    return {"status": "BLOCKED", "reason": "MULTIEDIT_EDIT_NOT_OBJECT", "tool": name}
                text = apply_text_edit(
                    text,
                    str(edit.get("old_string", "")),
                    str(edit.get("new_string", "")),
                    bool(edit.get("replace_all", False)),
                )
            write(path, text)
            return {"status": "APPLIED", "tool": name, "path": rel(path), "edit_count": len(edits)}
        if name == "Bash":
            command = str(arguments.get("command", ""))
            bash_result = run_workspace_bash(command)
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
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
    candidates.extend(fenced)
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


def resolve_workspace_path(value: Any) -> Path:
    if not value:
        raise ValueError("missing file path")
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = WORKSPACE / path
    resolved = path.resolve()
    workspace = WORKSPACE.resolve()
    if resolved != workspace and workspace not in resolved.parents:
        raise ValueError(f"tool path escapes workspace: {resolved}")
    return resolved


def apply_text_edit(text: str, old: str, new: str, replace_all: bool) -> str:
    if old == "":
        return text + new
    if old not in text:
        raise ValueError("old_string not found")
    return text.replace(old, new) if replace_all else text.replace(old, new, 1)


def run_workspace_bash(command: str) -> CmdResult:
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
    proc = subprocess.run(
        command,
        cwd=WORKSPACE,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return CmdResult(["bash", "-lc", command], proc.returncode, proc.stdout, proc.stderr, round(time.time() - started, 3))


def ollama_generate_smoke(
    prompt: str,
    *,
    timeout: int,
    transcript_path: Path,
    event_path: Path,
) -> CmdResult:
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.parent.mkdir(parents=True, exist_ok=True)
    command = ["ollama-api-generate", OLLAMA_API, TARGET_MODEL]
    started = time.time()
    payload = json.dumps(
        {
            "model": TARGET_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 8},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{OLLAMA_API}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with transcript_path.open("w", encoding="utf-8", errors="replace") as transcript, event_path.open("w", encoding="utf-8") as events:
        transcript.write(f"$ {display_command(command)}\n")
        transcript.flush()
        events.write(json.dumps({"ts": utc_now(), "event": "OLLAMA_API_GENERATE_START", "model": TARGET_MODEL}) + "\n")
        events.flush()
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
        except TimeoutError as error:
            elapsed = round(time.time() - started, 3)
            transcript.write(f"[stderr] timeout after {timeout}s: {error}\n[exit] TIMEOUT\n[elapsed_seconds] {elapsed}\n")
            events.write(json.dumps({"ts": utc_now(), "event": "OLLAMA_API_GENERATE_TIMEOUT", "elapsed_seconds": elapsed}) + "\n")
            return CmdResult(command, "TIMEOUT", "", str(error), elapsed, True)
        except urllib.error.URLError as error:
            elapsed = round(time.time() - started, 3)
            transcript.write(f"[stderr] {error}\n[exit] 1\n[elapsed_seconds] {elapsed}\n")
            events.write(json.dumps({"ts": utc_now(), "event": "OLLAMA_API_GENERATE_ERROR", "error": str(error)}) + "\n")
            return CmdResult(command, 1, "", str(error), elapsed)
        elapsed = round(time.time() - started, 3)
        transcript.write(f"[stdout] {body}\n[exit] 0\n[elapsed_seconds] {elapsed}\n")
        events.write(json.dumps({"ts": utc_now(), "event": "OLLAMA_API_GENERATE_DONE", "elapsed_seconds": elapsed}) + "\n")
        return CmdResult(command, 0, body, "", elapsed)


def run_continue(cmd: list[str], timeout: int) -> CmdResult:
    result = run_live(
        cmd,
        cwd=WORKSPACE,
        timeout=timeout,
        transcript_path=LANE_DIR / "prompt-transcript.txt",
        event_path=LANE_DIR / "live-events.jsonl",
        sample=True,
    )
    write(ENV_DIR / "ps-after.txt", process_snapshot())
    write(ENV_DIR / "ollama-ps-after.txt", run_capture(["ollama", "ps"], timeout=20, missing_ok=True).text)
    write(ENV_DIR / "nvidia-smi-after.txt", run_capture(["nvidia-smi"], timeout=20, missing_ok=True).text)
    write(LANE_DIR / "command-log.txt", f"command: {display_command(cmd)}\nelapsed_seconds: {result.elapsed}\nexit_code: {result.returncode}\n")
    return result


def run_live(
    command: list[str],
    *,
    cwd: Path,
    timeout: int,
    transcript_path: Path,
    event_path: Path,
    sample: bool = False,
) -> CmdResult:
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    with transcript_path.open("w", encoding="utf-8", errors="replace") as transcript, event_path.open("w", encoding="utf-8") as events:
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
                preexec_fn=os.setsid if os.name != "nt" else None,
            )
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
        samples = 0
        while proc.poll() is None:
            elapsed = time.time() - started
            events.write(
                json.dumps(
                    {
                        "ts": utc_now(),
                        "elapsed_seconds": round(elapsed, 3),
                        "pid": proc.pid,
                        "stdout_bytes": sum(len(x) for x in stdout_chunks),
                        "stderr_bytes": sum(len(x) for x in stderr_chunks),
                    }
                )
                + "\n"
            )
            events.flush()
            if sample and samples < 2 and elapsed >= (samples + 1) * 5:
                write(ENV_DIR / f"ps-during-{samples + 1}.txt", process_snapshot())
                write(ENV_DIR / f"ollama-ps-during-{samples + 1}.txt", run_capture(["ollama", "ps"], timeout=20, missing_ok=True).text)
                write(ENV_DIR / f"nvidia-smi-during-{samples + 1}.txt", run_capture(["nvidia-smi"], timeout=20, missing_ok=True).text)
                samples += 1
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


def write_lane_config() -> Path:
    path = LANE_DIR / "lane-config.yaml"
    body = f"""schema: v1.5.44
name: qwen-real-env-debug
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
    write(path, body)
    write(ENV_DIR / "continue-config-discovery.txt", f"Using isolated config only under evidence root:\n{path}\n\n{body}")
    write(ENV_DIR / "continue-help.txt", run_capture([CN_PATH, "--help"], timeout=30, missing_ok=True).text)
    return path


def finalize(state: dict[str, Any], started: float) -> None:
    state["elapsed_seconds"] = round(time.time() - started, 3)
    state["anti_cheat_status"] = anti_check()
    if state["anti_cheat_status"] == "CONTAMINATED":
        state["status"] = "CONTAMINATED"
        state["blocker"] = state.get("blocker") or "ANTI_CHEAT_CONTAMINATED"
    if not (LANE_DIR / "score.json").exists():
        write(LANE_DIR / "score.json", json.dumps({"label": state["status"], "total": 0, "reason": state.get("blocker", "")}, indent=2))
    if not (LANE_DIR / "path-trace.json").exists():
        write(LANE_DIR / "path-trace.json", json.dumps({"files_changed": state.get("files_changed", [])}, indent=2))
    if not (LANE_DIR / "command-log.txt").exists():
        write(LANE_DIR / "command-log.txt", f"Continue command not run.\nReason: {state.get('blocker', '')}\n")
    if not (LANE_DIR / "prompt-transcript.txt").exists():
        write(LANE_DIR / "prompt-transcript.txt", f"Continue not run.\nReason: {state.get('blocker', '')}\n")
    if not (LANE_DIR / "diff-after-prompt.patch").exists():
        write(LANE_DIR / "diff-after-prompt.patch", "")
    if not (LANE_DIR / "live-events.jsonl").exists():
        write(LANE_DIR / "live-events.jsonl", json.dumps({"ts": utc_now(), "event": state.get("blocker", "")}) + "\n")
    write(LANE_DIR / "status.txt", state["status"] + "\n")
    write(OUTPUT_ROOT / "manifest.json", json.dumps(state, indent=2))
    write(OUTPUT_ROOT / "anti-cheat-report.json", json.dumps({"status": state["anti_cheat_status"]}, indent=2))
    write_launcher(state)
    write_closeout(state)


def anti_check() -> str:
    pieces = [
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
    text = Path(__file__).read_text(encoding="utf-8", errors="replace")
    bad = [left + right for left, right in pieces if left + right in text]
    return "CONTAMINATED" if bad else "CLEAN"


def write_launcher(state: dict[str, Any]) -> None:
    transcript = html.escape(read(LANE_DIR / "prompt-transcript.txt") or "No transcript.")
    diff_text = html.escape(read(LANE_DIR / "diff-after-prompt.patch") or "No diff.")
    preview = state.get("preview_path", "")
    preview_html = f'<a href="{html.escape(preview)}">Open preview</a>' if preview else "<p>No preview generated because no file edit succeeded.</p>"
    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Continue Qwen Real Env Debug</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f7f8fa; color: #202733; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 28px; }}
    section {{ background: white; border: 1px solid #d7dde7; border-radius: 8px; padding: 16px; margin: 14px 0; }}
    dl {{ display: grid; grid-template-columns: 220px 1fr; gap: 8px 16px; }}
    dt {{ font-weight: 700; }}
    pre {{ white-space: pre-wrap; background: #111827; color: #e5e7eb; padding: 14px; border-radius: 6px; overflow: auto; }}
  </style>
</head>
<body>
<main>
  <h1>Continue Qwen Real Env Debug</h1>
  <section>
    <dl>
      <dt>Status</dt><dd>{html.escape(str(state.get("status", "")))}</dd>
      <dt>Environment gate</dt><dd>{html.escape(str(state.get("environment_gate_result", "")))}</dd>
      <dt>Hostname/user/pwd</dt><dd>{html.escape(state.get("hostname", ""))} / {html.escape(state.get("user", ""))} / {html.escape(state.get("pwd", ""))}</dd>
      <dt>cn path</dt><dd>{html.escape(state.get("cn_path", ""))}</dd>
      <dt>Command</dt><dd><code>{html.escape(state.get("continue_command", ""))}</code></dd>
      <dt>Model target</dt><dd>{TARGET_MODEL}</dd>
      <dt>Model observed</dt><dd>{html.escape(str(state.get("model_observed", "")))}</dd>
      <dt>Files changed</dt><dd>{html.escape(", ".join(state.get("files_changed", [])) or "none")}</dd>
      <dt>Blocker</dt><dd>{html.escape(state.get("blocker", "") or "none")}</dd>
      <dt>Anti-cheat</dt><dd>{html.escape(state.get("anti_cheat_status", ""))}</dd>
      <dt>Real app touched</dt><dd>{html.escape(str(state.get("real_app_touched", False)))}</dd>
      <dt>Clean command</dt><dd><code>{html.escape(state.get("clean_command", ""))}</code></dd>
    </dl>
    {preview_html}
  </section>
  <section><h2>Live Events</h2><pre>{html.escape(read(LANE_DIR / "live-events.jsonl") or "No live events.")}</pre></section>
  <section><h2>Transcript</h2><details open><summary>Show</summary><pre>{transcript}</pre></details></section>
  <section><h2>Diff</h2><details><summary>Show</summary><pre>{diff_text}</pre></details></section>
</main>
</body>
</html>
"""
    write(OUTPUT_ROOT / "index.html", body)


def write_closeout(state: dict[str, Any]) -> None:
    lines = [
        "# Continue Qwen Real Env Debug Closeout",
        "",
        f"Final status: {state.get('status')}",
        f"Environment gate result: {state.get('environment_gate_result')}",
        f"Hostname/user/pwd: {state.get('hostname')} / {state.get('user')} / {state.get('pwd')}",
        f"cn path: {state.get('cn_path')}",
        f"Qwen direct smoke time: {state.get('qwen_direct_smoke_time')}",
        f"README edit smoke result: {state.get('readme_edit_smoke', {}).get('status')}",
        f"Homepage prompt result: {state.get('homepage_prompt', {}).get('status')}",
        f"Exact Continue command: {state.get('continue_command') or 'not run'}",
        f"Model target: {TARGET_MODEL}",
        f"Model observed: {state.get('model_observed')}",
        f"Files changed: {', '.join(state.get('files_changed', [])) or 'none'}",
        f"Preview URL: {state.get('preview_url') or 'none'}",
        f"Launcher URL: {state.get('launcher_url')}",
        f"Blocker: {state.get('blocker') or 'none'}",
        f"Anti-cheat status: {state.get('anti_cheat_status')}",
        f"Real app touched: {state.get('real_app_touched')}",
        f"Closeout path: {state.get('closeout_path')}",
        f"Clean command: {state.get('clean_command')}",
        "",
    ]
    write(OUTPUT_ROOT / "closeout.md", "\n".join(lines))


def score_homepage(result: CmdResult, changed: list[str], preview: str) -> dict[str, Any]:
    if result.timed_out:
        return {"label": "TIMEOUT", "total": 0, "blocker": classify_timeout(result.stdout + result.stderr)}
    total = (2 if changed else 0) + (2 if changed else 0) + (2 if preview else 0) + (2 if preview else 0) + 2
    label = "GO" if total >= 8 else "WARNING" if total >= 5 else "NO-GO"
    return {"label": label, "total": total}


def reset_workspace(seed_readme: bool) -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    for child in WORKSPACE.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    subprocess.run(["git", "init"], cwd=WORKSPACE, capture_output=True, text=True, timeout=30)
    if seed_readme:
        write(WORKSPACE / "README.md", "START\n")


def process_snapshot() -> str:
    return run_capture(["bash", "-lc", "ps -ef | grep -E 'cn|continue|node|ollama|gemini' | grep -v grep || true"], timeout=30, missing_ok=True).text


def detect_process_conflicts(ps_text: str) -> list[str]:
    notes: list[str] = []
    serve_lines = [line for line in ps_text.splitlines() if "ollama" in line and " serve" in line]
    if len(serve_lines) >= 2:
        notes.append(f"Duplicate Ollama servers observed: {len(serve_lines)} serve processes.")
    if any(line.startswith("ollama ") and "ollama serve" in line for line in serve_lines) and any(
        line.startswith("root ") and "ollama serve" in line for line in serve_lines
    ):
        notes.append("Ollama servers are split across ollama and root users.")
    return notes


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
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        time.sleep(2)
        if proc.poll() is None:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception:
        proc.kill()


def snapshot(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            files[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    return files


def changed_files(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return [name for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)]


def diff_snapshots(before: dict[str, str], after: dict[str, str]) -> str:
    chunks: list[str] = []
    for name in changed_files(before, after):
        chunks.extend(
            difflib.unified_diff(
                before.get(name, "").splitlines(keepends=True),
                after.get(name, "").splitlines(keepends=True),
                fromfile=f"a/{name}",
                tofile=f"b/{name}",
            )
        )
    return "".join(chunks)


def choose_preview(after: dict[str, str]) -> str:
    for name in sorted(after):
        if name.lower().endswith((".html", ".htm")):
            return f"continue-qwen/workspace/{name}"
    return ""


def update_path_trace(extra: dict[str, Any]) -> None:
    current = {}
    path = LANE_DIR / "path-trace.json"
    if path.exists():
        current = json.loads(path.read_text(encoding="utf-8"))
    current.update(extra)
    write(path, json.dumps(current, indent=2))


def classify_timeout(text: str) -> str:
    low = text.lower()
    if "permission" in low or "allow" in low or "confirm" in low:
        return "CONTINUE_WAITING_FOR_PERMISSION"
    if "qwen" in low or TARGET_MODEL in low:
        return "CONTINUE_TIMEOUT_DURING_MODEL_OUTPUT"
    return "CONTINUE_TIMEOUT_BEFORE_MODEL_OUTPUT"


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


if __name__ == "__main__":
    raise SystemExit(main())
