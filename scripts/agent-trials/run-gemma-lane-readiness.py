from __future__ import annotations

import argparse
import difflib
import http.server
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUTPUT_ROOT = (
    REPO_ROOT
    / "docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/gemma-lane-readiness"
)

CONTINUE_DIR = OUTPUT_ROOT / "continue-gemma"
SOURCE_PROXY_DIR = OUTPUT_ROOT / "source-proxy-gemma"
DIRECT_SMOKE_PROMPT = "say GEMMA_READY in one line"
CONTINUE_SMOKE_PROMPT = (
    "Run only in this disposable workspace. Edit README.md by adding one new line: "
    "Gemma Continue file edit proof. Do not touch anything else."
)
SOURCE_PROXY_SMOKE_PROMPT = (
    "Run only in this disposable workspace. Create a tiny index.html that says "
    "Gemma Source Proxy file edit proof."
)
MINI_PROMPT = (
    "init a repo for agent lab experiements make me a homepage i can open on my phone "
    "dont touch the real spiritos app tho"
)

TIMEOUTS = {
    "pull": 20 * 60,
    "ollama_smoke": 3 * 60,
    "continue": 5 * 60,
    "source_proxy": 5 * 60,
    "mini": 8 * 60,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Gemma local lane readiness")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8773)
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
        return run()
    parser.print_help()
    return 1


def run() -> int:
    load_env()
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    CONTINUE_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_PROXY_DIR.mkdir(parents=True, exist_ok=True)
    (CONTINUE_DIR / "workspace").mkdir(parents=True, exist_ok=True)
    (SOURCE_PROXY_DIR / "workspace").mkdir(parents=True, exist_ok=True)

    started = utc_now()
    inventory = collect_inventory()
    (OUTPUT_ROOT / "model-inventory.txt").write_text(inventory["text"], encoding="utf-8")

    selected, install = select_and_install(inventory)
    inventory["selected_model"] = selected
    inventory["selection_reason"] = install["selection_reason"]
    (OUTPUT_ROOT / "install-log.txt").write_text(install["log"], encoding="utf-8")
    (OUTPUT_ROOT / "model-inventory.txt").write_text(render_inventory(inventory), encoding="utf-8")

    direct = run_direct_smoke(selected) if selected else blocked_result("NO_MODEL", "No Gemma model installed.")
    (OUTPUT_ROOT / "ollama-smoke.txt").write_text(direct["transcript"], encoding="utf-8")

    continue_result = run_continue_smoke(selected) if direct["status"] == "OK" else write_continue_blocked(
        "SKIPPED",
        "Direct Ollama Gemma smoke did not pass.",
        selected,
    )
    source_result = run_source_proxy_smoke(selected) if direct["status"] == "OK" else write_source_proxy_blocked(
        "SKIPPED",
        "Direct Ollama Gemma smoke did not pass.",
        selected,
    )

    mini_result = run_optional_mini(selected, continue_result, source_result)
    manifest = {
        "task": "gemma-lane-readiness",
        "created_at": started,
        "completed_at": utc_now(),
        "selected_gemma_model": selected,
        "selection_reason": inventory.get("selection_reason", ""),
        "timeouts_seconds": TIMEOUTS,
        "inventory": {
            "gpu_name": inventory.get("gpu_name", ""),
            "vram_total": inventory.get("vram_total", ""),
            "vram_free": inventory.get("vram_free", ""),
            "installed_ollama_models": inventory.get("models", []),
        },
        "install": {key: value for key, value in install.items() if key != "log"},
        "install_log_path": str((OUTPUT_ROOT / "install-log.txt").relative_to(REPO_ROOT)),
        "direct_ollama_smoke": compact_result(direct),
        "continue_gemma": compact_result(continue_result),
        "source_proxy_gemma": compact_result(source_result),
        "one_prompt_mini_smoke": compact_result(mini_result),
        "any_file_edit_happened": bool(
            continue_result.get("file_edit_happened")
            or source_result.get("file_edit_happened")
            or mini_result.get("file_edit_happened")
        ),
        "full_gauntlet_run": False,
        "plan_4_started": False,
        "real_spiritos_app_touched": False,
    }
    (OUTPUT_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    anti = write_anti_cheat()
    write_closeout(manifest, anti)
    return 0


def collect_inventory() -> dict[str, Any]:
    sections: list[tuple[str, RunResult]] = []
    for label, cmd in (
        ("ollama list", ["ollama", "list"]),
        ("nvidia-smi", ["nvidia-smi"]),
        ("free -h", ["free", "-h"]),
        ("df -h /mnt/spirit-8tb", ["df", "-h", "/mnt/spirit-8tb"]),
    ):
        sections.append((label, run_cmd(cmd, timeout=30, allow_missing=True)))
    text = "\n\n".join(f"## {label}\n{result.text}" for label, result in sections)
    ollama_text = sections[0][1].stdout + sections[0][1].stderr
    nvidia_text = sections[1][1].stdout + sections[1][1].stderr
    models = parse_ollama_models(ollama_text)
    gpu_name, vram_total, vram_free = parse_nvidia(nvidia_text)
    return {
        "text": text,
        "models": models,
        "gpu_name": gpu_name,
        "vram_total": vram_total,
        "vram_free": vram_free,
    }


def render_inventory(inventory: dict[str, Any]) -> str:
    lines = [
        "# Gemma Lane Model Inventory",
        "",
        f"GPU name: {inventory.get('gpu_name') or 'unknown'}",
        f"VRAM total: {inventory.get('vram_total') or 'unknown'}",
        f"VRAM free: {inventory.get('vram_free') or 'unknown'}",
        f"Selected Gemma model: {inventory.get('selected_model') or 'none'}",
        f"Selection reason: {inventory.get('selection_reason') or 'not selected'}",
        "",
        "Installed Ollama models:",
    ]
    for model in inventory.get("models", []):
        lines.append(f"- {model}")
    lines.extend(["", inventory.get("text", "")])
    return "\n".join(lines).rstrip() + "\n"


def select_and_install(inventory: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if not shutil.which("ollama"):
        return "", {
            "status": "MANUAL_REQUIRED",
            "selection_reason": "Ollama CLI is not available.",
            "log": "Ollama CLI is not available.\n",
            "attempts": [],
        }

    models = inventory.get("models", [])
    installed_gemma4 = choose_installed_gemma4_e4b(models)
    candidates: list[tuple[str, str]] = []
    if installed_gemma4:
        candidates.append((installed_gemma4, "Installed Gemma 4 E4B-looking model was already present."))
    else:
        candidates.extend(
            [
                ("gemma3n:e4b", "Preferred practical Gemma E4B lane for 12 GB VRAM."),
                ("gemma3n:latest", "Gemma3n E4B tag was unavailable; try normal latest tag."),
                ("gemma3:4b", "Small Gemma 4B final allowed option for 12 GB VRAM."),
            ]
        )

    logs: list[str] = []
    attempts: list[dict[str, Any]] = []
    for model, reason in candidates:
        if ollama_has(model):
            log = f"{model} already installed; no pull run.\n"
            logs.append(log)
            attempts.append({"model": model, "status": "ALREADY_INSTALLED", "reason": reason})
            return model, {
                "status": "ALREADY_INSTALLED",
                "selected_model": model,
                "selection_reason": reason,
                "log": "\n".join(logs),
                "attempts": attempts,
            }
        result = run_cmd(["ollama", "pull", model], timeout=TIMEOUTS["pull"])
        logs.append(f"$ ollama pull {model}\n{result.text}\n")
        status = "OK" if result.returncode == 0 and not result.timed_out else "TIMEOUT" if result.timed_out else "FAILED"
        attempts.append({"model": model, "status": status, "reason": reason, "elapsed_seconds": result.elapsed})
        if status == "OK" and ollama_has(model):
            return model, {
                "status": "PULLED",
                "selected_model": model,
                "selection_reason": reason,
                "log": "\n".join(logs),
                "attempts": attempts,
            }
        if status == "TIMEOUT":
            return model, {
                "status": "TIMEOUT",
                "selected_model": model,
                "selection_reason": reason,
                "log": "\n".join(logs),
                "attempts": attempts,
            }

    return "", {
        "status": "FAILED",
        "selection_reason": "All allowed Gemma candidates failed to install.",
        "log": "\n".join(logs),
        "attempts": attempts,
    }


def choose_installed_gemma4_e4b(models: list[str]) -> str:
    for model in models:
        low = model.lower()
        if "gemma4" in low and ("e4b" in low or ":4b" in low or "-4b" in low):
            return model
    return ""


def run_direct_smoke(model: str) -> dict[str, Any]:
    result = run_cmd(["ollama", "run", model, DIRECT_SMOKE_PROMPT], timeout=TIMEOUTS["ollama_smoke"])
    text = result.stdout + result.stderr
    ok = result.returncode == 0 and not result.timed_out and "gemma_ready" in text.lower().replace(" ", "_")
    status = "OK" if ok else "TIMEOUT" if result.timed_out else "FAILED"
    return {
        "status": status,
        "model": model,
        "elapsed_seconds": result.elapsed,
        "transcript": f"$ ollama run {model} <prompt>\nPrompt: {DIRECT_SMOKE_PROMPT}\n\n{result.text}",
    }


def run_continue_smoke(model: str) -> dict[str, Any]:
    lane_dir = CONTINUE_DIR
    workspace = lane_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "README.md").write_text("Gemma Continue seed.\n", encoding="utf-8")
    cn = shutil.which("cn")
    help_text = ""
    if not cn:
        return write_continue_blocked("MANUAL_REQUIRED", "Continue CLI `cn` is not on PATH.", model)
    help_result = run_cmd([cn, "--help"], timeout=60)
    help_text = help_result.stdout + help_result.stderr
    if "--config" not in help_text or "--auto" not in help_text or "-p" not in help_text:
        return write_continue_blocked(
            "MANUAL_REQUIRED",
            "Continue help did not document the required safe `--config --auto -p` syntax.",
            model,
            help_text,
        )

    config = write_continue_config(lane_dir, model)
    before = snapshot(workspace)
    started = time.time()
    cmd = [cn, "--config", str(config), "--auto", "-p", CONTINUE_SMOKE_PROMPT]
    result = run_cmd(cmd, timeout=TIMEOUTS["continue"], cwd=workspace)
    elapsed = round(time.time() - started, 3)
    after = snapshot(workspace)
    changed = changed_files(before, after)
    transcript = format_command_transcript(cmd, workspace, result)
    (lane_dir / "transcript.txt").write_text(transcript, encoding="utf-8")
    (lane_dir / "command-log.txt").write_text(
        "\n".join(
            [
                f"cwd: {workspace}",
                f"command: {display_cmd(cmd)}",
                f"elapsed_seconds: {elapsed}",
                f"changed_files: {changed}",
                f"config: {config}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    readme = (workspace / "README.md").read_text(encoding="utf-8", errors="replace")
    selected = model in config.read_text(encoding="utf-8", errors="replace")
    edited = "Gemma Continue file edit proof" in readme and "README.md" in changed
    status = "OK" if result.returncode == 0 and selected and edited else "TIMEOUT" if result.timed_out else "MANUAL_REQUIRED"
    reason = "" if status == "OK" else "Continue did not prove selected Gemma file editing."
    score = {
        "lane": "continue-gemma",
        "model": model,
        "status": status,
        "total": 1 if status == "OK" else 0,
        "selected_model_proven": selected,
        "file_edit_happened": edited,
        "changed_files": changed,
        "reason": reason,
    }
    (lane_dir / "score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    (lane_dir / "status.txt").write_text(status + ("\n" if not reason else f"\n{reason}\n"), encoding="utf-8")
    return {**score, "elapsed_seconds": elapsed, "transcript": transcript}


def write_continue_config(lane_dir: Path, model: str) -> Path:
    body = f"""schema: v1.5.44
name: gemma-lane-readiness
version: 1.0.0
models:
  - name: gemma-local
    model: {model}
    provider: ollama
    apiBase: http://localhost:11434
    roles:
      - chat
      - edit
allowAnonymousTelemetry: false
"""
    path = lane_dir / "lane-config.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def run_source_proxy_smoke(model: str) -> dict[str, Any]:
    lane_dir = SOURCE_PROXY_DIR
    workspace = lane_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    diagnostics = resolve_source_proxy_route(model)
    if not diagnostics.get("enabled") or not equivalent_model(str(diagnostics.get("ollama_model", "")), model):
        return write_source_proxy_blocked(
            "MANUAL_REQUIRED",
            "Source Proxy route did not resolve to the selected Gemma model.",
            model,
            diagnostics,
        )

    before = snapshot(workspace)
    raw, meta = call_resolved_ollama(
        str(diagnostics["api_base"]),
        str(diagnostics["ollama_model"]),
        SOURCE_PROXY_SMOKE_PROMPT,
        TIMEOUTS["source_proxy"],
    )
    (lane_dir / "transcript.txt").write_text(raw, encoding="utf-8")
    applied = apply_model_files(raw, workspace)
    after = snapshot(workspace)
    changed = changed_files(before, after)
    index_ok = "index.html" in after and "Gemma Source Proxy file edit proof" in after["index.html"]
    status = "OK" if meta["status"] == "OK" and index_ok else meta["status"] if meta["status"] == "TIMEOUT" else "MANUAL_REQUIRED"
    diagnostics.update(
        {
            "selected_gemma_model": model,
            "provider_call": meta,
            "file_parse_route": applied["route"],
            "changed_files": changed,
            "index_html_created": index_ok,
        }
    )
    (lane_dir / "route-diagnostics.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    score = {
        "lane": "source-proxy-gemma",
        "model": model,
        "status": status,
        "total": 1 if status == "OK" else 0,
        "selected_model_proven": equivalent_model(str(diagnostics.get("ollama_model", "")), model),
        "file_edit_happened": index_ok,
        "changed_files": changed,
        "reason": "" if status == "OK" else "Source Proxy route did not produce a model-authored index.html edit.",
    }
    (lane_dir / "score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    (lane_dir / "status.txt").write_text(status + "\n", encoding="utf-8")
    return {**score, "transcript": raw, "diagnostics": diagnostics}


def resolve_source_proxy_route(model: str) -> dict[str, Any]:
    original = {key: os.environ.get(key) for key in ("SOURCE_PROXY_OLLAMA_MODEL", "OLLAMA_MODEL")}
    try:
        os.environ["SOURCE_PROXY_OLLAMA_MODEL"] = model
        os.environ["OLLAMA_MODEL"] = model
        from source_proxy.routing.ollama_route import clear_ollama_route_cache, ollama_route_status_entry

        clear_ollama_route_cache()
        status = ollama_route_status_entry()
        status["env_override_used"] = {
            "SOURCE_PROXY_OLLAMA_MODEL": model,
            "OLLAMA_MODEL": model,
        }
        return status
    except Exception as error:
        return {"enabled": False, "error": str(error), "selected_gemma_model": model}
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def call_resolved_ollama(api_base: str, model: str, prompt: str, timeout: int) -> tuple[str, dict[str, Any]]:
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 700},
            "keep_alive": "5m",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{api_base.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
        text = str(payload.get("response") or "")
        return text, {
            "status": "OK",
            "elapsed_seconds": round(time.time() - started, 3),
            "api_base": api_base,
            "model": model,
            "done": payload.get("done"),
        }
    except TimeoutError:
        return "TIMEOUT\n", {
            "status": "TIMEOUT",
            "elapsed_seconds": round(time.time() - started, 3),
            "api_base": api_base,
            "model": model,
        }
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError) as error:
        return f"ERROR: {error}\n", {
            "status": "FAILED",
            "elapsed_seconds": round(time.time() - started, 3),
            "api_base": api_base,
            "model": model,
            "error": str(error),
        }


def run_optional_mini(model: str, continue_result: dict[str, Any], source_result: dict[str, Any]) -> dict[str, Any]:
    if continue_result.get("status") == "OK":
        return run_continue_mini(model)
    if source_result.get("status") == "OK":
        return run_source_proxy_mini(model, source_result.get("diagnostics") or {})
    result = {
        "status": "SKIPPED",
        "model": model,
        "reason": "No Gemma route proved file editing, so the one-prompt mini smoke did not run.",
        "file_edit_happened": False,
    }
    (OUTPUT_ROOT / "mini-smoke-status.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def run_continue_mini(model: str) -> dict[str, Any]:
    lane_dir = CONTINUE_DIR
    workspace = lane_dir / "mini-workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    config = lane_dir / "lane-config.yaml"
    before = snapshot(workspace)
    cn = shutil.which("cn") or "cn"
    cmd = [cn, "--config", str(config), "--auto", "-p", MINI_PROMPT]
    result = run_cmd(cmd, timeout=TIMEOUTS["mini"], cwd=workspace)
    after = snapshot(workspace)
    changed = changed_files(before, after)
    diff = diff_snapshots(before, after)
    (lane_dir / "mini-transcript.txt").write_text(format_command_transcript(cmd, workspace, result), encoding="utf-8")
    (lane_dir / "mini-diff.patch").write_text(diff, encoding="utf-8")
    edited = bool(changed)
    preview = "continue-gemma/mini-workspace/index.html" if (workspace / "index.html").exists() else ""
    status = "OK" if result.returncode == 0 and edited else "TIMEOUT" if result.timed_out else "FAILED"
    score = {
        "status": status,
        "lane": "continue-gemma-mini",
        "model": model,
        "file_edit_happened": edited,
        "changed_files": changed,
        "preview_path": preview,
    }
    (lane_dir / "mini-score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    return score


def run_source_proxy_mini(model: str, diagnostics: dict[str, Any]) -> dict[str, Any]:
    lane_dir = SOURCE_PROXY_DIR
    workspace = lane_dir / "mini-workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    before = snapshot(workspace)
    raw, meta = call_resolved_ollama(
        str(diagnostics["api_base"]),
        str(diagnostics["ollama_model"]),
        MINI_PROMPT,
        TIMEOUTS["mini"],
    )
    (lane_dir / "mini-transcript.txt").write_text(raw, encoding="utf-8")
    applied = apply_model_files(raw, workspace)
    after = snapshot(workspace)
    changed = changed_files(before, after)
    (lane_dir / "mini-diff.patch").write_text(diff_snapshots(before, after), encoding="utf-8")
    edited = bool(changed)
    preview = "source-proxy-gemma/mini-workspace/index.html" if (workspace / "index.html").exists() else ""
    status = "OK" if meta["status"] == "OK" and edited else meta["status"] if meta["status"] == "TIMEOUT" else "FAILED"
    score = {
        "status": status,
        "lane": "source-proxy-gemma-mini",
        "model": model,
        "file_edit_happened": edited,
        "changed_files": changed,
        "preview_path": preview,
        "file_parse_route": applied["route"],
    }
    (lane_dir / "mini-score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    return score


def write_continue_blocked(status: str, reason: str, model: str, help_text: str = "") -> dict[str, Any]:
    CONTINUE_DIR.mkdir(parents=True, exist_ok=True)
    score = {
        "lane": "continue-gemma",
        "model": model,
        "status": status,
        "total": 0,
        "selected_model_proven": False,
        "file_edit_happened": False,
        "manual_required": status == "MANUAL_REQUIRED",
        "reason": reason,
        "needed_config": f"Use `cn --config <single-model yaml for {model}> --auto -p <prompt>`.",
    }
    (CONTINUE_DIR / "status.txt").write_text(f"{status}\n{reason}\n", encoding="utf-8")
    (CONTINUE_DIR / "command-log.txt").write_text(help_text or reason, encoding="utf-8")
    (CONTINUE_DIR / "transcript.txt").write_text(reason + "\n", encoding="utf-8")
    (CONTINUE_DIR / "score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    return score


def write_source_proxy_blocked(
    status: str,
    reason: str,
    model: str,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    SOURCE_PROXY_DIR.mkdir(parents=True, exist_ok=True)
    score = {
        "lane": "source-proxy-gemma",
        "model": model,
        "status": status,
        "total": 0,
        "selected_model_proven": False,
        "file_edit_happened": False,
        "manual_required": status == "MANUAL_REQUIRED",
        "reason": reason,
        "needed_config": f"Set SOURCE_PROXY_OLLAMA_MODEL={model} and OLLAMA_MODEL={model}; verify route status resolves to that exact model.",
    }
    (SOURCE_PROXY_DIR / "status.txt").write_text(f"{status}\n{reason}\n", encoding="utf-8")
    (SOURCE_PROXY_DIR / "route-diagnostics.json").write_text(json.dumps(diagnostics or score, indent=2), encoding="utf-8")
    (SOURCE_PROXY_DIR / "transcript.txt").write_text(reason + "\n", encoding="utf-8")
    (SOURCE_PROXY_DIR / "score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    return score


def apply_model_files(raw: str, workspace: Path) -> dict[str, Any]:
    blocks = extract_file_blocks(raw)
    applied: list[str] = []
    for rel, content in blocks:
        clean = rel.strip().strip("`").replace("\\", "/")
        if not safe_relpath(clean):
            continue
        target = (workspace / clean).resolve()
        if workspace.resolve() not in target.parents and target != workspace.resolve():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content.rstrip() + "\n", encoding="utf-8")
        applied.append(clean)
    return {"route": "model_authored_file_blocks" if applied else "none", "files_applied": applied}


def extract_file_blocks(raw: str) -> list[tuple[str, str]]:
    patterns = [
        re.compile(r"(?:^|\n)(?:File|Path|Filename):\s*`?([A-Za-z0-9_.\-/\\ ]+)`?\s*\n```[A-Za-z0-9_+-]*\n(.*?)```", re.S),
        re.compile(r"```([A-Za-z0-9_.\-/\\]+)\n(.*?)```", re.S),
        re.compile(r"```[A-Za-z0-9_+-]*\n\s*(?:<!--\s*(?:file|path):\s*([^>]+?)\s*-->|//\s*(?:file|path):\s*(.+?)\n|#\s*(?:file|path):\s*(.+?)\n)(.*?)```", re.S | re.I),
    ]
    blocks: list[tuple[str, str]] = []
    for pattern in patterns[:2]:
        for match in pattern.finditer(raw):
            rel = match.group(1).strip()
            if "/" in rel or "." in Path(rel).name:
                blocks.append((rel, match.group(2)))
    for match in patterns[2].finditer(raw):
        rel = next((group for group in match.groups()[:3] if group), "").strip()
        blocks.append((rel, match.group(4)))
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for rel, content in blocks:
        clean = rel.strip().strip("`").replace("\\", "/")
        if clean and clean not in seen:
            seen.add(clean)
            unique.append((clean, content))
    return unique


def safe_relpath(rel: str) -> bool:
    if not rel or rel.startswith("/") or ":" in rel:
        return False
    parts = [part for part in rel.split("/") if part]
    if any(part == ".." for part in parts):
        return False
    return parts[0] not in {"src", "source_proxy", "docs", ".gate", ".git", "node_modules"}


def write_anti_cheat() -> dict[str, Any]:
    watched = [
        "cor" + "rection",
        "cor" + "rective",
        "harness_" + "corrected",
        "fallback_" + "success",
        "known_" + "good",
        "template_" + "homepage",
        "write_" + "known_" + "good",
        "repair_" + "output",
        "apply_" + "prompt_",
        "calculator_" + "page",
        "base_" + "homepage",
        "default_" + "homepage",
        "if failed " + "write",
    ]
    files = [Path(__file__)]
    for root in (CONTINUE_DIR / "workspace", SOURCE_PROXY_DIR / "workspace", CONTINUE_DIR / "mini-workspace", SOURCE_PROXY_DIR / "mini-workspace"):
        if root.exists():
            files.extend(path for path in root.rglob("*") if path.is_file())
    hits: dict[str, list[str]] = {}
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            continue
        found = [term for term in watched if term in text]
        if found:
            hits[str(path.relative_to(REPO_ROOT))] = found
    report = {
        "status": "CONTAMINATED" if hits else "CLEAN",
        "checked_files": [str(path.relative_to(REPO_ROOT)) for path in files if path.exists()],
        "terms_found": hits,
        "repair_or_scaffold_logic_applied": False,
        "copied_output_between_lanes": False,
        "fake_model_label_used": False,
    }
    (OUTPUT_ROOT / "anti-cheat-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def write_closeout(manifest: dict[str, Any], anti: dict[str, Any]) -> None:
    preview = manifest.get("one_prompt_mini_smoke", {}).get("preview_path") or ""
    ready = (
        manifest.get("direct_ollama_smoke", {}).get("status") == "OK"
        and (
            manifest.get("continue_gemma", {}).get("status") == "OK"
            or manifest.get("source_proxy_gemma", {}).get("status") == "OK"
        )
        and anti.get("status") == "CLEAN"
    )
    manual_steps = []
    for key in ("continue_gemma", "source_proxy_gemma"):
        result = manifest.get(key, {})
        if result.get("manual_required"):
            manual_steps.append(f"- {key}: {result.get('needed_config') or result.get('reason')}")
    lines = [
        "# Gemma Lane Readiness Closeout",
        "",
        f"- Selected Gemma model: {manifest.get('selected_gemma_model') or 'none'}",
        f"- Why selected: {manifest.get('selection_reason') or 'not selected'}",
        f"- Install/pull status: {manifest.get('install', {}).get('status')}",
        f"- Direct Ollama smoke result: {manifest.get('direct_ollama_smoke', {}).get('status')}",
        f"- Continue Gemma selection result: {manifest.get('continue_gemma', {}).get('status')}",
        f"- Source Proxy Gemma route result: {manifest.get('source_proxy_gemma', {}).get('status')}",
        f"- Any file edit happened: {manifest.get('any_file_edit_happened')}",
        f"- One-prompt mini smoke: {manifest.get('one_prompt_mini_smoke', {}).get('status')}",
        f"- Preview URL: {'http://<host>:8773/' + preview if preview else 'not available'}",
        f"- Anti-cheat status: {anti.get('status')}",
        f"- Timeouts/failures: {summarize_timeouts(manifest)}",
        "- Manual-required steps:",
        *(manual_steps or ["- none"]),
        f"- Gemma ready for ultimate gauntlet: {ready}",
        "- Full gauntlet run: no",
        "- Plan 4 started: no",
        "- Real SpiritOS app touched: no",
        "",
    ]
    (OUTPUT_ROOT / "closeout.md").write_text("\n".join(lines), encoding="utf-8")


def summarize_timeouts(manifest: dict[str, Any]) -> str:
    statuses = []
    for key in ("install", "direct_ollama_smoke", "continue_gemma", "source_proxy_gemma", "one_prompt_mini_smoke"):
        status = manifest.get(key, {}).get("status")
        if status and status not in {"OK", "ALREADY_INSTALLED", "PULLED", "SKIPPED"}:
            statuses.append(f"{key}={status}")
    return ", ".join(statuses) if statuses else "none"


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if key not in {"transcript"}}


def blocked_result(status: str, reason: str) -> dict[str, Any]:
    return {"status": status, "reason": reason, "file_edit_happened": False, "transcript": reason + "\n"}


class RunResult:
    def __init__(
        self,
        cmd: list[str],
        returncode: int,
        stdout: str,
        stderr: str,
        elapsed: float,
        timed_out: bool = False,
    ) -> None:
        self.cmd = cmd
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.elapsed = elapsed
        self.timed_out = timed_out

    @property
    def text(self) -> str:
        status = "TIMEOUT" if self.timed_out else str(self.returncode)
        return (
            f"command: {display_cmd(self.cmd)}\n"
            f"exit_code: {status}\n"
            f"elapsed_seconds: {self.elapsed}\n\n"
            f"{self.stdout}{self.stderr}"
        ).rstrip() + "\n"


def run_cmd(
    cmd: list[str],
    *,
    timeout: int,
    cwd: Path | None = None,
    allow_missing: bool = False,
) -> RunResult:
    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return RunResult(
            cmd,
            proc.returncode,
            clean_log_text(proc.stdout),
            clean_log_text(proc.stderr),
            round(time.time() - started, 3),
        )
    except FileNotFoundError as error:
        if not allow_missing:
            raise
        return RunResult(cmd, 127, "", str(error), round(time.time() - started, 3))
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return RunResult(
            cmd,
            -1,
            clean_log_text(stdout),
            clean_log_text(stderr),
            round(time.time() - started, 3),
            timed_out=True,
        )


def clean_log_text(text: str) -> str:
    return "".join(char if char == "\n" or char == "\t" or ord(char) >= 32 else "\n" for char in text)


def format_command_transcript(cmd: list[str], workspace: Path, result: RunResult) -> str:
    return (
        f"cwd: {workspace}\n"
        f"command: {display_cmd(cmd)}\n"
        f"exit_code: {'TIMEOUT' if result.timed_out else result.returncode}\n"
        f"elapsed_seconds: {result.elapsed}\n\n"
        "=== STDOUT/STDERR ===\n"
        f"{result.stdout}{result.stderr}\n"
    )


def display_cmd(cmd: list[str]) -> str:
    return " ".join(shlex_quote(part) for part in cmd)


def shlex_quote(value: str) -> str:
    if re.fullmatch(r"[\w./:@=-]+", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def parse_ollama_models(text: str) -> list[str]:
    models: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("name "):
            continue
        name = stripped.split()[0]
        if ":" in name or name:
            models.append(name)
    return models


def parse_nvidia(text: str) -> tuple[str, str, str]:
    gpu_name = ""
    vram_total = ""
    vram_free = ""
    for line in text.splitlines():
        if "|" in line and "MiB" in line and "/" in line:
            match = re.search(r"(\d+)MiB\s*/\s*(\d+)MiB", line)
            if match:
                used = int(match.group(1))
                total = int(match.group(2))
                vram_total = f"{total} MiB"
                vram_free = f"{max(total - used, 0)} MiB"
        if re.search(r"RTX|NVIDIA|GeForce|Quadro|Tesla", line) and not gpu_name:
            cells = [cell.strip() for cell in line.split("|") if cell.strip()]
            for cell in cells:
                if re.search(r"RTX|NVIDIA|GeForce|Quadro|Tesla", cell):
                    gpu_name = re.sub(r"\s{2,}", " ", cell)
                    break
    return gpu_name, vram_total, vram_free


def ollama_has(model: str) -> bool:
    result = run_cmd(["ollama", "list"], timeout=30, allow_missing=True)
    names = parse_ollama_models(result.stdout + result.stderr)
    return any(equivalent_model(name, model) for name in names)


def equivalent_model(left: str, right: str) -> bool:
    left_low = left.lower()
    right_low = right.lower()
    return left_low == right_low or left_low.removesuffix(":latest") == right_low.removesuffix(":latest")


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
    return sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))


def diff_snapshots(before: dict[str, str], after: dict[str, str]) -> str:
    lines: list[str] = []
    for rel in changed_files(before, after):
        old = before.get(rel, "").splitlines(True)
        new = after.get(rel, "").splitlines(True)
        lines.extend(difflib.unified_diff(old, new, fromfile=f"before/{rel}", tofile=f"after/{rel}"))
    return "".join(lines)


def serve(host: str, port: int) -> int:
    if not OUTPUT_ROOT.exists():
        print(f"No output root: {OUTPUT_ROOT}")
        return 1
    lan_ip = get_lan_ip()
    tailscale_ip = get_tailscale_ip()
    print(f"Launcher: http://{lan_ip}:{port}/")
    if tailscale_ip:
        print(f"Tailscale: http://{tailscale_ip}:{port}/")
    manifest_path = OUTPUT_ROOT / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        preview = manifest.get("one_prompt_mini_smoke", {}).get("preview_path")
        if preview:
            print(f"Preview: http://{lan_ip}:{port}/{preview}")
            if tailscale_ip:
                print(f"Preview Tailscale: http://{tailscale_ip}:{port}/{preview}")
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


def get_tailscale_ip() -> str:
    tailscale = shutil.which("tailscale")
    if not tailscale:
        return ""
    result = run_cmd([tailscale, "ip", "-4"], timeout=5, allow_missing=True)
    return (result.stdout.splitlines() or [""])[0].strip()


def load_env() -> None:
    path = REPO_ROOT / ".env.local"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() and key.strip() not in os.environ:
            os.environ[key.strip()] = value.strip().strip('"').strip("'")


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


if __name__ == "__main__":
    raise SystemExit(main())
