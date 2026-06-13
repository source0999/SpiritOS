from __future__ import annotations

import argparse
import json
import urllib.request
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from source_proxy.decision.artifact_repair_contract import build_behavior_failure_packet
from source_proxy.decision.artifact_repair_loop import run_limited_artifact_repair_loop


DEFAULT_MODEL_ID = "qwen2.5-coder:7b"
DEFAULT_OLLAMA_API = "http://127.0.0.1:11434"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--browser-results", required=True)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--ollama-api", default=DEFAULT_OLLAMA_API)
    args = parser.parse_args()

    run_root = Path(args.run_root).resolve()
    browser_results_path = Path(args.browser_results).resolve()
    browser_results = _read_json(browser_results_path)
    repair_summaries: list[dict[str, Any]] = []

    for row in browser_results.get("results") or []:
        if str(((row.get("behavior_probe") or {}).get("verdict") or "")).upper() != "FAIL":
            repair_summaries.append(_skipped(row, "behavior_not_failed"))
            continue
        run_dir = run_root / str(row.get("run") or "")
        score_path = run_dir / "score.json"
        if not score_path.is_file():
            repair_summaries.append(_skipped(row, "score_missing"))
            continue
        score = _read_json(score_path)
        if not _eligible(score):
            repair_summaries.append(_skipped(row, "not_eligible_for_behavior_repair"))
            continue
        existing_repair_path = run_dir / "post-behavior-repair-result.json"
        if existing_repair_path.is_file():
            repair_result = _read_json(existing_repair_path)
            repair_summaries.append(
                {
                    "run": row.get("run"),
                    "prompt": score.get("prompt"),
                    "eligible": True,
                    "repair_status": repair_result.get("status"),
                    "attempts_used": repair_result.get("attempts_used"),
                    "repaired_files": repair_result.get("repaired_files") or repair_result.get("changed_files") or [],
                    "repair_model_authored_targets": repair_result.get("repair_model_authored_targets") or [],
                    "file_equals_model_action_content": repair_result.get("file_equals_model_action_content"),
                    "reason_codes": repair_result.get("reason_codes") or [],
                    "reused_existing_result": True,
                }
            )
            continue
        before_probe = run_dir / "behavior-probe.json"
        if before_probe.is_file():
            (run_dir / "behavior-probe-before-repair.json").write_text(
                before_probe.read_text(encoding="utf-8-sig"),
                encoding="utf-8",
            )

        workspace = Path(str(score.get("workspace_path") or "")).resolve()
        packet = build_behavior_failure_packet(
            prompt=str(score.get("prompt") or row.get("prompt") or ""),
            artifact_class=str(score.get("artifact_class") or ""),
            behavior_contract=dict(score.get("behavior_contract") or {}),
            behavior_probe=dict(row.get("behavior_probe") or {}),
            selected_preview_path=str(score.get("selected_preview_path") or row.get("preview_path_local") or ""),
            generated_files=list(score.get("workspace_files") or score.get("files_changed") or []),
            model_authored_targets=list(score.get("model_authored_targets") or []),
            final_reason_codes=list(score.get("final_verdict_reason_codes") or []),
            allowed_workspace=str(workspace),
            attempt_count=0,
            console_details=dict(row.get("open_probe") or {}),
        )
        _write_json(run_dir / "behavior-failure-packet.json", packet)

        if packet.get("handoff_required"):
            repair_result = {
                "status": "HANDOFF",
                "handoff_required": True,
                "handoff_reason": "failure_packet_requires_handoff",
                "attempts_used": 0,
                "reason_codes": list(packet.get("reason_codes") or []),
            }
        else:
            repair_result = run_limited_artifact_repair_loop(
                failure_packet=packet,
                repair_call=lambda _packet, prompt, _attempt, model_id=args.model_id, api=args.ollama_api: _ollama_generate(
                    prompt,
                    model_id=model_id,
                    ollama_api=api,
                ),
                max_attempts=1,
                model_id=args.model_id,
            )
        _write_json(run_dir / "post-behavior-repair-result.json", repair_result)
        repair_summaries.append(
            {
                "run": row.get("run"),
                "prompt": score.get("prompt"),
                "eligible": True,
                "repair_status": repair_result.get("status"),
                "attempts_used": repair_result.get("attempts_used"),
                "repaired_files": repair_result.get("repaired_files") or repair_result.get("changed_files") or [],
                "repair_model_authored_targets": repair_result.get("repair_model_authored_targets") or [],
                "file_equals_model_action_content": repair_result.get("file_equals_model_action_content"),
                "reason_codes": repair_result.get("reason_codes") or [],
            }
        )

    out = {
        "repair_summary_version": "anti-tailoring-post-behavior-repair-v1",
        "run_root": str(run_root),
        "browser_results": str(browser_results_path),
        "model_id": args.model_id,
        "repairs": repair_summaries,
    }
    _write_json(browser_results_path.with_name(browser_results_path.stem.replace("-browser-behavior-results", "") + "-post-behavior-repair-summary.json"), out)
    print(json.dumps({"repairs": len([item for item in repair_summaries if item.get("eligible")]), "total": len(repair_summaries)}, indent=2))


def _eligible(score: dict[str, Any]) -> bool:
    if str(score.get("route_status") or "").upper() != "GO":
        return False
    if str(score.get("artifact_class") or "") not in {"static_ui_artifact", "html_static_page"}:
        return False
    if not score.get("selected_preview_path"):
        return False
    blocked = set(str(code) for code in score.get("reason_codes") or [])
    authority = {"protected_path", "path_escape", "target_not_allowed", "symlink_escape"}
    if blocked & authority:
        return False
    return not bool(score.get("real_app_touched")) and not bool(score.get("backend_created_content"))


def _ollama_generate(prompt: str, *, model_id: str, ollama_api: str) -> str:
    payload = {
        "model": model_id,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "10m",
        "options": {"temperature": 0, "num_predict": 2200},
    }
    request = urllib.request.Request(
        f"{ollama_api.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        parsed = json.loads(response.read().decode("utf-8", errors="replace"))
    return str(parsed.get("response") or "")


def _skipped(row: dict[str, Any], reason: str) -> dict[str, Any]:
    return {"run": row.get("run"), "prompt": row.get("prompt"), "eligible": False, "skip_reason": reason}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
