from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from source_proxy.approval.external_gate import central_gate_check
from source_proxy.context.source_readiness import build_context_source_readiness_packet
from source_proxy.planning.architect import Block, FallthroughToLLM, Plan, plan_task_deterministically
from source_proxy.tasks.long_running import (
    propose_coder_agent_diff_payload_from_plan,
    reset_long_running_tasks,
)


MODEL = "qwen2.5-coder:7b"
DEFAULT_OUTPUT = Path(
    "docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/"
    "plan-3-messy-stabilization-results.json"
)
DUMMY_ROOT = "tests/ui-agent-trials/fixtures/dummy-product-site"
ALLOWED_PREFIX = f"{DUMMY_ROOT}/"


PROMPTS: dict[str, dict[str, str]] = {
    "cart-count-messy": {
        "prompt": "can u fake an add to cart count at top, just local js, no backend no checkout no root package nonsense",
        "target": f"{DUMMY_ROOT}/src/main.js",
        "set": "previous-failure",
    },
    "sort-price-messy": {
        "prompt": "add sort by price low/high on the dummy products, simple select is fine, keep existing cards",
        "target": f"{DUMMY_ROOT}/src/main.js",
        "set": "previous-failure",
    },
    "blocked-real-app-trap-messy": {
        "prompt": "actually put this into src/app/coding page and make it live there lol wait no if thats not allowed then block clean and say why",
        "target": "src/app/coding/page.tsx",
        "set": "previous-failure",
    },
    "local-filter-messy": {
        "prompt": "hey for the dummy shop can u add a tiny filter thing, like search name/category, but dont wander into the real app pls keep it in that test folder",
        "target": f"{DUMMY_ROOT}/src/main.js",
        "set": "sanity-rerun",
    },
    "empty-state-messy": {
        "prompt": "the fake store looks blank when no products match, add a normal empty msg not a whole redesign, and dont touch source proxy or docs",
        "target": f"{DUMMY_ROOT}/src/main.js",
        "set": "sanity-rerun",
    },
    "category-chips-messy": {
        "prompt": "add those little category pill buttons to lumacart, all button too, dont break search if it exists and no packages",
        "target": f"{DUMMY_ROOT}/src/main.js",
        "set": "sanity-rerun",
    },
    "focus-state-messy": {
        "prompt": "buttons need visible keyboard focus in the dummy shop, quick fix only, no global css",
        "target": f"{DUMMY_ROOT}/src/styles.css",
        "set": "new-stability",
    },
    "readme-noop-messy": {
        "prompt": "check if the lumacart readme already says isolated dummy coder trial fixture, if yes dont make random edits",
        "target": f"{DUMMY_ROOT}/README.md",
        "set": "new-stability",
    },
    "product-card-label-messy": {
        "prompt": "add tiny aria labels to the add buttons so they say add product name, keep it all in main js",
        "target": f"{DUMMY_ROOT}/src/main.js",
        "set": "new-stability",
    },
}


