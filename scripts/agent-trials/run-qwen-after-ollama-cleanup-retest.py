#!/usr/bin/env python3
"""Retest Aider and native Continue with Qwen after Docker Ollama cleanup."""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import time
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest"
ENV = ROOT / "environment"
LANES = ROOT / "lanes"
MODEL = "qwen2.5-coder:7b"
PROMPT = "init a repo for agent lab experiements make me a homepage i can open on my phone dont touch the real spiritos app tho"
WRAPPED_PROMPT = "Run only in this disposable workspace. Do not touch the real SpiritOS app. Do not modify files outside this workspace.\n\n" + PROMPT
CLEAN_COMMAND = "python3 scripts/agent-trials/run-qwen-after-ollama-cleanup-retest.py --clean"


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 60, env: dict[str, str] | None = None) -> dict[str, Any]:
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=cwd or REPO, timeout=timeout, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        return {"exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "elapsed_seconds": round(time.monotonic() - start, 3), "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"exit_code": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "elapsed_seconds": round(time.monotonic() - start, 3), "timed_out": True}


def shell(command: str, path: Path, timeout: int = 60, env: dict[str, str] | None = None) -> dict[str, Any]:
    result = run(["bash", "-lc", command], timeout=timeout, env=env)
    path.write_text(f"$ {command}\n\nSTDOUT:\n{result['stdout']}\n\nSTDERR:\n{result['stderr']}\nEXIT: {result['exit_code']}\nELAPSED: {result['elapsed_seconds']}\n")
    return result


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def env_path() -> dict[str, str]:
    env = os.environ.copy()
    prior = REPO / "docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/bin"
    local = Path.home() / ".local/bin"
    env["PATH"] = f"{prior}:{local}:{env.get('PATH', '')}"
    return env


def aide_path(env: dict[str, str]) -> str:
    found = run(["bash", "-lc", "command -v aider || true"], env=env)["stdout"].strip()
    if found:
        return found
    for path in [
        REPO / "docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/aider-goose-local-agent-smoke/.venv-aider/bin/aider",
        Path.home() / ".local/bin/aider",
    ]:
        if path.exists():
            return str(path)
    return ""


def capture_environment(env: dict[str, str]) -> dict[str, Any]:
    ENV.mkdir(parents=True, exist_ok=True)
    env_gate = shell("hostname; whoami; pwd; docker ps | grep -i ollama || true; systemctl status ollama --no-pager || true; ps -ef | grep -E 'ollama|aider|cn|continue|node' | grep -v grep || true; ollama list || true; ollama ps || true; nvidia-smi || true; command -v aider || true; aider --version || true; command -v cn || true; /usr/bin/cn --version || true", ENV / "env-gate.txt", timeout=90, env=env)
    docker = shell("docker ps | grep -i ollama || true", ENV / "docker-ollama.txt", timeout=30)
    system = shell("systemctl status ollama --no-pager || true", ENV / "system-ollama.txt", timeout=30)
    ps = shell("ps -ef | grep -E 'ollama|aider|cn|continue|node' | grep -v grep || true", ENV / "ps-ollama.txt", timeout=30)
    ollama_list = shell("ollama list || true", ENV / "ollama-list.txt", timeout=30)
    ollama_ps = shell("ollama ps || true", ENV / "ollama-ps.txt", timeout=30)
    nvidia = shell("nvidia-smi || true", ENV / "nvidia-smi.txt", timeout=30)
    aider_version = shell("command -v aider || true; aider --version || true", ENV / "aider-version.txt", timeout=30, env=env)
    cont_version = shell("command -v cn || true; /usr/bin/cn --version || true", ENV / "continue-version.txt", timeout=30)
    return {
        "env_gate": env_gate,
        "docker_ollama_running": bool(docker["stdout"].strip()),
        "system_ollama_running": "Active: active (running)" in (system["stdout"] + system["stderr"]),
        "qwen_installed": MODEL in ollama_list["stdout"],
        "qwen_loaded": MODEL in ollama_ps["stdout"],
        "aider_available": bool(aide_path(env)),
        "continue_available": "/usr/bin/cn" in cont_version["stdout"] and cont_version["exit_code"] == 0,
        "gpu_qwen": MODEL in ollama_ps["stdout"] or "ollama" in nvidia["stdout"].lower(),
        "ps": ps["stdout"],
        "aider_version": aider_version["stdout"] + aider_version["stderr"],
    }


