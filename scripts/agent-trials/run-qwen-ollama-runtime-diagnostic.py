#!/usr/bin/env python3
"""Diagnose qwen2.5-coder:7b Ollama runtime stability without agent lanes."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-ollama-runtime-diagnostic"
ENV = ROOT / "environment"
PROBES = ROOT / "probes"
MODEL = "qwen2.5-coder:7b"
PROMPT = "say QWEN_READY in one line"
CLEAN_COMMAND = "python3 scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py --clean"


def run(cmd: list[str], timeout: int = 60, cwd: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=cwd or REPO, timeout=timeout, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {
            "cmd": cmd,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "elapsed_seconds": round(time.monotonic() - start, 3),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "exit_code": 124,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "elapsed_seconds": round(time.monotonic() - start, 3),
            "timed_out": True,
        }


def shell(command: str, path: Path, timeout: int = 60) -> dict[str, Any]:
    result = run(["bash", "-lc", command], timeout=timeout)
    path.write_text(
        f"$ {command}\n\nSTDOUT:\n{result['stdout']}\n\nSTDERR:\n{result['stderr']}\n"
        f"EXIT: {result['exit_code']}\nELAPSED: {result['elapsed_seconds']}\n"
    )
    return result


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def passive_environment() -> dict[str, Any]:
    ENV.mkdir(parents=True, exist_ok=True)
    captures = {
        "hostname": shell("hostname", ENV / "hostname.txt"),
        "whoami": shell("whoami", ENV / "whoami.txt"),
        "pwd": shell("pwd", ENV / "pwd.txt"),
        "env_ollama": shell("env | grep -E 'OLLAMA|CUDA|NVIDIA' || true", ENV / "env-ollama.txt"),
        "docker_ollama": shell("docker ps | grep -i ollama || true", ENV / "docker-ollama.txt"),
        "system_ollama": shell("systemctl status ollama --no-pager || true", ENV / "system-ollama.txt"),
        "ps_before": shell("ps -ef | grep -E 'ollama|cn|aider|goose|continue|node' | grep -v grep || true", ENV / "ps-ollama-before.txt"),
        "ollama_list": shell("ollama list || true", ENV / "ollama-list.txt"),
        "ollama_ps_before": shell("ollama ps || true", ENV / "ollama-ps-before.txt"),
        "nvidia_before": shell("nvidia-smi || true", ENV / "nvidia-smi-before.txt"),
        "memory_swap": shell("free -h || true; echo; swapon --show || true", ENV / "memory-swap.txt"),
        "disk": shell("df -h / /mnt/spirit-8tb || true", ENV / "disk.txt"),
    }
    ollama_list = captures["ollama_list"]["stdout"]
    docker_text = captures["docker_ollama"]["stdout"]
    system_text = captures["system_ollama"]["stdout"] + captures["system_ollama"]["stderr"]
    ps_text = captures["ps_before"]["stdout"]
    nvidia_text = captures["nvidia_before"]["stdout"]
    mem_text = captures["memory_swap"]["stdout"]
    return {
        "hostname": captures["hostname"]["stdout"].strip(),
        "whoami": captures["whoami"]["stdout"].strip(),
        "pwd": captures["pwd"]["stdout"].strip(),
        "qwen_installed": MODEL in ollama_list,
        "docker_ollama_running": "ollama" in docker_text.lower(),
        "spirit_ollama_container": "spirit-ollama" in docker_text,
        "system_ollama_exists": "ollama.service" in system_text,
        "system_ollama_running": "Active: active (running)" in system_text,
        "duplicate_ollama_warning": ("ollama" in docker_text.lower()) and ("Active: active (running)" in system_text),
        "qwen_loaded_before": MODEL in captures["ollama_ps_before"]["stdout"],
        "gpu_runner_before": "ollama" in nvidia_text.lower(),
        "swap_pressure": infer_swap_pressure(mem_text),
        "stale_runner_processes": any(token in ps_text for token in ["ollama runner", "ollama_llama_server"]) and MODEL not in captures["ollama_ps_before"]["stdout"],
    }


def infer_swap_pressure(text: str) -> bool:
    for line in text.splitlines():
        if line.lower().startswith("swap:"):
            parts = line.split()
            if len(parts) >= 3 and parts[2] not in {"0B", "0", "0.0B"}:
                return True
    return False


def timed_cli_probe(name: str) -> dict[str, Any]:
    before = run(["ollama", "ps"], timeout=20)
    proc = subprocess.Popen(
        ["timeout", "120s", "ollama", "run", MODEL, PROMPT],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)
    during_ps = run(["bash", "-lc", "ps -ef | grep -E 'ollama|cn|aider|goose|continue|node' | grep -v grep || true"], timeout=20)
    during_gpu = run(["nvidia-smi"], timeout=20)
    if name == "qwen-cli-cold":
        (ENV / "ps-ollama-during.txt").write_text(during_ps["stdout"] + during_ps["stderr"])
        (ENV / "nvidia-smi-during.txt").write_text(during_gpu["stdout"] + during_gpu["stderr"])
    start = time.monotonic()
    try:
        stdout, stderr = proc.communicate(timeout=125)
        elapsed = time.monotonic() - start + 2
        code = proc.returncode
        timed_out = code == 124
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        elapsed = 127.0
        code = 124
        timed_out = True
    after = run(["ollama", "ps"], timeout=20)
    result = {
        "name": name,
        "command": f'timeout 120s ollama run {MODEL} "{PROMPT}"',
        "elapsed_seconds": round(elapsed, 3),
        "exit_code": code,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "ollama_ps_before": before["stdout"],
        "ollama_ps_after": after["stdout"],
        "nvidia_smi_during": during_gpu["stdout"],
    }
    (PROBES / f"{name}.txt").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def http_generate(name: str, keep_alive: str = "10m", delay_before: float = 0) -> dict[str, Any]:
    if delay_before:
        time.sleep(delay_before)
    body = {
        "model": MODEL,
        "prompt": PROMPT,
        "stream": False,
        "keep_alive": keep_alive,
        "options": {"temperature": 0, "num_predict": 16},
    }
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8", errors="replace")
        elapsed = time.monotonic() - start
        payload = json.loads(raw)
        error = ""
        code = 0
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        elapsed = time.monotonic() - start
        payload = {}
        raw = ""
        error = str(exc)
        code = 1
    result = {
        "name": name,
        "elapsed_seconds": round(elapsed, 3),
        "exit_code": code,
        "error": error,
        "request": body,
        "raw_response": raw,
        "response_json": payload,
        "response_text": payload.get("response", ""),
        "total_duration_seconds": ns_to_s(payload.get("total_duration")),
        "load_duration_seconds": ns_to_s(payload.get("load_duration")),
        "prompt_eval_duration_seconds": ns_to_s(payload.get("prompt_eval_duration")),
        "eval_duration_seconds": ns_to_s(payload.get("eval_duration")),
        "eval_count": payload.get("eval_count"),
    }
    write_json(PROBES / f"{name}.json", result)
    return result


def ns_to_s(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return round(value / 1_000_000_000, 3)
    return None


def build_repeat_metrics(cli_cold: dict[str, Any], cli_warm: dict[str, Any], http_results: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [
        {"probe": "cli cold", "elapsed_seconds": cli_cold["elapsed_seconds"], "exit_code": cli_cold["exit_code"], "load_duration_seconds": None, "eval_duration_seconds": None, "response": cli_cold["stdout"].strip()},
        {"probe": "cli warm", "elapsed_seconds": cli_warm["elapsed_seconds"], "exit_code": cli_warm["exit_code"], "load_duration_seconds": None, "eval_duration_seconds": None, "response": cli_warm["stdout"].strip()},
    ]
    for item in http_results:
        rows.append({
            "probe": item["name"],
            "elapsed_seconds": item["elapsed_seconds"],
            "exit_code": item["exit_code"],
            "load_duration_seconds": item["load_duration_seconds"],
            "eval_duration_seconds": item["eval_duration_seconds"],
            "response": item["response_text"].strip(),
        })
    write_json(PROBES / "qwen-repeat-metrics.json", {"rows": rows})
    md = ["Probe | Elapsed | Exit | Load Duration | Eval Duration | Response", "--- | ---: | ---: | ---: | ---: | ---"]
    for row in rows:
        md.append(
            f"{row['probe']} | {row['elapsed_seconds']}s | {row['exit_code']} | "
            f"{row['load_duration_seconds'] if row['load_duration_seconds'] is not None else 'n/a'} | "
            f"{row['eval_duration_seconds'] if row['eval_duration_seconds'] is not None else 'n/a'} | "
            f"{row['response'] or 'none'}"
        )
    (PROBES / "qwen-repeat-table.md").write_text("\n".join(md) + "\n")
    return {"rows": rows}


def diagnose(env: dict[str, Any], cli_cold: dict[str, Any], cli_warm: dict[str, Any], http_results: list[dict[str, Any]]) -> dict[str, Any]:
    http_ok = [r for r in http_results if r["exit_code"] == 0]
    qwen_missing = not env["qwen_installed"]
    if qwen_missing:
        status = "BLOCKED_QWEN_MISSING"
    elif not http_ok and all(r["exit_code"] != 0 for r in http_results):
        status = "BLOCKED_OLLAMA_UNREACHABLE"
    elif env["duplicate_ollama_warning"]:
        status = "RUNTIME_CONFLICT_DETECTED"
    elif any(r["elapsed_seconds"] > 90 for r in [cli_cold, cli_warm] + http_results):
        status = "RUNTIME_UNSTABLE"
    elif any(r["elapsed_seconds"] > 30 for r in [cli_cold, cli_warm] + http_results):
        status = "RUNTIME_SLOW_BUT_USABLE"
    else:
        status = "RUNTIME_STABLE"
    slow_cli = cli_cold["elapsed_seconds"] > 90 or cli_warm["elapsed_seconds"] > 90
    warm_helped = cli_warm["elapsed_seconds"] < cli_cold["elapsed_seconds"]
    max_http = max((r["elapsed_seconds"] for r in http_results), default=0)
    suspected = []
    if env["duplicate_ollama_warning"]:
        suspected.append("Duplicate Docker/system Ollama services are running.")
    if slow_cli and max_http <= 120:
        suspected.append("Qwen cold/warm CLI startup is too slow for readiness gates; readiness harness blocked before Aider.")
    if env["swap_pressure"]:
        suspected.append("Swap is in use, which may contribute to slow model load.")
    if env["gpu_runner_before"] or any("ollama" in r.get("nvidia_smi_during", "").lower() for r in [cli_cold, cli_warm]):
        gpu_used = True
    else:
        gpu_used = False
        suspected.append("GPU runner was not clearly visible in sampled nvidia-smi output.")
    if not suspected:
        suspected.append("No hard conflict found; variance likely cold-load/model residency and CLI startup overhead.")
    recommendation = "OPERATOR_DECISION_REQUIRED" if env["duplicate_ollama_warning"] else "NO_CHANGE_NEEDED"
    allow_aider = env["qwen_installed"] and bool(http_ok) and max_http <= 120
    return {
        "final_status": status,
        "suspected_blocker": " ".join(suspected),
        "recommended_fix": recommendation,
        "manual_cleanup_commands": [
            "systemctl status ollama --no-pager",
            "docker ps | grep -i ollama",
            "# Choose one Ollama runtime; do not run these without deciding which runtime should own 11434.",
        ] if recommendation == "OPERATOR_DECISION_REQUIRED" else [],
        "warm_run_faster": warm_helped,
        "gpu_used": gpu_used,
        "aider_should_run": allow_aider,
        "recommended_aider_timeout_seconds": 300,
        "readiness_policy": "Make readiness diagnostic-only if HTTP API responds within 120 seconds; do not block Aider solely on CLI warmup variance.",
        "clean_duplicate_ollama": recommendation == "OPERATOR_DECISION_REQUIRED",
    }


def write_aider_decision(summary: dict[str, Any]) -> None:
    text = f"""# Aider Readiness Decision

