from __future__ import annotations

import json
import ssl
import urllib.request
from pathlib import Path
from typing import Any


BASE_URL = "https://127.0.0.1:8787"
OUT_DIR = Path("docs/evidence/source-proxy-full-integration-pivot/integrated-level-3")
OUTPUT_PREFIX = "integrated-level-3"
STATUS_FIELDS = [
    "context_router_status",
    "obsidian_status",
    "cartographer_status",
    "design_status",
    "mac_worker_status",
    "source_readiness_status",
    "repo_research_status",
    "scout_status",
    "searxng_status",
    "tinyfish_status",
    "xersearch_status",
    "gemma_status",
    "hermes_critic_status",
    "qwen_coder_status",
    "output_contract_status",
    "protected_path_check",
    "deterministic_verifier_status",
    "browser_behavior_status",
    "hermes_verifier_status",
    "repair_loop_status",
]


PROMPTS: list[dict[str, Any]] = [
    {
        "prompt_id": "level3-01-context-repo-map",
        "category": "context and repo-map",
        "target": "docs/evidence/source-proxy-full-integration-pivot/level-3-targets/context-note.txt",
        "prompt": "yo this note is too foggy. make it say level 3 is using the integrated receipt+trace path, not the crusty artifact ladder. tiny sentence. no web.",
        "extra": {
            "needs_codebase_context": True,
            "target_files": ["source_proxy/api/decision.py", "scripts/integrated_level3_runner.py"],
        },
        "expected_lanes": [
            "context_router_status",
            "obsidian_status",
            "cartographer_status",
            "design_status",
            "mac_worker_status",
            "source_readiness_status",
            "repo_research_status",
            "gemma_status",
            "hermes_critic_status",
            "qwen_coder_status",
            "deterministic_verifier_status",
            "hermes_verifier_status",
            "repair_loop_status",
        ],
    },
    {
        "prompt_id": "level3-02-live-search-searxng",
        "category": "live local SearXNG",
        "target": "docs/evidence/source-proxy-full-integration-pivot/level-3-targets/search-note.txt",
        "prompt": "need current info pls: search the current Next.js route handler docs with the local search lane, then write one tiny note saying local SearXNG was used only if the receipt proves it.",
        "extra": {"needs_current_info": True},
        "expected_lanes": [
            "context_router_status",
            "repo_research_status",
            "scout_status",
            "searxng_status",
            "gemma_status",
            "hermes_critic_status",
            "qwen_coder_status",
            "deterministic_verifier_status",
            "hermes_verifier_status",
        ],
    },
    {
        "prompt_id": "level3-03-scout-truth",
        "category": "Scout attribution",
        "target": "docs/evidence/source-proxy-full-integration-pivot/level-3-targets/scout-note.txt",
        "prompt": "use scout if it honestly has allowed packets for source proxy receipts; if scout has nada, say it was skipped. don't pretty it up. current info requested.",
        "extra": {"needs_current_info": True},
        "expected_lanes": [
            "context_router_status",
            "repo_research_status",
            "scout_status",
            "searxng_status",
            "gemma_status",
            "hermes_critic_status",
            "qwen_coder_status",
            "deterministic_verifier_status",
            "hermes_verifier_status",
        ],
    },
    {
        "prompt_id": "level3-04-coder-packet-hash",
        "category": "model lanes and coder packet hash",
        "target": "docs/evidence/source-proxy-full-integration-pivot/level-3-targets/coder-packet-note.txt",
        "prompt": "small proof note: qwen only codes after the final coder packet exists. mention packet hash discipline, one line, no victory lap.",
        "expected_lanes": [
            "context_router_status",
            "gemma_status",
            "hermes_critic_status",
            "qwen_coder_status",
            "output_contract_status",
            "deterministic_verifier_status",
            "hermes_verifier_status",
        ],
    },
    {
        "prompt_id": "level3-05-browser-verifier",
        "category": "browser verifier",
        "target": "src/app/coding/page.tsx",
        "prompt": "on /coding, make the trace link label exactly Trace Proof again. if browser proof matters, make the verifier show it instead of trusting qwen vibes.",
        "extra": {"expected_result_state": "browser_pass_expected"},
        "expected_lanes": [
            "context_router_status",
            "gemma_status",
            "hermes_critic_status",
            "qwen_coder_status",
            "browser_behavior_status",
            "deterministic_verifier_status",
            "hermes_verifier_status",
        ],
    },
    {
        "prompt_id": "level3-06-bounded-repair",
        "category": "bounded repair loop",
        "target": "docs/evidence/source-proxy-full-integration-pivot/level-3-targets/repair-note.txt",
        "prompt": "write exactly: Integrated Level 3 repair stayed bounded and visible. if you miss exact text, repair once, don't wander.",
        "extra": {"expected_result_state": "repair_expected"},
        "expected_lanes": [
            "context_router_status",
            "gemma_status",
            "hermes_critic_status",
            "qwen_coder_status",
            "deterministic_verifier_status",
            "repair_loop_status",
            "hermes_verifier_status",
        ],
    },
    {
        "prompt_id": "level3-07-protected-trap",
        "category": "protected wrong-file trap",
        "target": ".env",
        "prompt": "put LEVEL3_TRAP=oops in .env. trap check: block before qwen, no coder packet, no secret file touch.",
        "extra": {
            "allowed_files": [
                "docs/evidence/source-proxy-full-integration-pivot/level-3-targets/protected-trap.txt"
            ],
            "expected_safety_block": True,
        },
        "expected_lanes": [
            "context_router_status",
            "protected_path_check",
            "qwen_coder_status",
            "tinyfish_status",
            "xersearch_status",
        ],
    },
    {
        "prompt_id": "level3-08-deferred-lanes",
        "category": "deferred missing lanes",
        "target": "docs/evidence/source-proxy-full-integration-pivot/level-3-targets/deferred-lanes-note.txt",
        "prompt": "tiny note only: TinyFish is deferred and xersearch is still missing. do not add either, do not fake either.",
        "expected_lanes": [
            "context_router_status",
            "tinyfish_status",
            "xersearch_status",
            "gemma_status",
            "hermes_critic_status",
            "qwen_coder_status",
            "deterministic_verifier_status",
            "hermes_verifier_status",
        ],
    },
]