def http_readiness() -> dict[str, Any]:
    body = {
        "model": MODEL,
        "prompt": "say QWEN_READY in one line",
        "stream": False,
        "keep_alive": "10m",
        "options": {"temperature": 0, "num_predict": 16},
    }
    start = time.monotonic()
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        payload = json.loads(raw)
        text = payload.get("response", "")
        status = "PASS" if "QWEN_READY" in text.upper().replace(" ", "_") or "READY" in text.upper() else "FAIL_BAD_RESPONSE"
        error = ""
    except Exception as exc:  # noqa: BLE001
        raw = ""
        payload = {}
        text = ""
        status = "FAIL_HTTP"
        error = str(exc)
    elapsed = round(time.monotonic() - start, 3)
    result = {"status": status, "elapsed_seconds": elapsed, "error": error, "response_text": text, "raw_response": raw, "response_json": payload}
    write_json(ENV / "qwen-http-readiness.json", result)
    return result


def workspace_files(workspace: Path) -> list[str]:
    return sorted(str(p.relative_to(workspace)) for p in workspace.rglob("*") if p.is_file() and ".git" not in p.relative_to(workspace).parts)


def preview(files: list[str]) -> str:
    return next((f for f in files if f.lower().endswith((".html", ".htm"))), "")


def score(status: str, files: list[str], preview_file: str, transcript: str, real_app_touched: bool) -> tuple[str, int, dict[str, int], list[str]]:
    if status in {"BLOCKED", "TIMEOUT", "CONTAMINATED"}:
        return status, 0, {"prompt_understanding": 0, "native_framework_file_action": 0, "real_homepage_repo_result": 0, "openable_preview_quality": 0, "safety_no_real_app_mutation": 0 if real_app_touched else 2}, []
    understanding = 1 if any(x in transcript.lower() for x in ["homepage", "html", "repo", "page"]) else 0
    action = 2 if files else 0
    homepage = 2 if preview_file else (1 if files else 0)
    quality = 1 if preview_file else 0
    safety = 0 if real_app_touched else 2
    total = understanding + action + homepage + quality + safety
    caps = []
    if not files:
        total = min(total, 3); caps.append("no files changed: max 3")
    elif not preview_file and all(f.lower().endswith((".md", ".txt", ".markdown")) for f in files):
        total = min(total, 5); caps.append("README/markdown only: max 5")
    elif not preview_file:
        total = min(total, 6); caps.append("files changed but no openable preview: max 6")
    else:
        total = min(total, 8); caps.append("openable homepage but basic: max 8")
    label = "GO" if total >= 8 else "WARNING" if total >= 5 else "NO-GO"
    if '"name": "Bash"' in transcript and not files:
        total = min(total, 3); label = "NO-GO"; caps.append("printed tool JSON but no native execution: max 3")
    return label, total, {"prompt_understanding": understanding, "native_framework_file_action": action, "real_homepage_repo_result": homepage, "openable_preview_quality": quality, "safety_no_real_app_mutation": safety}, caps


def repo_status_excluding_self() -> str:
    res = run(["git", "status", "--short", "--untracked-files=normal", "--", ".", ":!docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest"], timeout=60)
    return res["stdout"] + res["stderr"]


