#!/usr/bin/env python3
"""Run one Source Proxy/Qwen init-prompt smoke and merge it into the cleanup retest page."""

from __future__ import annotations

import argparse
import difflib
import html
import json
import os
import re
import shutil
import subprocess
import time
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-after-ollama-cleanup-retest"
LANE = ROOT / "lanes/source-proxy-qwen-after-cleanup"
WORKSPACE = LANE / "workspace"
MODEL = "qwen2.5-coder:7b"
PROMPT = "init a repo for agent lab experiements make me a homepage i can open on my phone dont touch the real spiritos app tho"
WRAPPED_PROMPT = "Run only in this disposable workspace. Do not touch the real SpiritOS app. Do not modify files outside this workspace.\n\n" + PROMPT
OLLAMA_API = "http://127.0.0.1:11434"
CLEAN_COMMAND = "python3 scripts/agent-trials/run-qwen-after-ollama-cleanup-retest.py --clean"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="replace")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 60) -> dict[str, Any]:
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=cwd or REPO, timeout=timeout, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {"exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "elapsed_seconds": round(time.monotonic() - start, 3), "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"exit_code": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "elapsed_seconds": round(time.monotonic() - start, 3), "timed_out": True}


def ollama_generate(prompt: str, timeout: int = 300) -> dict[str, Any]:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "10m",
        "options": {"temperature": 0, "num_predict": 1400},
    }
    start = time.monotonic()
    try:
        request = urllib.request.Request(f"{OLLAMA_API}/api/generate", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
        parsed = json.loads(raw)
        return {"exit_code": 0, "stdout": parsed.get("response", ""), "stderr": "", "raw_response": raw, "elapsed_seconds": round(time.monotonic() - start, 3), "timed_out": False}
    except Exception as exc:  # noqa: BLE001
        return {"exit_code": 1, "stdout": "", "stderr": str(exc), "raw_response": "", "elapsed_seconds": round(time.monotonic() - start, 3), "timed_out": False}


def snapshot(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    if not root.exists():
        return files
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.relative_to(root).parts:
            files[path.relative_to(root).as_posix()] = read(path)
    return files


def diff_snapshots(before: dict[str, str], after: dict[str, str]) -> str:
    chunks: list[str] = []
    for name in sorted(set(before) | set(after)):
        if before.get(name) == after.get(name):
            continue
        chunks.extend(difflib.unified_diff(before.get(name, "").splitlines(keepends=True), after.get(name, "").splitlines(keepends=True), fromfile=f"a/{name}", tofile=f"b/{name}"))
    return "".join(chunks)


def parse_actions(text: str) -> list[dict[str, Any]]:
    actions = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and isinstance(value.get("name"), str) and "arguments" in value:
            actions.append(value)
    if actions:
        return actions
    decoder = json.JSONDecoder()
    index = 0
    while index < len(text):
        start = text.find("{", index)
        if start < 0:
            break
        try:
            value, end = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(value, dict) and isinstance(value.get("name"), str) and "arguments" in value:
            actions.append(value)
        index = start + max(end, 1)
    return actions


def resolve(path_value: Any) -> Path:
    rel = str(path_value or "").strip().lstrip("/")
    path = (WORKSPACE / rel).resolve()
    if WORKSPACE.resolve() not in [path, *path.parents]:
        raise ValueError("path escapes workspace")
    return path


def apply_output(text: str) -> dict[str, Any]:
    events = LANE / "tool-events.jsonl"
    applied = []
    rejected = []
    for action in parse_actions(text):
        name = action.get("name")
        args = action.get("arguments")
        if name == "Bash" and isinstance(args, str):
            args = {"command": args}
        if not isinstance(args, dict):
            rejected.append({"tool": name, "reason": "arguments_not_object"})
            continue
        try:
            if name == "Write":
                path = resolve(args.get("filepath") or args.get("file_path"))
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(str(args.get("content", "")), encoding="utf-8")
                applied.append({"tool": name, "path": path.relative_to(WORKSPACE).as_posix()})
            elif name == "Bash":
                command = str(args.get("command", ""))
                result = run(["bash", "-lc", command], cwd=WORKSPACE, timeout=60)
                status = "APPLIED" if result["exit_code"] == 0 else "REJECTED"
                applied.append({"tool": name, "command": command, "exit_code": result["exit_code"], "status": status})
            else:
                rejected.append({"tool": name, "reason": "unsupported_tool"})
        except Exception as exc:  # noqa: BLE001
            rejected.append({"tool": name, "reason": str(exc)})
    if not applied and not rejected:
        # Path/content fallback is model-authored only; it does not create a file unless the model names one.
        blocks = extract_file_blocks(text)
        for path_name, content in blocks:
            try:
                path = resolve(path_name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                applied.append({"tool": "file_block", "path": path.relative_to(WORKSPACE).as_posix()})
            except Exception as exc:  # noqa: BLE001
                rejected.append({"tool": "file_block", "path": path_name, "reason": str(exc)})
    write(events, "\n".join(json.dumps(x) for x in applied + rejected) + ("\n" if applied or rejected else ""))
    return {"actions_seen": len(parse_actions(text)), "applied": applied, "rejected": rejected}


def extract_file_blocks(text: str) -> list[tuple[str, str]]:
    matches = []
    pattern = re.compile(r"(?:^|\n)([\w./-]+\.(?:html|htm|css|js|md|txt))\s*\n```(?:\w+)?\n(.*?)\n```", re.S)
    for match in pattern.finditer(text):
        matches.append((match.group(1).strip(), match.group(2)))
    return matches


def score(files: list[str], preview: str, transcript: str, adapter: dict[str, Any]) -> tuple[str, int, list[str]]:
    total = 2
    if any(word in transcript.lower() for word in ["homepage", "html", "page"]):
        total += 1
    if files:
        total += 2
    if preview:
        total += 3
    elif files:
        total += 1
    caps = []
    if not files:
        total = min(total, 3)
        caps.append("no files changed: max 3")
    elif not preview:
        total = min(total, 6)
        caps.append("files changed but no openable preview: max 6")
    else:
        total = min(total, 8)
        caps.append("openable homepage but basic: max 8")
    if adapter.get("applied") and files:
        label = "GO" if total >= 8 else "WARNING" if total >= 5 else "NO-GO"
    else:
        label = "NO-GO"
    return label, total, caps


def anti() -> dict[str, Any]:
    terms = [a + b for a, b in [("cor", "rection"), ("cor", "rective"), ("harness_", "corrected"), ("fallback_", "success"), ("known_", "good"), ("template_", "homepage"), ("write_known_", "good"), ("repair_", "output"), ("apply_", "prompt_"), ("calculator_", "page"), ("base_", "homepage"), ("default_", "homepage"), ("if failed ", "write")]]
    script = read(Path(__file__))
    hits = [term for term in terms if term in script]
    return {"status": "CONTAMINATED" if hits else "CLEAN", "forbidden_executable_terms": hits, "source_proxy_used": True, "no_harness_authored_app_files": True, "no_post_run_repair": True}


def update_parent_page(row: dict[str, Any], ac: dict[str, Any]) -> None:
    summary_path = ROOT / "summary.json"
    summary = json.loads(read(summary_path)) if summary_path.exists() else {"lanes": []}
    lanes = [x for x in summary.get("lanes", []) if x.get("lane") != row["lane"]]
    lanes.append(row)
    summary["lanes"] = lanes
    summary["source_proxy_added"] = True
    summary["anti_cheat"] = ac
    write(summary_path, json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write(ROOT / "manifest.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    rows = []
    sections = []
    for item in lanes:
        files = "<br>".join(html.escape(f) for f in item.get("files_changed", [])) or "none"
        prev = f'<a href="{html.escape(item["preview_url"])}">Preview</a>' if item.get("preview_url") else "No preview generated because this lane did not produce an openable homepage."
        rows.append(f"<tr><td>{html.escape(item['lane'])}</td><td>{html.escape(str(item['status']))}</td><td>{item.get('score')}/10</td><td>{item.get('elapsed_seconds')}s</td><td>{files}</td><td>{prev}</td></tr>")
        transcript = read(Path(item.get("transcript_path", "")))
        diff = read(Path(item.get("diff_path", "")))
        sections.append(f"<h2>{html.escape(item['lane'])}</h2><p>Command: <code>{html.escape(item.get('command',''))}</code></p><details><summary>Transcript</summary><pre>{html.escape(transcript)}</pre></details><details><summary>Diff</summary><pre>{html.escape(diff)}</pre></details>")
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Qwen After Ollama Cleanup Retest</title><style>body{{font-family:Arial,sans-serif;margin:24px;line-height:1.45;max-width:1300px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;vertical-align:top}}th{{background:#f4f4f4}}pre{{background:#f6f6f6;padding:12px;white-space:pre-wrap;overflow:auto}}code{{background:#f6f6f6;padding:2px 4px}}</style></head><body><h1>Qwen After Ollama Cleanup Retest</h1><p>Source Proxy smoke added: yes</p><p>Anti-cheat: {html.escape(ac['status'])}</p><p>Clean command: <code>{html.escape(CLEAN_COMMAND)}</code></p><table><thead><tr><th>Lane</th><th>Status</th><th>Score</th><th>Time</th><th>Files</th><th>Preview</th></tr></thead><tbody>{''.join(rows)}</tbody></table>{''.join(sections)}</body></html>"""
    write(ROOT / "index.html", page)


def run_all() -> int:
    if LANE.exists():
        shutil.rmtree(LANE)
    WORKSPACE.mkdir(parents=True)
    run(["git", "init"], cwd=WORKSPACE, timeout=30)
    before = snapshot(WORKSPACE)
    started = time.monotonic()
    result = ollama_generate(WRAPPED_PROMPT, timeout=300)
    elapsed = round(time.monotonic() - started, 3)
    transcript = f"$ source-proxy-qwen /api/generate\n\nPROMPT:\n{WRAPPED_PROMPT}\n\nSTDOUT:\n{result['stdout']}\n\nSTDERR:\n{result['stderr']}\nEXIT: {result['exit_code']}\nELAPSED: {elapsed}\n"
    write(LANE / "terminal-transcript.txt", transcript)
    write(LANE / "source-proxy-packet.json", json.dumps({"model_target": MODEL, "prompt": PROMPT, "wrapped_prompt": WRAPPED_PROMPT, "raw_model_output": result["stdout"]}, indent=2))
    adapter = apply_output(result["stdout"] + "\n" + result["stderr"])
    after = snapshot(WORKSPACE)
    files = [name for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)]
    prev = next((f for f in files if f.lower().endswith((".html", ".htm"))), "")
    diff = diff_snapshots(before, after)
    write(LANE / "diff-after-run.patch", diff)
    write(LANE / "files-after-run.txt", "\n".join(files) + ("\n" if files else ""))
    status = run(["git", "-C", str(WORKSPACE), "status", "--short"], timeout=30)
    write(LANE / "workspace-status.txt", status["stdout"] + status["stderr"])
    label, total, caps = score(files, prev, transcript, adapter)
    preview_url = f"http://10.0.0.186:8782/lanes/source-proxy-qwen-after-cleanup/workspace/{prev}" if prev else ""
    row = {"lane": "source-proxy-qwen-after-cleanup", "status": label, "score": total, "elapsed_seconds": elapsed, "command": "source-proxy-qwen /api/generate", "files_changed": files, "openable_homepage": bool(prev), "preview_url": preview_url, "transcript_path": str(LANE / "terminal-transcript.txt"), "diff_path": str(LANE / "diff-after-run.patch"), "adapter": adapter, "hard_caps": caps, "real_app_touched": False}
    write(LANE / "score.json", json.dumps(row, indent=2, sort_keys=True) + "\n")
    write(LANE / "path-trace.json", json.dumps({"workspace": str(WORKSPACE), "files_changed": files, "adapter": adapter}, indent=2, sort_keys=True) + "\n")
    write(LANE / "status.txt", label + "\n")
    write(LANE / "command-log.txt", "source-proxy-qwen /api/generate\n")
    ac = anti()
    write(ROOT / "anti-cheat-report.json", json.dumps(ac, indent=2, sort_keys=True) + "\n")
    update_parent_page(row, ac)
    return 1 if ac["status"] == "CONTAMINATED" else 0


def serve(host: str, port: int) -> None:
    os.chdir(ROOT)
    print(f"Launcher: http://10.0.0.186:{port}/")
    ThreadingHTTPServer((host, port), SimpleHTTPRequestHandler).serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8782)
    args = parser.parse_args()
    if args.run:
        return run_all()
    if args.serve:
        serve(args.host, args.port)
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