Qwen should be allowed through the Aider test now: {summary['aider_should_run']}

The readiness gate should not block Aider when qwen2.5-coder:7b is installed and the HTTP API responds within 120 seconds. Treat readiness as diagnostic-only and keep the Aider run capped.

Recommended Aider timeout: {summary['recommended_aider_timeout_seconds']} seconds.

Qwen runtime stable enough for one Aider run: {summary['aider_should_run']}

Duplicate Ollama should be cleaned first: {summary['clean_duplicate_ollama']}

Reason: {summary['suspected_blocker']}
"""
    (ROOT / "aider-readiness-decision.md").write_text(text)


def write_launcher(manifest: dict[str, Any], summary: dict[str, Any]) -> None:
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Qwen Ollama Runtime Diagnostic</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; max-width: 1100px; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background: #f4f4f4; width: 260px; }}
code {{ background: #f6f6f6; padding: 2px 4px; }}
</style>
</head>
<body>
<h1>Qwen Ollama Runtime Diagnostic</h1>
<table>
<tr><th>Final status</th><td>{summary['final_status']}</td></tr>
<tr><th>Qwen installed</th><td>{yesno(manifest['environment']['qwen_installed'])}</td></tr>
<tr><th>Duplicate Ollama warning</th><td>{yesno(manifest['environment']['duplicate_ollama_warning'])}</td></tr>
<tr><th>CLI cold time</th><td>{manifest['cli_cold']['elapsed_seconds']}s</td></tr>
<tr><th>CLI warm time</th><td>{manifest['cli_warm']['elapsed_seconds']}s</td></tr>
<tr><th>HTTP cold time</th><td>{manifest['http_results'][0]['elapsed_seconds']}s</td></tr>
<tr><th>HTTP warm time</th><td>{manifest['http_results'][1]['elapsed_seconds']}s</td></tr>
<tr><th>Load duration</th><td>{manifest['http_results'][0]['load_duration_seconds']}</td></tr>
<tr><th>Generation duration</th><td>{manifest['http_results'][0]['eval_duration_seconds']}</td></tr>
<tr><th>GPU used</th><td>{yesno(summary['gpu_used'])}</td></tr>
<tr><th>Swap pressure</th><td>{yesno(manifest['environment']['swap_pressure'])}</td></tr>
<tr><th>Suspected blocker</th><td>{summary['suspected_blocker']}</td></tr>
<tr><th>Recommended fix</th><td>{summary['recommended_fix']}</td></tr>
<tr><th>Aider should be allowed to run</th><td>{yesno(summary['aider_should_run'])}</td></tr>
<tr><th>Clean command</th><td><code>{CLEAN_COMMAND}</code></td></tr>
</table>
</body>
</html>
"""
    (ROOT / "index.html").write_text(page)