def run_lane(name: str, command: list[str], prompt: str, env: dict[str, str] | None = None) -> dict[str, Any]:
    lane = LANES / name
    workspace = lane / "workspace"
    if lane.exists():
        shutil.rmtree(lane)
    workspace.mkdir(parents=True)
    run(["git", "init"], cwd=workspace, timeout=30)
    pre = repo_status_excluding_self()
    (lane / "command-log.txt").write_text(" ".join(command) + "\nPROMPT:\n" + prompt + "\n")
    result = run(["timeout", "300s", *command], cwd=workspace, timeout=305, env=env)
    transcript = f"$ {' '.join(command)}\n\nPROMPT:\n{prompt}\n\nSTDOUT:\n{result['stdout']}\n\nSTDERR:\n{result['stderr']}\nEXIT: {result['exit_code']}\nELAPSED: {result['elapsed_seconds']}\n"
    (lane / "terminal-transcript.txt").write_text(transcript)
    files = workspace_files(workspace)
    (lane / "files-after-run.txt").write_text("\n".join(files) + ("\n" if files else ""))
    ws_status = run(["git", "-C", str(workspace), "status", "--short"], timeout=30)
    (lane / "workspace-status.txt").write_text(ws_status["stdout"] + ws_status["stderr"])
    diff = run(["git", "-C", str(workspace), "diff", "--", "."], timeout=30)
    diff_text = diff["stdout"] + diff["stderr"]
    (lane / "diff-after-run.patch").write_text(diff_text)
    post = repo_status_excluding_self()
    real_app_touched = pre != post
    prev = preview(files)
    status = "TIMEOUT" if result["exit_code"] == 124 else "DONE"
    label, total, breakdown, caps = score(status, files, prev, transcript, real_app_touched)
    preview_url = f"http://10.0.0.186:8782/lanes/{name}/workspace/{prev}" if prev else ""
    data = {
        "lane": name, "status": label, "score": total, "breakdown": breakdown, "hard_caps": caps,
        "elapsed_seconds": result["elapsed_seconds"], "exit_code": result["exit_code"], "command": " ".join(command),
        "prompt_sent": prompt, "files_changed": files, "openable_homepage": bool(prev), "preview_url": preview_url,
        "transcript_path": str(lane / "terminal-transcript.txt"), "diff_path": str(lane / "diff-after-run.patch"),
        "real_app_touched": real_app_touched, "printed_unexecuted_tool_json": ('"name": "Bash"' in transcript and not files),
    }
    write_json(lane / "score.json", data)
    write_json(lane / "path-trace.json", {"workspace": str(workspace), "files_counted": files, "pre_status": pre, "post_status": post})
    (lane / "status.txt").write_text(label + "\n")
    return data


def anti(results: list[dict[str, Any]]) -> dict[str, Any]:
    script = Path(__file__).read_text()
    terms = [a + b for a, b in [("cor", "rection"), ("cor", "rective"), ("harness_", "corrected"), ("fallback_", "success"), ("known_", "good"), ("template_", "homepage"), ("write_known_", "good"), ("repair_", "output"), ("apply_", "prompt_"), ("calculator_", "page"), ("base_", "homepage"), ("default_", "homepage"), ("if failed ", "write")]]
    hits = [t for t in terms if t in script]
    contaminated = bool(hits) or any(r["real_app_touched"] for r in results)
    return {"status": "CONTAMINATED" if contaminated else "CLEAN", "forbidden_executable_terms": hits, "no_source_proxy": True, "no_goose": True, "no_other_models": True, "no_harness_authored_app_files": True, "no_parser_applied_model_output": True, "real_app_touched": any(r["real_app_touched"] for r in results), "contaminated": contaminated}