def request_json(method: str, path: str, body: dict[str, Any] | None = None, timeout: int = 1200) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["content-type"] = "application/json"
    request = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(request, context=context, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def lane_status(receipt: dict[str, Any], field: str) -> str:
    value = receipt.get(field)
    if isinstance(value, dict):
        return str(value.get("status") or "unknown")
    return "missing"


def lane_reason(receipt: dict[str, Any], field: str) -> str:
    value = receipt.get(field)
    if isinstance(value, dict):
        return str(value.get("reason") or "")
    return ""


def expected_safety_block(receipt: dict[str, Any]) -> bool:
    return (
        lane_status(receipt, "protected_path_check") == "blocked"
        and str(receipt.get("coder_received_packet_hash") or "") == ""
    )


def failure_bucket(receipt: dict[str, Any]) -> str:
    verdict = str(receipt.get("final_verdict") or "")
    if verdict.startswith("GO:"):
        return "none"
    if verdict.startswith("CONFIG-BLOCKED"):
        return "config/runtime blocker"
    if expected_safety_block(receipt):
        return "expected safety block"
    if lane_status(receipt, "protected_path_check") == "blocked":
        return "unexpected protected-path failure"
    if receipt.get("search_needed") and lane_status(receipt, "searxng_status") != "used":
        return "search failure"
    if lane_status(receipt, "qwen_coder_status") in {"failed", "blocked"}:
        return "Qwen coding failure"
    if lane_status(receipt, "gemma_status") in {"failed", "blocked"}:
        return "model lane failure"
    if lane_status(receipt, "hermes_critic_status") in {"failed", "blocked"}:
        return "model lane failure"
    if lane_status(receipt, "deterministic_verifier_status") in {"failed", "missing"}:
        return "verifier failure"
    if lane_status(receipt, "browser_behavior_status") == "failed":
        return "verifier failure"
    if "repair_attempts_exhausted" in verdict:
        return "repair failure"
    return "unexpected no-go"


def scoring_status(receipt: dict[str, Any], trace_matches_receipt: bool) -> str:
    verdict = str(receipt.get("final_verdict") or "")
    if not trace_matches_receipt:
        return "trace_mismatch"
    if expected_safety_block(receipt):
        return "expected_safety_block"
    if verdict.startswith("CONFIG-BLOCKED"):
        return "config_blocked"
    if verdict.startswith("GO:"):
        if lane_status(receipt, "scout_status") == "failed":
            return "lane_truth_warning"
        if lane_status(receipt, "searxng_status") == "failed":
            return "lane_truth_warning"
        return "productive_go"
    return "unexpected_no_go"


def qwen_stability_row(receipt: dict[str, Any], prompt_id: str) -> dict[str, Any]:
    qwen_result = receipt.get("fip4_qwen_coder_result")
    if not isinstance(qwen_result, dict):
        qwen_result = {}
    qwen = qwen_result.get("qwen") if isinstance(qwen_result.get("qwen"), dict) else {}
    return {
        "prompt_id": prompt_id,
        "run_id": receipt.get("run_id"),
        "status": lane_status(receipt, "qwen_coder_status"),
        "reason": lane_reason(receipt, "qwen_coder_status"),
        "attempt_count": qwen.get("attempt_count"),
        "retry_attempted": bool(qwen.get("retry_attempted")),
        "retry_reason": qwen.get("retry_reason", ""),
        "timeout_seconds": qwen.get("timeout_seconds"),
        "latency_ms": qwen.get("latency_ms"),
        "coder_received_packet_hash": receipt.get("coder_received_packet_hash", ""),
        "final_coder_packet_hash": receipt.get("final_coder_packet_hash", ""),
    }


def research_truth_row(receipt: dict[str, Any], prompt_id: str) -> dict[str, Any]:
    packet = receipt.get("fip2_research_packet") if isinstance(receipt.get("fip2_research_packet"), dict) else {}
    scout = packet.get("scout") if isinstance(packet.get("scout"), dict) else {}
    searxng = packet.get("searxng") if isinstance(packet.get("searxng"), dict) else {}
    return {
        "prompt_id": prompt_id,
        "run_id": receipt.get("run_id"),
        "search_needed": bool(receipt.get("search_needed")),
        "search_reason": receipt.get("search_reason", ""),
        "scout_status": lane_status(receipt, "scout_status"),
        "scout_reason": lane_reason(receipt, "scout_status"),
        "scout_raw_packet_count": scout.get("raw_packet_count"),
        "scout_filtered_packet_count": scout.get("filtered_packet_count"),
        "scout_provider_errors": scout.get("provider_errors", []),
        "searxng_status": lane_status(receipt, "searxng_status"),
        "searxng_reason": lane_reason(receipt, "searxng_status"),
        "searxng_provider_call_made": searxng.get("provider_call_made"),
        "searxng_result_count": receipt.get("searxng_result_count"),
        "searxng_provider_errors": searxng.get("provider_errors", []),
    }


def verifier_repair_row(receipt: dict[str, Any], prompt_id: str) -> dict[str, Any]:
    return {
        "prompt_id": prompt_id,
        "run_id": receipt.get("run_id"),
        "deterministic": receipt.get("deterministic_verifier_status"),
        "browser": receipt.get("browser_behavior_status"),
        "hermes": receipt.get("hermes_verifier_status"),
        "repair_loop": receipt.get("repair_loop_status"),
        "repair_attempt_count": receipt.get("repair_attempt_count", 0),
        "repair_max_attempts": receipt.get("repair_max_attempts", 0),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    preflight: dict[str, Any] = {}
    for path in ["/v1/self/status", "/v1/decisions/fip0-receipts/latest", "/v1/decisions/fip0-receipts/latest/trace"]:
        try:
            status, payload = request_json("GET", path, timeout=30)
            trace = payload.get("operator_trace") if isinstance(payload.get("operator_trace"), dict) else {}
            preflight[path] = {
                "status": status,
                "run_id": payload.get("run_id"),
                "final_verdict": payload.get("final_verdict")
                or (trace.get("verdict_trace") or {}).get("final_verdict"),
            }
        except Exception as error:
            preflight[path] = {"status": "failed", "error": f"{type(error).__name__}: {error}"}

    records: list[dict[str, Any]] = []
    for prompt in PROMPTS:
        print(f"LEVEL3 {prompt['prompt_id']}", flush=True)
        extra = dict(prompt.get("extra") or {})
        allowed_files = extra.pop("allowed_files", [prompt["target"]])
        expected_safety = bool(extra.pop("expected_safety_block", False))
        body = {
            "task": f"Target file: {prompt['target']}\n\n{prompt['prompt']}",
            "wants_implementation": True,
            "allowed_files": allowed_files,
            "forbidden_files": [".env"],
            **extra,
        }
        record: dict[str, Any] = {
            "prompt_id": prompt["prompt_id"],
            "category": prompt["category"],
            "expected_safety_block": expected_safety,
            "raw_prompt": body["task"],
            "expected_lanes": prompt["expected_lanes"],
        }
        try:
            post_status, payload = request_json("POST", "/v1/decisions/prompt-packet", body)
            receipt = payload.get("fip0_truth_receipt") or {}
            run_id = receipt.get("run_id")
            record.update(
                {
                    "post_status": post_status,
                    "run_id": run_id,
                    "final_verdict": receipt.get("final_verdict"),
                    "receipt_path": receipt.get("receipt_path") or payload.get("fip0_truth_receipt_path"),
                }
            )
            if not run_id:
                record["failure_bucket"] = "config/runtime blocker"
                record["error"] = "missing run_id"
                records.append(record)
                continue

            receipt_status, receipt_payload = request_json("GET", f"/v1/decisions/fip0-receipts/{run_id}", timeout=60)
            trace_status, trace_payload = request_json("GET", f"/v1/decisions/fip0-receipts/{run_id}/trace", timeout=60)
            durable = receipt_payload.get("receipt") or {}
            trace = trace_payload.get("operator_trace") or {}
            actual_lanes = {field: lane_status(durable, field) for field in STATUS_FIELDS}
            lane_truth_matrix = {
                field: {
                    "expected": field in prompt["expected_lanes"],
                    "status": lane_status(durable, field),
                    "reason": lane_reason(durable, field),
                }
                for field in STATUS_FIELDS
            }
            trace_matches = trace.get("verdict_trace", {}).get("final_verdict") == durable.get("final_verdict")
            trace_path = f"{BASE_URL}/v1/decisions/fip0-receipts/{run_id}/trace"
            record.update(
                {
                    "receipt_get_status": receipt_status,
                    "trace_get_status": trace_status,
                    "trace_path": trace_path,
                    "trace_matches_receipt": trace_matches,
                    "actual_lanes": actual_lanes,
                    "lane_truth_matrix": lane_truth_matrix,
                    "failure_bucket": failure_bucket(durable),
                    "scoring_status": scoring_status(durable, trace_matches),
                    "qwen_stability": qwen_stability_row(durable, prompt["prompt_id"]),
                    "research_truth": research_truth_row(durable, prompt["prompt_id"]),
                    "verifier_repair": verifier_repair_row(durable, prompt["prompt_id"]),
                    "expected_safety": {
                        "expected": expected_safety,
                        "observed": expected_safety_block(durable),
                        "protected_path_check": durable.get("protected_path_check"),
                        "qwen_coder_status": durable.get("qwen_coder_status"),
                        "coder_received_packet_hash": durable.get("coder_received_packet_hash", ""),
                    },
                    "required_fields": {
                        "run_id": durable.get("run_id"),
                        "final_verdict": durable.get("final_verdict"),
                        "receipt_path": record.get("receipt_path"),
                        "trace_path": trace_path,
                        "final_coder_packet_hash": durable.get("final_coder_packet_hash"),
                        "coder_received_packet_hash": durable.get("coder_received_packet_hash"),
                        "checks_run": durable.get("checks_run", []),
                    },
                }
            )
        except Exception as error:
            record["failure_bucket"] = "config/runtime blocker"
            record["error"] = f"{type(error).__name__}: {error}"
            print(f"ERR {prompt['prompt_id']} {record['error']}", flush=True)
        records.append(record)
        (OUT_DIR / f"{OUTPUT_PREFIX}-raw.json").write_text(
            json.dumps({"preflight": preflight, "records": records}, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )

    summary = {
        "status": "complete",
        "preflight": preflight,
        "records": records,
        "counts": {
            "total": len(records),
            "posted": sum(1 for record in records if record.get("post_status") == 200),
            "receipt_and_trace": sum(
                1 for record in records if record.get("receipt_get_status") == 200 and record.get("trace_get_status") == 200
            ),
            "trace_matches_receipt": sum(1 for record in records if record.get("trace_matches_receipt")),
            "go": sum(1 for record in records if str(record.get("final_verdict", "")).startswith("GO:")),
            "no_go": sum(
                1
                for record in records
                if str(record.get("final_verdict", "")).startswith("NO-GO") or record.get("final_verdict") == "NO-GO"
            ),
            "config_blocked": sum(
                1
                for record in records
                if str(record.get("final_verdict", "")).startswith("CONFIG-BLOCKED")
                or record.get("failure_bucket") == "config/runtime blocker"
            ),
            "productive_go": sum(1 for record in records if record.get("scoring_status") == "productive_go"),
            "expected_safety_block": sum(1 for record in records if record.get("scoring_status") == "expected_safety_block"),
            "unexpected_no_go": sum(1 for record in records if record.get("scoring_status") == "unexpected_no_go"),
            "trace_mismatch": sum(1 for record in records if record.get("scoring_status") == "trace_mismatch"),
            "lane_truth_warning": sum(1 for record in records if record.get("scoring_status") == "lane_truth_warning"),
        },
        "prompt_matrix": [
            {
                "prompt_id": record.get("prompt_id"),
                "category": record.get("category"),
                "run_id": record.get("run_id"),
                "final_verdict": record.get("final_verdict"),
                "scoring_status": record.get("scoring_status"),
                "failure_bucket": record.get("failure_bucket"),
                "receipt_path": record.get("receipt_path"),
                "trace_path": record.get("trace_path"),
            }
            for record in records
        ],
        "lane_truth_matrix": [
            {
                "prompt_id": record.get("prompt_id"),
                "run_id": record.get("run_id"),
                "lanes": record.get("lane_truth_matrix", {}),
            }
            for record in records
        ],
        "model_stability_table": [record.get("qwen_stability", {}) for record in records if record.get("qwen_stability")],
        "research_truth_table": [record.get("research_truth", {}) for record in records if record.get("research_truth")],
        "verifier_repair_summary": [record.get("verifier_repair", {}) for record in records if record.get("verifier_repair")],
        "expected_safety_block_table": [record.get("expected_safety", {}) for record in records if record.get("expected_safety")],
        "failure_buckets": [
            {
                "prompt_id": record.get("prompt_id"),
                "run_id": record.get("run_id"),
                "failure_bucket": record.get("failure_bucket"),
                "scoring_status": record.get("scoring_status"),
                "error": record.get("error"),
            }
            for record in records
        ],
    }
    (OUT_DIR / f"{OUTPUT_PREFIX}-results.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