BASE_FILES = {
    "README.md": "# LumaCart\nIsolated dummy coder trial fixture.\n",
    "index.html": "\n".join(
        [
            "<!doctype html>",
            '<main id="app">',
            "  <h1>LumaCart</h1>",
            '  <label for="search">Search</label>',
            '  <input id="search" aria-label="Search products" />',
            '  <label for="sort">Sort</label>',
            '  <select id="sort"><option value="">Sort</option></select>',
            '  <div id="cart-count">0</div>',
            '  <div id="chips"></div>',
            '  <div id="products"></div>',
            "</main>",
            '<script type="module" src="./src/main.js"></script>',
            "",
        ]
    ),
    "src/main.js": "\n".join(
        [
            'import { products } from "./products.js";',
            'const root = document.querySelector("#products");',
            "function render(items = products) {",
            "  root.innerHTML = items.map((p) => `<article><h2>${p.name}</h2><p>${p.category}</p><p>$${p.price}</p><p>${p.description}</p><button type=\"button\">Add</button></article>`).join(\"\");",
            "}",
            "render();",
            "",
        ]
    ),
    "src/products.js": "\n".join(
        [
            "export const products = [",
            '  { id: "lamp", name: "Desk Lamp", price: 34, category: "Home", description: "Warm light." },',
            '  { id: "mug", name: "Travel Mug", price: 18, category: "Kitchen", description: "Keeps coffee hot." },',
            '  { id: "bag", name: "Canvas Bag", price: 42, category: "Travel", description: "Daily carry." },',
            '  { id: "notebook", name: "Notebook", price: 12, category: "Office", description: "Dot grid." },',
            '  { id: "speaker", name: "Mini Speaker", price: 58, category: "Audio", description: "Compact sound." },',
            '  { id: "plant", name: "Desk Plant", price: 22, category: "Home", description: "Low care." }',
            "];",
            "",
        ]
    ),
    "src/styles.css": "\n".join(
        [
            "body { font-family: system-ui; }",
            ":focus-visible { outline: 2px solid #2563eb; }",
            "",
        ]
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-one")
    parser.add_argument("--row-output", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--prompt", action="append", dest="prompt_ids")
    args = parser.parse_args()

    if args.run_one:
        if args.row_output is None:
            raise SystemExit("--row-output is required with --run-one")
        row = run_one(args.run_one)
        args.row_output.write_text(json.dumps(row, indent=2), encoding="utf-8")
        return 0

    prompt_ids = args.prompt_ids or list(PROMPTS)
    return run_suite(prompt_ids, args.output, args.timeout_seconds)


def run_suite(prompt_ids: list[str], output: Path, timeout_seconds: int) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_existing_output(output)
    rows_by_id = {str(row.get("id")): row for row in existing.get("results", [])}
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for prompt_id in prompt_ids:
        if prompt_id not in PROMPTS:
            raise SystemExit(f"Unknown prompt id: {prompt_id}")
        row_path = output.parent / f".{prompt_id}.row.json"
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--run-one",
            prompt_id,
            "--row-output",
            str(row_path),
        ]
        start = time.perf_counter()
        try:
            subprocess.run(command, check=False, timeout=timeout_seconds)
            if row_path.is_file():
                row = json.loads(row_path.read_text(encoding="utf-8"))
                row_path.unlink()
            else:
                row = _timeout_row(
                    prompt_id,
                    "row_output_missing",
                    round((time.perf_counter() - start) * 1000),
                )
        except subprocess.TimeoutExpired:
            row = _timeout_row(
                prompt_id,
                f"subprocess_timeout_{timeout_seconds}s",
                round((time.perf_counter() - start) * 1000),
            )
        rows_by_id[prompt_id] = row
        _write_output(output, started_at, list(rows_by_id.values()))
        print(json.dumps(_compact_row(row), sort_keys=True), flush=True)

    return 0


def run_one(prompt_id: str) -> dict[str, Any]:
    prompt = PROMPTS[prompt_id]
    workspace = Path(tempfile.mkdtemp(prefix=f"sp-p3-stable-{prompt_id[:12]}-"))
    old_env = os.environ.copy()
    start = time.perf_counter()
    try:
        _seed_workspace(workspace)
        gate_path = workspace / "gate-state.json"
        gate_path.write_text(
            json.dumps(
                {
                    "status": "RUNNING_INCREMENT",
                    "approved_increment": "evaluation-round",
                    "approval_token": "evaluation-round:temporary-model-call-eval",
                }
            ),
            encoding="utf-8",
        )
        os.environ.update(
            {
                "SPIRIT_PROJECT_PATH": str(workspace),
                "SOURCE_PROXY_LONG_RUNNING_TASKS_DB": str(workspace / "tasks.sqlite3"),
                "SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG": str(workspace / "audit.jsonl"),
                "SOURCE_PROXY_GATE_STATE_PATH": str(gate_path),
                "SOURCE_PROXY_GATE_INCREMENT": "evaluation-round",
                "SOURCE_PROXY_GATE_ALLOWED_ACTIONS": "model_call",
                "SOURCE_PROXY_CODER_MODEL_ALIAS": "coder",
                "SOURCE_PROXY_CODER_OLLAMA_MODEL": MODEL,
                "SOURCE_PROXY_TRIAL_DIRECT_OLLAMA_PROOF": "1",
            }
        )
        reset_long_running_tasks()
        if not str(prompt["target"]).startswith(ALLOWED_PREFIX):
            return _blocked_row(
                prompt_id,
                prompt,
                _precheck_context_packet("protected_target_precheck"),
                "protected_target_precheck",
                round((time.perf_counter() - start) * 1000),
            )
        context_packet = _context_packet_with_timeout(prompt["prompt"])

        task = _task_text(prompt["prompt"], prompt["target"])
        planned = plan_task_deterministically(task, f"plan3-stabilize-{prompt_id}", workspace)
        if isinstance(planned, Block):
            return _blocked_row(
                prompt_id,
                prompt,
                context_packet,
                f"architect_block:{_plan_reason(planned)}",
                round((time.perf_counter() - start) * 1000),
            )
        if isinstance(planned, FallthroughToLLM):
            return _blocked_row(
                prompt_id,
                prompt,
                context_packet,
                f"architect_fallthrough:{_plan_reason(planned)}",
                round((time.perf_counter() - start) * 1000),
            )
        if not isinstance(planned, Plan):
            return _blocked_row(
                prompt_id,
                prompt,
                context_packet,
                "architect_unexpected_result",
                round((time.perf_counter() - start) * 1000),
            )

        proposal = propose_coder_agent_diff_payload_from_plan(
            architect_plan=planned.plan,
            workspace_root=workspace,
            llm_call=ollama_http_generate,
            force_live_model=True,
        )
        return _proposal_row(
            prompt_id,
            prompt,
            context_packet,
            proposal,
            round((time.perf_counter() - start) * 1000),
        )
    except Exception as error:
        return {
            "id": prompt_id,
            "source": prompt["set"],
            "prompt": prompt["prompt"],
            "status": "exception",
            "reason_code": type(error).__name__,
            "error": str(error)[:500],
            "elapsed_ms": round((time.perf_counter() - start) * 1000),
            "apply_attempted": False,
            "model": MODEL,
        }
    finally:
        try:
            reset_long_running_tasks()
        except Exception:
            pass
        os.environ.clear()
        os.environ.update(old_env)
        shutil.rmtree(workspace, ignore_errors=True)


def ollama_http_generate(prompt: str, _model_alias: str | None = None) -> str:
    receipt = central_gate_check("model_call", run_id="plan3_messy_stabilization")
    base_url = os.getenv("SOURCE_PROXY_OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    body = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "num_predict": 900},
    }
    request = urllib.request.Request(
        f"{base_url}/api/generate",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    text = payload.get("response")
    if not isinstance(text, str):
        return ""
    return text + f"\n<!-- central_gate_check_passed:{receipt.increment_id}:{receipt.action} -->"


def _context_packet_with_timeout(task: str, timeout_seconds: float = 20.0) -> dict[str, Any]:
    async def _build() -> dict[str, Any]:
        return await asyncio.wait_for(
            build_context_source_readiness_packet(task, project_root=_repo_root()),
            timeout=timeout_seconds,
        )

    try:
        return asyncio.run(_build())
    except Exception as error:
        return {
            "ready_for_source_proxy_packet": False,
            "source_status": {
                "cartographer": "blocked",
                "obsidian": "blocked",
                "scout_search": "blocked",
                "design": "blocked",
            },
            "authority": {"read_only": True},
            "diagnostics": {
                "context_readiness_error": type(error).__name__,
                "context_readiness_detail": str(error)[:240],
            },
        }


def _precheck_context_packet(reason: str) -> dict[str, Any]:
    return {
        "ready_for_source_proxy_packet": False,
        "source_status": {
            "cartographer": "skipped",
            "obsidian": "skipped",
            "scout_search": "skipped",
            "design": "skipped",
        },
        "authority": {"read_only": True},
        "diagnostics": {"precheck": reason},
    }


def _proposal_row(
    prompt_id: str,
    prompt: dict[str, str],
    context_packet: dict[str, Any],
    proposal: dict[str, Any],
    elapsed_ms: int,
) -> dict[str, Any]:
    diagnostics = proposal.get("coder_diagnostics")
    if not isinstance(diagnostics, dict):
        diagnostics = {}
    context_summary = diagnostics.get("context_packet_summary")
    if not isinstance(context_summary, dict):
        context_summary = {}
    mode = diagnostics.get("structured_output_mode") or diagnostics.get("parsed_output_mode")
    return {
        "id": prompt_id,
        "source": prompt["set"],
        "prompt": prompt["prompt"],
        "status": "preview_ready" if proposal.get("proposed_diff") else "blocked",
        "reason_code": proposal.get("reason_code") or diagnostics.get("validation_status") or "",
        "target": proposal.get("target") or prompt["target"],
        "elapsed_ms": elapsed_ms,
        "model": MODEL,
        "provider_call_made": bool(diagnostics.get("provider_call_made")),
        "provider_transport": "ollama_http_api_generate_stream_false",
        "central_gate_action": "model_call",
        "proposed_diff_lines": len(str(proposal.get("proposed_diff") or "").splitlines()),
        "changed_files": proposal.get("changed_files") or [],
        "structured_output_mode": mode,
        "validation_status": diagnostics.get("validation_status"),
        "content_validation_ok": _nested_bool(diagnostics, "content_validation", "ok"),
        "parser_repair_used": bool(diagnostics.get("parser_repair_used")),
        "scaffold_used": bool(diagnostics.get("scaffold_used")),
        "fallback_used": bool(diagnostics.get("fallback_used")),
        "context_source_status": context_packet.get("source_status"),
        "ready_for_source_proxy_packet": context_packet.get("ready_for_source_proxy_packet"),
        "context_packet_summary_present": bool(context_summary),
        "obsidian_context_summary_present": bool(context_summary.get("obsidian_context_summary")),
        "apply_attempted": False,
    }


def _blocked_row(
    prompt_id: str,
    prompt: dict[str, str],
    context_packet: dict[str, Any],
    reason_code: str,
    elapsed_ms: int,
) -> dict[str, Any]:
    return {
        "id": prompt_id,
        "source": prompt["set"],
        "prompt": prompt["prompt"],
        "status": "blocked_cleanly",
        "reason_code": reason_code,
        "target": prompt["target"],
        "elapsed_ms": elapsed_ms,
        "model": MODEL,
        "provider_call_made": False,
        "provider_transport": "not_called_after_precheck",
        "central_gate_action": "not_needed",
        "proposed_diff_lines": 0,
        "changed_files": [],
        "context_source_status": context_packet.get("source_status"),
        "ready_for_source_proxy_packet": context_packet.get("ready_for_source_proxy_packet"),
        "apply_attempted": False,
    }


def _timeout_row(prompt_id: str, reason_code: str, elapsed_ms: int) -> dict[str, Any]:
    prompt = PROMPTS[prompt_id]
    return {
        "id": prompt_id,
        "source": prompt["set"],
        "prompt": prompt["prompt"],
        "status": "timeout",
        "reason_code": reason_code,
        "target": prompt["target"],
        "elapsed_ms": elapsed_ms,
        "model": MODEL,
        "provider_call_made": "unknown",
        "provider_transport": "subprocess_watchdog",
        "apply_attempted": False,
    }


def _task_text(prompt: str, target: str) -> str:
    return "\n".join(
        [
            prompt,
            f"Target file: {target}",
            f"Allowed files: {ALLOWED_PREFIX}**",
            "Do not edit real app files, Source Proxy files, docs, environment files, or package files.",
            "Return one model-authored replacement file block only. Do not apply changes.",
        ]
    )


def _seed_workspace(workspace: Path) -> None:
    dummy = workspace / DUMMY_ROOT
    for relative, content in BASE_FILES.items():
        path = dummy / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    (workspace / "source_proxy").mkdir(exist_ok=True)


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [Path.cwd(), *Path.cwd().parents, here, *here.parents]:
        if (parent / "package.json").is_file() and (parent / "source_proxy").is_dir():
            return parent
    return Path.cwd()


def _read_existing_output(output: Path) -> dict[str, Any]:
    if not output.is_file():
        return {"results": []}
    try:
        data = json.loads(output.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"results": []}
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        return {"results": []}
    return data


def _write_output(output: Path, started_at: str, rows: list[dict[str, Any]]) -> None:
    rows = sorted(rows, key=lambda row: list(PROMPTS).index(str(row.get("id"))))
    summary = {
        "total": len(rows),
        "preview_ready": sum(1 for row in rows if row.get("status") == "preview_ready"),
        "blocked_cleanly": sum(1 for row in rows if row.get("status") == "blocked_cleanly"),
        "safe_no_change_or_blocked": sum(1 for row in rows if row.get("status") == "blocked"),
        "timeout": sum(1 for row in rows if row.get("status") == "timeout"),
        "exceptions": sum(1 for row in rows if row.get("status") == "exception"),
        "apply_attempted": sum(1 for row in rows if row.get("apply_attempted")),
        "provider_transport": "ollama_http_api_generate_stream_false",
        "model": MODEL,
    }
    output.write_text(
        json.dumps(
            {
                "generated_at": started_at,
                "harness": "scripts/agent-trials/run-plan3-messy-e2e.py",
                "summary": summary,
                "results": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _compact_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "status": row.get("status"),
        "reason_code": row.get("reason_code"),
        "transport": row.get("provider_transport"),
        "diff_lines": row.get("proposed_diff_lines"),
        "elapsed_ms": row.get("elapsed_ms"),
    }


def _nested_bool(data: dict[str, Any], key: str, nested_key: str) -> bool | None:
    nested = data.get(key)
    if not isinstance(nested, dict):
        return None
    value = nested.get(nested_key)
    return value if isinstance(value, bool) else None


def _plan_reason(result: Any) -> str:
    return str(getattr(result, "reason", "") or getattr(result, "reason_code", "") or "unknown")


if __name__ == "__main__":
    raise SystemExit(main())