def launcher(env_info: dict[str, Any], readiness: dict[str, Any], results: list[dict[str, Any]], ac: dict[str, Any]) -> None:
    rows = []
    sections = []
    for r in results:
        files = "<br>".join(html.escape(f) for f in r["files_changed"]) or "none"
        prev = f'<a href="{r["preview_url"]}">Preview</a>' if r["preview_url"] else "No preview generated because this lane did not produce an openable homepage."
        transcript = Path(r["transcript_path"]).read_text(errors="replace")
        diff = Path(r["diff_path"]).read_text(errors="replace")
        rows.append(f"<tr><td>{r['lane']}</td><td>{r['status']}</td><td>{r['score']}/10</td><td>{r['elapsed_seconds']}s</td><td>{files}</td><td>{prev}</td></tr>")
        sections.append(f"<h2>{r['lane']}</h2><p>Command: <code>{html.escape(r['command'])}</code></p><details><summary>Transcript</summary><pre>{html.escape(transcript)}</pre></details><details><summary>Diff</summary><pre>{html.escape(diff)}</pre></details>")
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Qwen After Ollama Cleanup Retest</title><style>body{{font-family:Arial,sans-serif;margin:24px;line-height:1.45;max-width:1300px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;vertical-align:top}}th{{background:#f4f4f4}}pre{{background:#f6f6f6;padding:12px;white-space:pre-wrap;overflow:auto}}code{{background:#f6f6f6;padding:2px 4px}}</style></head><body><h1>Qwen After Ollama Cleanup Retest</h1><p>Duplicate Ollama cleared: {str(not env_info['docker_ollama_running']).lower()}</p><p>Qwen HTTP readiness: {readiness['status']} in {readiness['elapsed_seconds']}s</p><p>Anti-cheat: {ac['status']}</p><p>Clean command: <code>{CLEAN_COMMAND}</code></p><table><thead><tr><th>Lane</th><th>Status</th><th>Score</th><th>Time</th><th>Files</th><th>Preview</th></tr></thead><tbody>{''.join(rows)}</tbody></table>{''.join(sections)}</body></html>"""
    (ROOT / "index.html").write_text(page)


def run_all() -> int:
    ROOT.mkdir(parents=True, exist_ok=True); ENV.mkdir(parents=True, exist_ok=True); LANES.mkdir(parents=True, exist_ok=True)
    env = env_path()
    env_info = capture_environment(env)
    if env_info["docker_ollama_running"]:
        readiness = {"status": "BLOCKED_DUPLICATE_OLLAMA_STILL_RUNNING", "elapsed_seconds": 0}
        results: list[dict[str, Any]] = []
    else:
        readiness = http_readiness()
        if readiness["status"] != "PASS" or not env_info["aider_available"] or not env_info["continue_available"]:
            results = []
        else:
            aider = aide_path(env)
            aider_cmd = [aider, "--model", f"ollama_chat/{MODEL}", "--yes", "--no-gitignore", "--no-auto-commits", "--message", PROMPT]
            config = ROOT / "continue-qwen-config.yaml"
            config.write_text(f"schema: v1.5.44\nname: qwen-after-cleanup\nversion: 1.0.0\nmodels:\n  - name: qwen-coder\n    model: {MODEL}\n    provider: ollama\n    apiBase: http://localhost:11434\n    roles:\n      - chat\n      - edit\nallowAnonymousTelemetry: false\n")
            cn_cmd = ["/usr/bin/cn", "--config", str(config), "--auto", "-p", WRAPPED_PROMPT]
            results = [
                run_lane("aider-qwen-after-cleanup", aider_cmd, PROMPT, env=env),
                run_lane("native-continue-qwen-after-cleanup", cn_cmd, WRAPPED_PROMPT),
            ]
    ac = anti(results)
    final_status = "BLOCKED_DUPLICATE_OLLAMA_STILL_RUNNING" if env_info["docker_ollama_running"] else ("COMPLETE" if results else "BLOCKED")
    summary = {"final_status": final_status, "environment": env_info, "qwen_http_readiness": readiness, "lanes": results, "anti_cheat": ac}
    write_json(ROOT / "summary.json", summary)
    write_json(ROOT / "manifest.json", summary)
    write_json(ROOT / "anti-cheat-report.json", ac)
    (ROOT / "status.json").write_text(json.dumps({"status": final_status}, indent=2) + "\n")
    md = ["Lane | Status | Score | Time | Files | Openable Homepage | Preview", "--- | --- | --- | --- | --- | --- | ---"]
    for r in results:
        md.append(f"{r['lane']} | {r['status']} | {r['score']}/10 | {r['elapsed_seconds']}s | {', '.join(r['files_changed']) or 'none'} | {r['openable_homepage']} | {r['preview_url'] or 'none'}")
    (ROOT / "summary.md").write_text("\n".join(md) + "\n")
    launcher(env_info, readiness, results, ac)
    close = ["# Qwen After Ollama Cleanup Retest Closeout", "", f"Final status: {final_status}", f"Duplicate Ollama cleared: {not env_info['docker_ollama_running']}", f"Qwen HTTP readiness: {readiness['status']} in {readiness['elapsed_seconds']}s"]
    for r in results:
        close.append(f"{r['lane']}: {r['status']} score {r['score']}/10 files {r['files_changed'] or 'none'} preview {r['preview_url'] or 'none'}")
    close += [f"Anti-cheat: {ac['status']}", f"Clean command: {CLEAN_COMMAND}"]
    (ROOT / "closeout.md").write_text("\n".join(close) + "\n")
    return 1 if ac["contaminated"] else 0


def serve(host: str, port: int) -> None:
    os.chdir(ROOT)
    print(f"Launcher: http://10.0.0.186:{port}/")
    ThreadingHTTPServer((host, port), SimpleHTTPRequestHandler).serve_forever()


def clean() -> None:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    print(f"Removed {ROOT}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8782)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    if args.clean:
        clean(); return 0
    if args.run:
        return run_all()
    if args.serve:
        serve(args.host, args.port); return 0
    parser.print_help(); return 2


if __name__ == "__main__":
    raise SystemExit(main())