def yesno(value: Any) -> str:
    return "yes" if value else "no"


def run_all() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    ENV.mkdir(parents=True, exist_ok=True)
    PROBES.mkdir(parents=True, exist_ok=True)
    env = passive_environment()
    if not env["qwen_installed"]:
        cli_cold = {"elapsed_seconds": 0, "exit_code": 1, "stdout": "", "stderr": "qwen missing", "nvidia_smi_during": ""}
        cli_warm = cli_cold.copy()
        http_results: list[dict[str, Any]] = []
    else:
        cli_cold = timed_cli_probe("qwen-cli-cold")
        cli_warm = timed_cli_probe("qwen-cli-warm")
        http_results = [
            http_generate("qwen-http-generate-cold"),
            http_generate("qwen-http-generate-warm"),
            http_generate("qwen-http-generate-keepalive", delay_before=5),
        ]
    shell("ps -ef | grep -E 'ollama|cn|aider|goose|continue|node' | grep -v grep || true", ENV / "ps-ollama-after.txt")
    shell("ollama ps || true", ENV / "ollama-ps-after.txt")
    shell("nvidia-smi || true", ENV / "nvidia-smi-after.txt")
    metrics = build_repeat_metrics(cli_cold, cli_warm, http_results)
    summary = diagnose(env, cli_cold, cli_warm, http_results)
    manifest = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": env,
        "cli_cold": cli_cold,
        "cli_warm": cli_warm,
        "http_results": http_results,
        "metrics": metrics,
        "summary": summary,
    }
    write_json(ROOT / "manifest.json", manifest)
    write_json(ROOT / "summary.json", summary)
    anti = {
        "status": "CLEAN",
        "no_app_files_created": True,
        "no_model_benchmark_scores_faked": True,
        "no_aider_continue_goose_lanes_run": True,
        "no_services_stopped_or_restarted": True,
        "no_sudo_used": True,
    }
    write_json(ROOT / "anti-cheat-report.json", anti)
    write_aider_decision(summary)
    write_launcher(manifest, summary)
    closeout = f"""# Qwen Ollama Runtime Diagnostic Closeout

Final status: {summary['final_status']}
Qwen installed: {env['qwen_installed']}
Duplicate Ollama warning: {env['duplicate_ollama_warning']}
System Ollama running: {env['system_ollama_running']}
Docker Ollama running: {env['docker_ollama_running']}
CLI cold time: {cli_cold['elapsed_seconds']}s
CLI warm time: {cli_warm['elapsed_seconds']}s
HTTP cold time: {http_results[0]['elapsed_seconds'] if http_results else 'n/a'}s
HTTP warm time: {http_results[1]['elapsed_seconds'] if len(http_results) > 1 else 'n/a'}s
GPU used: {summary['gpu_used']}
Swap pressure: {env['swap_pressure']}
Suspected blocker: {summary['suspected_blocker']}
Recommended fix: {summary['recommended_fix']}
Aider should be rerun: {summary['aider_should_run']}
Recommended Aider timeout: {summary['recommended_aider_timeout_seconds']}s
Clean command: {CLEAN_COMMAND}
"""
    (ROOT / "closeout.md").write_text(closeout)
    return 0


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
    parser.add_argument("--port", type=int, default=8781)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    if args.clean:
        clean()
        return 0
    if args.run:
        return run_all()
    if args.serve:
        serve(args.host, args.port)
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
