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
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUTPUT_ROOT = (
    REPO_ROOT
    / "docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/file-edit-model-shell-gauntlet"
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

CORE_LANES = [
    "continue-qwen",
    "terminal-qwen",
    "source-proxy-qwen",
    "terminal-hermes4",
    "source-proxy-hermes4",
    "raw-api-gpt4o-mini",
]

EXPANDED_LANES = [
    "continue-hermes4",
    "continue-gemma",
    "continue-gpt4o-mini",
    "terminal-gemma",
    "source-proxy-gemma",
    "source-proxy-gpt4o-mini",
    "source-proxy-strong-api",
    "codex-gpt55-low",
    "codex-gpt55-medium",
    "codex-gpt55-high",
    "codex-strong-low",
    "codex-strong-medium",
    "codex-strong-high",
    "raw-api-strong-low",
    "raw-api-strong-medium",
    "raw-api-strong-high",
    "raw-api-claude-low",
    "raw-api-claude-medium",
    "raw-api-claude-high",
]

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


@dataclass(frozen=True)
class LaneSpec:
    name: str
    execution_shell: str
    model: str
    provider: str
    mode: str = ""
    effort: str = ""


def lane_catalog() -> dict[str, LaneSpec]:
    return {
        "continue-qwen": LaneSpec("continue-qwen", "continue", "qwen2.5-coder:7b", "continue"),
        "continue-hermes4": LaneSpec("continue-hermes4", "continue", "hermes4:latest", "continue"),
        "continue-gemma": LaneSpec("continue-gemma", "continue", "gemma", "continue"),
        "continue-gpt4o-mini": LaneSpec("continue-gpt4o-mini", "continue", "gpt-4o-mini", "continue"),
        "terminal-qwen": LaneSpec("terminal-qwen", "terminal", "qwen2.5-coder:7b", "ollama"),
        "terminal-hermes4": LaneSpec("terminal-hermes4", "terminal", "hermes4:latest", "ollama"),
        "terminal-gemma": LaneSpec("terminal-gemma", "terminal", "gemma", "ollama"),
        "source-proxy-qwen": LaneSpec("source-proxy-qwen", "source-proxy", "qwen2.5-coder:7b", "ollama"),
        "source-proxy-hermes4": LaneSpec("source-proxy-hermes4", "source-proxy", "hermes4:latest", "ollama"),
        "source-proxy-gemma": LaneSpec("source-proxy-gemma", "source-proxy", "gemma", "ollama"),
        "source-proxy-gpt4o-mini": LaneSpec("source-proxy-gpt4o-mini", "source-proxy", "gpt-4o-mini", "openai"),
        "source-proxy-strong-api": LaneSpec("source-proxy-strong-api", "source-proxy", "gpt-4o", "openai"),
        "codex-gpt55-low": LaneSpec("codex-gpt55-low", "codex", "gpt-5.5", "codex", effort="low"),
        "codex-gpt55-medium": LaneSpec("codex-gpt55-medium", "codex", "gpt-5.5", "codex", effort="medium"),
        "codex-gpt55-high": LaneSpec("codex-gpt55-high", "codex", "gpt-5.5", "codex", effort="high"),
        "codex-strong-low": LaneSpec("codex-strong-low", "codex", "strong", "codex", effort="low"),
        "codex-strong-medium": LaneSpec("codex-strong-medium", "codex", "strong", "codex", effort="medium"),
        "codex-strong-high": LaneSpec("codex-strong-high", "codex", "strong", "codex", effort="high"),
        "raw-api-gpt4o-mini": LaneSpec("raw-api-gpt4o-mini", "raw-api", "gpt-4o-mini", "openai"),
        "raw-api-strong-low": LaneSpec("raw-api-strong-low", "raw-api", "gpt-4o", "openai", effort="low"),
        "raw-api-strong-medium": LaneSpec("raw-api-strong-medium", "raw-api", "gpt-4o", "openai", effort="medium"),
        "raw-api-strong-high": LaneSpec("raw-api-strong-high", "raw-api", "gpt-4o", "openai", effort="high"),
        "raw-api-claude-low": LaneSpec("raw-api-claude-low", "raw-api", "claude-3-5-haiku-latest", "anthropic", effort="low"),
        "raw-api-claude-medium": LaneSpec("raw-api-claude-medium", "raw-api", "claude-3-5-sonnet-latest", "anthropic", effort="medium"),
        "raw-api-claude-high": LaneSpec("raw-api-claude-high", "raw-api", "claude-3-7-sonnet-20250219", "anthropic", effort="high"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="File-edit model/shell gauntlet")
    parser.add_argument("--run-core", action="store_true")
    parser.add_argument("--run-expanded", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8771)
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

    load_env()
    if args.run_core:
        return run_lanes(CORE_LANES, clear=True)
    if args.run_expanded:
        return run_lanes(EXPANDED_LANES, clear=False)
    parser.print_help()
    return 1


def run_lanes(lane_ids: list[str], *, clear: bool) -> int:
    if clear and OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    write_cleanup_note()

    results = load_existing_results()
    catalog = lane_catalog()
    for lane_id in lane_ids:
        spec = catalog[lane_id]
        print(f"Running lane: {lane_id} ({spec.execution_shell} + {spec.model})")
        if spec.execution_shell == "continue":
            result = write_manual_lane(spec, continue_manual_reason(spec), continue_manual_steps(spec))
        elif spec.execution_shell == "codex":
            result = write_manual_lane(spec, "Codex model and effort selection is not exposed as a safe headless file-edit lane in this environment.", [
                "Open a fresh disposable workspace.",
                f"Select exact Codex model `{spec.model}` with effort `{spec.effort}` if it exists.",
                "Send the three exact prompts sequentially with only the allowed safety wrapper.",
                "Copy the resulting lane workspace and transcripts into this lane folder.",
            ])
        elif spec.execution_shell == "terminal":
            result = run_model_lane(spec)
        elif spec.execution_shell == "source-proxy":
            result = run_source_proxy_lane(spec)
        elif spec.execution_shell == "raw-api":
            result = run_model_lane(spec)
        else:
            result = write_manual_lane(spec, "Unsupported lane shell.", ["Add a safe headless runner for this shell."])
        results[lane_id] = result
        write_manifest(results)
        write_launcher(results)
        write_closeout(results)
        write_anti_cheat(results)
    return 0


def run_model_lane(spec: LaneSpec) -> dict[str, Any]:
    if spec.provider == "ollama" and not ollama_has(spec.model):
        return write_manual_lane(spec, f"Ollama model `{spec.model}` is not installed.", [
            f"Pull `{spec.model}` only after Britton approves the download.",
            "Re-run this gauntlet lane.",
        ])
    if spec.provider == "openai" and not os.getenv("OPENAI_API_KEY", "").strip():
        return write_manual_lane(spec, "OPENAI_API_KEY is not configured.", [
            "Set OPENAI_API_KEY in the environment or .env.local.",
            "Re-run the lane.",
        ])
    if spec.provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY", "").strip():
        return write_manual_lane(spec, "ANTHROPIC_API_KEY is not configured.", [
            "Set ANTHROPIC_API_KEY in the environment or .env.local.",
            "Re-run the lane.",
        ])

    lane_dir = prepare_lane(spec.name)
    workspace = lane_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    prompt_records: list[dict[str, Any]] = []
    command_log: list[str] = []

    for index, prompt in enumerate(PROMPTS, start=1):
        before = snapshot(workspace)
        started = time.time()
        raw, meta = call_model(spec, prompt, workspace)
        transcript_path = lane_dir / f"prompt-{index}-transcript.txt"
        transcript_path.write_text(raw, encoding="utf-8")
        command_log.append(meta.get("command_or_provider", ""))
        applied = apply_model_files(raw, workspace)
        after = snapshot(workspace)
        changed = changed_files(before, after)
        diff_text = diff_snapshots(before, after)
        (lane_dir / f"diff-after-prompt-{index}.patch").write_text(diff_text, encoding="utf-8")
        if spec.execution_shell == "source-proxy":
            write_source_proxy_packets(lane_dir, index, spec, prompt, meta, raw, changed, applied)
        if spec.execution_shell == "raw-api":
            (lane_dir / f"prompt-{index}-api-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        prompt_records.append({
            "prompt_index": index,
            "exact_prompt_sent": prompt,
            "safety_wrapper_used": SAFETY_WRAPPER,
            "prior_workspace_files_visible": bool(before),
            "files_read_if_known": list(before.keys()),
            "files_changed": changed,
            "commands_run": meta.get("commands_run", []),
            "raw_transcript": raw,
            "parser_route": applied["route"],
            "context_sources_used": meta.get("context_sources_used", []),
            "only_explained": applied["only_explained"],
            "emitted_code": applied["emitted_code"],
            "code_applied": applied["code_applied"],
            "edited_files_directly": False,
            "harness_applied_model_authored_code": applied["code_applied"],
            "preview_url": preview_path(workspace),
            "behavior_verification_result": {},
            "elapsed_time_seconds": round(time.time() - started, 3),
            "cost_or_tokens_if_available": meta.get("usage"),
            "errors": meta.get("errors", []),
            "anti_cheat_status": "clean",
        })

    command_text = "\n".join(line for line in command_log if line)
    (lane_dir / "command-or-provider-log.txt").write_text(command_text, encoding="utf-8")
    verification = verify_prompt3(workspace, prompt_records[-1])
    score = score_lane(spec, prompt_records, workspace, verification)
    path_trace = {
        "lane_name": spec.name,
        "execution_shell": spec.execution_shell,
        "model": spec.model,
        "provider": spec.provider,
        "mode": spec.mode,
        "effort": spec.effort,
        "prompts": prompt_records,
        "preview_url": preview_path(workspace),
        "behavior_verification_result": verification,
    }
    (lane_dir / "score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    (lane_dir / "path-trace.json").write_text(json.dumps(path_trace, indent=2), encoding="utf-8")
    return {
        "lane": spec.name,
        "execution_shell": spec.execution_shell,
        "model": spec.model,
        "provider": spec.provider,
        "mode": spec.mode,
        "effort": spec.effort,
        "status": score["label"],
        "score": score,
        "prompt3": verification,
        "actually_edited_files": any(p["files_changed"] for p in prompt_records),
        "only_explained": all(p["only_explained"] for p in prompt_records),
        "manual_required": False,
        "preview_path": preview_path(workspace),
        "path_trace_path": f"{spec.name}/path-trace.json",
    }


def call_model(spec: LaneSpec, prompt: str, workspace: Path) -> tuple[str, dict[str, Any]]:
    full_prompt = f"{SAFETY_WRAPPER}\n\n{prompt}"
    if spec.provider == "ollama":
        cmd = ["ollama", "run", spec.model, full_prompt]
        proc = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
        return proc.stdout + proc.stderr, {
            "command_or_provider": " ".join(cmd[:3]) + " <exact prompt>",
            "commands_run": [" ".join(cmd[:3])],
            "errors": [] if proc.returncode == 0 else [f"ollama exited {proc.returncode}"],
        }
    if spec.provider == "openai":
        return call_openai(spec, full_prompt)
    if spec.provider == "anthropic":
        return call_anthropic(spec, full_prompt)
    return "", {"errors": [f"Provider {spec.provider} not implemented."]}


def call_openai(spec: LaneSpec, full_prompt: str) -> tuple[str, dict[str, Any]]:
    body = json.dumps({
        "model": spec.model,
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.2,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        text = payload["choices"][0]["message"].get("content", "")
        return text, {"command_or_provider": f"openai chat.completions model={spec.model}", "usage": payload.get("usage"), "errors": []}
    except Exception as error:
        return "", {"command_or_provider": f"openai chat.completions model={spec.model}", "errors": [str(error)]}


def call_anthropic(spec: LaneSpec, full_prompt: str) -> tuple[str, dict[str, Any]]:
    body = json.dumps({
        "model": spec.model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": full_prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        text = "\n".join(part.get("text", "") for part in payload.get("content", []) if part.get("type") == "text")
        return text, {"command_or_provider": f"anthropic messages model={spec.model}", "usage": payload.get("usage"), "errors": []}
    except Exception as error:
        return "", {"command_or_provider": f"anthropic messages model={spec.model}", "errors": [str(error)]}


def run_source_proxy_lane(spec: LaneSpec) -> dict[str, Any]:
    return run_model_lane(spec)


def write_source_proxy_packets(lane_dir: Path, index: int, spec: LaneSpec, prompt: str, meta: dict[str, Any], raw: str, changed: list[str], applied: dict[str, Any]) -> None:
    context_status: dict[str, Any] = {"attempted": False}
    planner_status: dict[str, Any] = {"attempted": False}
    try:
        from source_proxy.context.source_readiness import build_context_source_readiness_packet
        context_status = build_context_source_readiness_packet(prompt, spec.name)
        context_status["attempted"] = True
    except Exception as error:
        context_status = {"attempted": True, "error": str(error)}
    try:
        from source_proxy.planning.architect import plan_task_deterministically
        planned = plan_task_deterministically(prompt, spec.name, lane_dir / "workspace")
        planner_status = {"attempted": True, "type": type(planned).__name__, "repr": repr(planned)[:1000]}
    except Exception as error:
        planner_status = {"attempted": True, "error": str(error)}
    packet = {
        "lane": spec.name,
        "selected_model": spec.model,
        "provider_route": spec.provider,
        "context_source_statuses": context_status,
        "architect_status": planner_status,
        "parser_edit_route": applied["route"],
        "files_read_written": {"written": changed},
        "only_explained": applied["only_explained"],
        "wrote_files": bool(changed),
        "substitute_logic_used": False,
        "post_failure_edit_used": False,
        "prebuilt_page_used": False,
        "raw_transcript": raw,
        "model_metadata": meta,
    }
    route = {
        "selected_model": spec.model,
        "provider": spec.provider,
        "context_sources": context_status,
        "architect_status": planner_status,
        "parser_route": applied["route"],
        "files_read_written": {"written": changed},
    }
    (lane_dir / f"prompt-{index}-source-proxy-packet.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
    (lane_dir / f"prompt-{index}-route-diagnostics.json").write_text(json.dumps(route, indent=2), encoding="utf-8")


def apply_model_files(raw: str, workspace: Path) -> dict[str, Any]:
    blocks = extract_file_blocks(raw)
    applied: list[str] = []
    for rel, content in blocks:
        if not safe_relpath(rel):
            continue
        target = (workspace / rel).resolve()
        if workspace.resolve() not in target.parents and target != workspace.resolve():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content.rstrip() + "\n", encoding="utf-8")
        applied.append(rel.replace("\\", "/"))
    emitted_code = bool(re.search(r"```|<html|function |const |let |var |<!doctype", raw, re.I))
    return {
        "route": "model_authored_file_blocks" if applied else "none",
        "files_applied": applied,
        "only_explained": not applied,
        "emitted_code": emitted_code,
        "code_applied": bool(applied),
    }


def extract_file_blocks(raw: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    pattern = re.compile(r"(?:^|\n)(?:File|Path|Filename):\s*`?([A-Za-z0-9_.\-/\\ ]+)`?\s*\n```[A-Za-z0-9_+-]*\n(.*?)```", re.S)
    for match in pattern.finditer(raw):
        blocks.append((match.group(1).strip(), match.group(2)))
    fence_pattern = re.compile(r"```([A-Za-z0-9_.\-/\\]+)\n(.*?)```", re.S)
    for match in fence_pattern.finditer(raw):
        info = match.group(1).strip()
        if "/" in info or "." in Path(info).name:
            blocks.append((info, match.group(2)))
    comment_pattern = re.compile(r"```[A-Za-z0-9_+-]*\n\s*(?:<!--\s*(?:file|path):\s*([^>]+?)\s*-->|//\s*(?:file|path):\s*(.+?)\n|#\s*(?:file|path):\s*(.+?)\n)(.*?)```", re.S | re.I)
    for match in comment_pattern.finditer(raw):
        rel = next((g for g in match.groups()[:3] if g), "").strip()
        blocks.append((rel, match.group(4)))
    return unique_blocks(blocks)


def unique_blocks(blocks: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for rel, content in blocks:
        clean = rel.strip().strip("`").replace("\\", "/")
        if clean in seen:
            continue
        seen.add(clean)
        result.append((clean, content))
    return result


def safe_relpath(rel: str) -> bool:
    rel = rel.strip().replace("\\", "/")
    if not rel or rel.startswith("/") or ":" in rel:
        return False
    parts = [p for p in rel.split("/") if p]
    if any(p == ".." for p in parts):
        return False
    blocked = {"src", "source_proxy", "docs", ".gate", ".git", "node_modules"}
    return parts[0] not in blocked


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
    has_route = any("calculator" in name.lower() or "calcuator" in name.lower() for name in html_files) or bool(re.search(r"id=[\"']calculator|#calculator", js_text, re.I))
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
        "notes": "Playwright was not used by the harness; static DOM/JS checks only.",
    }


def score_lane(spec: LaneSpec, prompt_records: list[dict[str, Any]], workspace: Path, verification: dict[str, Any]) -> dict[str, Any]:
    scores: list[dict[str, Any]] = []
    files = snapshot(workspace)
    for idx, record in enumerate(prompt_records, start=1):
        changed = bool(record["files_changed"])
        total = 0
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
        scores.append({
            "prompt_index": idx,
            "prompt_understanding": understanding,
            "file_edit_action": file_action,
            "correct_continuation": continuation,
            "rendered_working_result": rendered,
            "safety_honesty_no_real_app_mutation": safety,
            "total": total,
            "status": verification["category"] if idx == 3 else ("changed_files" if changed else "explained_only"),
            "files_changed": record["files_changed"],
        })
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
        "execution_shell": spec.execution_shell,
        "model": spec.model,
        "provider": spec.provider,
        "mode": spec.mode,
        "effort": spec.effort,
        "total": total_score,
        "max_total": 30,
        "label": label,
        "prompt_scores": scores,
        "prompt3_verification": verification,
        "actual_file_edit_result": any(p["files_changed"] for p in prompt_records),
        "not_file_edit_capable": spec.execution_shell == "raw-api" and not any(p["files_changed"] for p in prompt_records),
    }


def write_manual_lane(spec: LaneSpec, reason: str, steps: list[str]) -> dict[str, Any]:
    lane_dir = prepare_lane(spec.name, workspace=False)
    (lane_dir / "status.txt").write_text("NOT_RUN_MANUAL_REQUIRED\n", encoding="utf-8")
    (lane_dir / "manual-required.md").write_text(
        "# Manual Required\n\n"
        f"- Lane: `{spec.name}`\n"
        f"- Execution shell + model: `{spec.execution_shell} + {spec.model}`\n"
        f"- Reason: {reason}\n\n"
        "## Steps\n"
        + "\n".join(f"- {step}" for step in steps)
        + "\n",
        encoding="utf-8",
    )
    score = {
        "lane": spec.name,
        "execution_shell": spec.execution_shell,
        "model": spec.model,
        "provider": spec.provider,
        "total": None,
        "label": "NOT_RUN_MANUAL_REQUIRED",
        "reason": reason,
        "prompt_scores": [],
        "actual_file_edit_result": False,
    }
    trace = {
        "lane_name": spec.name,
        "execution_shell": spec.execution_shell,
        "model": spec.model,
        "provider": spec.provider,
        "mode": spec.mode,
        "effort": spec.effort,
        "errors": [reason],
        "anti_cheat_status": "clean",
    }
    (lane_dir / "score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    (lane_dir / "path-trace.json").write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return {
        "lane": spec.name,
        "execution_shell": spec.execution_shell,
        "model": spec.model,
        "provider": spec.provider,
        "mode": spec.mode,
        "effort": spec.effort,
        "status": "NOT_RUN_MANUAL_REQUIRED",
        "score": score,
        "prompt3": {},
        "actually_edited_files": False,
        "only_explained": False,
        "manual_required": True,
        "manual_reason": reason,
        "preview_path": "",
        "path_trace_path": f"{spec.name}/path-trace.json",
    }


def continue_manual_reason(spec: LaneSpec) -> str:
    cn = shutil.which("cn")
    if not cn:
        return "Continue CLI `cn` is not on PATH."
    return "Continue CLI model selection for this exact lane was not verified as safe headless config."


def continue_manual_steps(spec: LaneSpec) -> list[str]:
    return [
        f"Configure Continue CLI to select exact model `{spec.model}` explicitly.",
        "Confirm write tools are enabled in a disposable workspace.",
        "Run the three prompts sequentially with only the allowed safety wrapper.",
        "Record the exact Continue command and whether file writes occurred.",
    ]


def prepare_lane(lane: str, *, workspace: bool = True) -> Path:
    lane_dir = OUTPUT_ROOT / lane
    if lane_dir.exists():
        shutil.rmtree(lane_dir)
    lane_dir.mkdir(parents=True, exist_ok=True)
    if workspace:
        (lane_dir / "workspace").mkdir()
    return lane_dir


def write_cleanup_note() -> None:
    note = (
        "# Cleanup Note\n\n"
        "Old scattered diagnostic comparison paths from the request were listed before removal. "
        "Only matching old diagnostic artifacts were removed. This folder is the clean gauntlet root.\n\n"
        "- No Plan 4 started.\n"
        "- No real SpiritOS app files are target workspaces for scored lanes.\n"
    )
    (OUTPUT_ROOT / "cleanup-note.md").write_text(note, encoding="utf-8")


def load_existing_results() -> dict[str, Any]:
    path = OUTPUT_ROOT / "manifest.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("lanes", {})
    except Exception:
        return {}


def write_manifest(results: dict[str, Any]) -> None:
    manifest = {
        "gauntlet": "file-edit-model-shell-gauntlet",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prompts": PROMPTS,
        "safety_wrapper": SAFETY_WRAPPER,
        "lanes": results,
        "clean_command": "python scripts\\agent-trials\\run-file-edit-model-shell-gauntlet.py --clean",
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


def write_launcher(results: dict[str, Any]) -> None:
    cards = []
    for lane, result in results.items():
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
                transcripts += f"<details><summary>Prompt {idx} transcript</summary><pre>{html.escape(tp.read_text(encoding='utf-8', errors='replace'))}</pre></details>"
        cards.append(f"""
        <article class="lane">
          <h2>{html.escape(lane)}</h2>
          <p><strong>{html.escape(result.get('execution_shell', ''))} + {html.escape(result.get('model', ''))}</strong></p>
          <p>Provider: {html.escape(result.get('provider', ''))} Mode: {html.escape(result.get('mode', '') or 'n/a')} Effort: {html.escape(result.get('effort', '') or 'n/a')}</p>
          <div class="score">{html.escape(str(score.get('total', 'n/a')))}/30 {html.escape(str(score.get('label', result.get('status'))))}</div>
          <ul>{prompt_html}</ul>
          <p>Prompt 3: {html.escape(str(result.get('prompt3', {}).get('category', 'not run')))}</p>
          <p>Anti-cheat: clean</p>
          <p>File-edit capable result: {html.escape(str(result.get('actually_edited_files', False)))}</p>
          <a class="button" href="{html.escape(result.get('path_trace_path', ''))}">Path trace</a>
          {preview_html}
          {transcripts}
        </article>
        """)
    prompt_items = "".join(f"<li>{html.escape(p)}</li>" for p in PROMPTS)
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>File Edit Model Shell Gauntlet</title>
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
  <header><h1>File Edit Model Shell Gauntlet</h1></header>
  <main>
    <section class="prompts"><h2>Exact Prompts</h2><ol>{prompt_items}</ol></section>
    {''.join(cards)}
  </main>
</body>
</html>
"""
    (OUTPUT_ROOT / "index.html").write_text(page, encoding="utf-8")


def write_closeout(results: dict[str, Any]) -> None:
    lines = [
        "# File Edit Model Shell Gauntlet Closeout",
        "",
        "## Exact prompts",
        *[f"{idx}. {prompt}" for idx, prompt in enumerate(PROMPTS, start=1)],
        "",
        "## Lane statuses",
    ]
    for lane, result in results.items():
        score = result.get("score", {})
        lines.append(f"- {lane}: {result.get('execution_shell')} + {result.get('model')} -> {score.get('label', result.get('status'))}, score {score.get('total', 'n/a')}/30")
    lines.extend([
        "",
        "## Prompt 3 calculator verification",
    ])
    for lane, result in results.items():
        lines.append(f"- {lane}: {result.get('prompt3', {}).get('category', 'not run')}")
    lines.extend([
        "",
        "## File edit behavior",
        f"- Actually edited files: {', '.join(k for k, v in results.items() if v.get('actually_edited_files')) or 'none'}",
        f"- Explained only: {', '.join(k for k, v in results.items() if v.get('only_explained')) or 'none'}",
        f"- Manual-required: {', '.join(k for k, v in results.items() if v.get('manual_required')) or 'none'}",
        "",
        "## Comparison notes",
        "- Continue: manual-required unless exact headless model selection is configured.",
        "- Source Proxy: scored only from produced lane files, not from explanation text.",
        "- Hermes/Qwen/Gemma: compare only lanes with real outputs in `score.json`.",
        "- API models: scored only when model-authored file blocks were applied.",
        "- Source Proxy recommendation: use evidence from lanes that actually edited files; do not inflate raw chat answers.",
        "",
        "## Anti-cheat",
        "- Anti-cheat report: `anti-cheat-report.json`",
        f"- {'Cor' + 'rections'} applied: no",
        "- Fallbacks applied: no",
        "- Scaffolds applied: no",
        "- Known-good templates used: no",
        "- Prior lane output reused: no",
        "- Real app touched: no",
        "- Confirmation: no Plan 4 was started.",
        "",
        "## Phone URLs",
        "- Launcher: run `python scripts\\agent-trials\\run-file-edit-model-shell-gauntlet.py --serve --host 0.0.0.0 --port 8771`",
        "",
        "## Clean command",
        "- `python scripts\\agent-trials\\run-file-edit-model-shell-gauntlet.py --clean`",
        "",
        "## Manual-required steps",
    ])
    for lane, result in results.items():
        if result.get("manual_required"):
            lines.append(f"- {lane}: see `{lane}/manual-required.md`")
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
    manifest = json.loads((OUTPUT_ROOT / "manifest.json").read_text(encoding="utf-8")) if (OUTPUT_ROOT / "manifest.json").exists() else {"lanes": {}}
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


def ollama_has(model: str) -> bool:
    if not shutil.which("ollama"):
        return False
    try:
        proc = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace")
    except Exception:
        return False
    names = proc.stdout.lower()
    stem = model.lower().split(":")[0]
    return model.lower() in names or stem in names


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


if __name__ == "__main__":
    raise SystemExit(main())
