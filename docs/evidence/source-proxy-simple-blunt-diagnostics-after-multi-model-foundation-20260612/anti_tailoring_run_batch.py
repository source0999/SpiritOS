from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from source_proxy.decision.artifact_final_verdict import (
    classify_artifact_score_integrity,
    classify_repair_failure_bucket,
)
from source_proxy.decision.human_messy_homepage import run_human_messy_homepage


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--html", required=True)
    parser.add_argument("--run-receipt", required=True)
    parser.add_argument("--browser-results", required=True)
    parser.add_argument("--repair-summary", required=True)
    parser.add_argument("--model-id", default="qwen2.5-coder:7b")
    parser.add_argument("--ollama-api", default="http://127.0.0.1:11434")
    args = parser.parse_args()

    prompt_path = _path(args.prompt_file)
    prompt_doc = _read_json(prompt_path)
    prompts = list(prompt_doc.get("prompts") or [])
    run_root = _path(args.run_root)
    run_root.mkdir(parents=True, exist_ok=True)
    receipt_rows: list[dict[str, Any]] = []

    for index, prompt_row in enumerate(prompts, start=1):
        prompt = str(prompt_row.get("prompt") or "")
        run_name = f"{index:02d}-{_slug(prompt)}"
        run_dir = run_root / run_name
        score_path = run_dir / "score.json"
        if score_path.is_file():
            score = _read_json(score_path)
        else:
            score = run_human_messy_homepage(
                prompt=prompt,
                workspace=run_dir / "workspace",
                receipt_path=run_dir / "receipt.json",
                score_path=score_path,
                transcript_path=run_dir / "transcript.txt",
                diff_path=run_dir / "workspace.diff",
                model_id=args.model_id,
                mode="product",
                ollama_api=args.ollama_api,
            )
        (run_dir / "generation-result.json").write_text(
            json.dumps({"score_status": score.get("status"), "preview": score.get("selected_preview_path")}, indent=2) + "\n",
            encoding="utf-8",
        )
        _write_route_trace(run_dir, prompt, prompt_row, score)
        receipt_rows.append(
            {
                "run": run_name,
                "prompt": prompt,
                "run_dir": _rel(run_dir),
                "score_status": score.get("status"),
                "selected_preview_path": score.get("selected_preview_path"),
            }
        )

    pre_browser = _path(args.browser_results).with_name(_path(args.browser_results).stem + "-before-repair.json")
    _run_node_probe(run_root, pre_browser)
    _run_repair(run_root, pre_browser, args.model_id, args.ollama_api)
    final_browser = _path(args.browser_results)
    _run_node_probe(run_root, final_browser)

    repair_summary = pre_browser.with_name(pre_browser.stem.replace("-browser-behavior-results-before-repair", "") + "-post-behavior-repair-summary.json")
    if not repair_summary.is_file():
        repair_summary = pre_browser.with_name(pre_browser.stem.replace("-browser-behavior-results", "") + "-post-behavior-repair-summary.json")
    requested_repair_summary = _path(args.repair_summary)
    if repair_summary.is_file() and repair_summary != requested_repair_summary:
        requested_repair_summary.write_text(repair_summary.read_text(encoding="utf-8-sig"), encoding="utf-8")

    results = _compose_results(
        title=args.title,
        prompt_doc=prompt_doc,
        run_root=run_root,
        browser_results=final_browser,
        repair_summary=requested_repair_summary if requested_repair_summary.is_file() else repair_summary,
        old_result_context=_old_context(prompt_doc),
    )
    _write_json(_path(args.results), results)
    _path(args.html).write_text(_render_html(results), encoding="utf-8")
    _write_json(
        _path(args.run_receipt),
        {
            "created_at": _now(),
            "prompt_file": _rel(prompt_path),
            "run_root": _rel(run_root),
            "results": _rel(_path(args.results)),
            "html": _rel(_path(args.html)),
            "browser_behavior_results": _rel(final_browser),
            "repair_summary": _rel(requested_repair_summary),
            "model_id": args.model_id,
            "rows": receipt_rows,
        },
    )
    print(json.dumps({"total": results["total_count"], "pass": results["pass_count"], "overall": results["overall_verdict"]}, indent=2))


def _compose_results(
    *,
    title: str,
    prompt_doc: dict[str, Any],
    run_root: Path,
    browser_results: Path,
    repair_summary: Path,
    old_result_context: dict[str, Any],
) -> dict[str, Any]:
    browser = _read_json(browser_results)
    repairs = {item.get("run"): item for item in (_read_json(repair_summary).get("repairs") if repair_summary.is_file() else []) or []}
    prompt_by_text = {item.get("prompt"): item for item in prompt_doc.get("prompts") or []}
    rows = []
    for item in browser.get("results") or []:
        run = str(item.get("run") or "")
        score = _read_json(run_root / run / "score.json")
        repair = repairs.get(run, {})
        probe = item.get("behavior_probe") or {}
        raw_passed = bool(probe.get("passed")) and str(probe.get("verdict") or "").upper() == "PASS"
        raw_final_verdict = "PASS" if raw_passed else "FAIL"
        prompt_meta = prompt_by_text.get(score.get("prompt")) or {}
        open_status = "PASS" if (item.get("open_probe") or {}).get("opened") else "FAIL"
        score_integrity = classify_artifact_score_integrity(
            prompt=str(score.get("prompt") or ""),
            category=str(prompt_meta.get("baseline_neighbor") or ""),
            route_status=str(score.get("route_status") or ""),
            open_status=open_status,
            behavior_probe=probe,
            raw_final_verdict=raw_final_verdict,
        )
        passed = bool(score_integrity["product_pass"])
        final_verdict = str(score_integrity["strict_final_verdict"])
        repair_failure_bucket = classify_repair_failure_bucket(repair)
        primary_behavior_failure_bucket = str(score_integrity["primary_behavior_failure_bucket"] or "")
        flags = {
            "deterministic_scaffold_used": bool(score.get("deterministic_scaffold_used")),
            "fallback_used": bool(score.get("fallback_used")),
            "backend_created_content": bool(score.get("backend_created_content")),
            "real_app_touched": bool(score.get("real_app_touched")),
            "cloud_api_fallback_used": False,
            "repair_attempts_used": int(repair.get("attempts_used") or 0),
            "behavior_failed_marked_pass": (not passed) and raw_passed,
            "score_integrity_failure": bool(score_integrity["score_integrity_failure"]),
            "report_verdict_mismatch": bool(score_integrity["report_verdict_mismatch"]),
            "missing_transcript": not (run_root / run / "transcript.txt").is_file(),
            "missing_behavior_evidence": not bool(probe),
        }
        links = {
            "preview": _relpath_from(ROOT, Path(str(score.get("selected_preview_path") or "")).resolve()),
            "behavior_probe": _relpath_from(ROOT, run_root / run / "behavior-probe.json"),
            "score": _relpath_from(ROOT, run_root / run / "score.json"),
            "receipt": _relpath_from(ROOT, run_root / run / "receipt.json"),
            "transcript": _relpath_from(ROOT, run_root / run / "transcript.txt"),
            "workspace_diff": _relpath_from(ROOT, run_root / run / "workspace.diff"),
            "behavior_probe_before_repair": _optional_rel(run_root / run / "behavior-probe-before-repair.json"),
            "behavior_failure_packet": _optional_rel(run_root / run / "behavior-failure-packet.json"),
            "post_behavior_repair_result": _optional_rel(run_root / run / "post-behavior-repair-result.json"),
            "route_trace": _optional_rel(run_root / run / "route_trace.json"),
        }
        reason_codes = ["behavior_pass_verified"] if passed else ["behavior_failed_verified", f"behavior_probe_failed:{probe.get('test') or 'probe'}"]
        if primary_behavior_failure_bucket:
            reason_codes.append(primary_behavior_failure_bucket)
        if repair_failure_bucket:
            reason_codes.append(repair_failure_bucket)
        if score_integrity["score_integrity_failure"]:
            reason_codes.append("score_integrity_false_positive_corrected")
        if score_integrity["report_verdict_mismatch"]:
            reason_codes.append("report_verdict_mismatch_corrected")
        if int(repair.get("attempts_used") or 0) == 1:
            reason_codes.append("post_behavior_repair_pass" if passed else "post_behavior_repair_failed")
            reason_codes.append("repair_attempts_1")
        rows.append(
            {
                "run": run,
                "prompt": score.get("prompt"),
                "baseline_neighbor": prompt_meta.get("baseline_neighbor", ""),
                "expected_behavior": prompt_meta.get("expected_behavior", ""),
                "route_status": score.get("route_status"),
                "open_status": open_status,
                "behavior_status": probe.get("verdict"),
                "raw_behavior_pass": raw_passed,
                "raw_final_verdict": raw_final_verdict,
                "strict_human_final_verdict": final_verdict,
                "final_verdict": final_verdict,
                "final_behavior_verdict": final_verdict,
                "post_behavior_final_verdict": final_verdict,
                "behavior_test": probe.get("test"),
                "behavior_expected": probe.get("expected"),
                "behavior_actual": probe.get("actual"),
                "repair_attempts": int(repair.get("attempts_used") or 0),
                "repair_status": repair.get("repair_status") or repair.get("status") or "SKIPPED",
                "repair_eligible": bool(repair.get("eligible")),
                "repair_skip_reason": repair.get("skip_reason") or "",
                "failure_bucket": "" if passed else primary_behavior_failure_bucket or repair_failure_bucket or _failure_bucket(repair, probe),
                "primary_behavior_failure_bucket": primary_behavior_failure_bucket,
                "secondary_behavior_failure_bucket": str(score_integrity["secondary_behavior_failure_bucket"] or ""),
                "repair_failure_bucket": repair_failure_bucket,
                "score_integrity_failure": bool(score_integrity["score_integrity_failure"]),
                "report_verdict_mismatch": bool(score_integrity["report_verdict_mismatch"]),
                "score_integrity_classification": score_integrity["classification"],
                "strict_reason": score_integrity["strict_reason"],
                "anti_cheat_flags": flags,
                "final_reason_codes": reason_codes,
                "post_behavior_reason_codes": reason_codes,
                "selected_preview_path": score.get("selected_preview_path"),
                "preview_link": links["preview"],
                "files_changed": score.get("files_changed") or [],
                "workspace_files": score.get("workspace_files") or [],
                "model_authored_targets": score.get("model_authored_targets") or [],
                "evidence_links": links,
            }
        )
    pass_count = sum(1 for row in rows if row["final_verdict"] == "PASS")
    fail_count = len(rows) - pass_count
    repair_attempts = sum(int(row["repair_attempts"]) for row in rows)
    handoffs = sum(1 for row in rows if row["repair_status"] == "HANDOFF" and int(row["repair_attempts"]) == 0)
    score_integrity_warnings = sum(1 for row in rows if row["score_integrity_failure"] or row["report_verdict_mismatch"])
    false_positive_corrections = sum(1 for row in rows if row["score_integrity_classification"] == "false_positive_pass")
    false_negative_corrections = sum(1 for row in rows if row["score_integrity_classification"] == "false_negative_fail")
    report_verdict_mismatches = sum(1 for row in rows if row["report_verdict_mismatch"])
    return {
        "created_at": _now(),
        "title": title,
        "old_result_context": old_result_context,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "total_count": len(rows),
        "repair_attempt_count": repair_attempts,
        "repair_handoff_without_attempt_count": handoffs,
        "score_integrity_warnings_count": score_integrity_warnings,
        "false_positive_corrections_count": false_positive_corrections,
        "false_negative_corrections_count": false_negative_corrections,
        "report_verdict_mismatch_count": report_verdict_mismatches,
        "overall_verdict": "GREEN_READY_FOR_BRITTON_REVIEW" if pass_count >= 8 else "NO-GO",
        "green_threshold": "8/10 behavior PASS required for this batch",
        "rows": rows,
    }


def _render_html(results: dict[str, Any]) -> str:
    rows = []
    for row in results["rows"]:
        links = " ".join(
            f"<a href='{_esc(target)}'>{_esc(label)}</a>"
            for label, target in (row.get("evidence_links") or {}).items()
            if target
        )
        details = json.dumps(row.get("behavior_actual") or {}, indent=2)
        rows.append(
            "<tr>"
            f"<td>{_esc(row['prompt'])}</td><td>{_esc(row.get('baseline_neighbor',''))}</td>"
            f"<td>{_esc(row.get('route_status'))}</td><td>{_esc(row.get('open_status'))}</td>"
            f"<td>{_esc(row.get('behavior_status'))}</td><td>{_esc(row.get('raw_final_verdict'))}</td><td>{_esc(row.get('strict_human_final_verdict'))}</td>"
            f"<td>{row.get('repair_attempts')}</td><td>{_esc(row.get('repair_status'))}</td>"
            f"<td>{_esc(row.get('primary_behavior_failure_bucket'))}</td><td>{_esc(row.get('repair_failure_bucket'))}</td>"
            f"<td>{_esc(row.get('score_integrity_classification'))}</td><td><code>{_esc(json.dumps(row.get('anti_cheat_flags'), sort_keys=True))}</code></td>"
            f"<td>{links}<details><summary>actual before/after</summary><pre>{_esc(details)}</pre></details></td>"
            "</tr>"
        )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>"
        + _esc(results["title"])
        + "</title><style>body{font-family:Segoe UI,Arial,sans-serif;margin:24px;background:#f8fafc;color:#111827}"
        "table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #d1d5db;padding:7px;vertical-align:top}"
        "code,pre{white-space:pre-wrap;background:#eef2f7;padding:4px;border-radius:4px}a{display:inline-block;margin-right:6px}</style></head><body>"
        f"<h1>{_esc(results['title'])}</h1>"
        f"<p><strong>Overall:</strong> {_esc(results['overall_verdict'])} "
        f"<strong>Behavior PASS:</strong> {results['pass_count']} "
        f"<strong>Behavior FAIL:</strong> {results['fail_count']} "
        f"<strong>Threshold:</strong> {_esc(results['green_threshold'])} "
        f"<strong>Repair attempts:</strong> {results['repair_attempt_count']} "
        f"<strong>Handoffs:</strong> {results['repair_handoff_without_attempt_count']} "
        f"<strong>Score warnings:</strong> {results['score_integrity_warnings_count']} "
        f"<strong>False-positive corrections:</strong> {results['false_positive_corrections_count']} "
        f"<strong>False-negative corrections:</strong> {results['false_negative_corrections_count']}</p>"
        "<table><thead><tr><th>Prompt</th><th>Category</th><th>Route</th><th>Open</th><th>Probe</th><th>Raw final</th><th>Strict final</th><th>Repairs</th><th>Repair status</th><th>Primary behavior bucket</th><th>Repair bucket</th><th>Score integrity</th><th>Anti-cheat flags</th><th>Evidence</th></tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table></body></html>"
    )


def _run_node_probe(run_root: Path, output_path: Path) -> None:
    subprocess.run(
        ["node", str(ROOT / "anti_tailoring_behavior_probe.mjs"), str(run_root), output_path.name],
        cwd=ROOT,
        check=True,
    )


def _run_repair(run_root: Path, browser_results: Path, model_id: str, ollama_api: str) -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "anti_tailoring_post_behavior_repair.py"),
            "--run-root",
            str(run_root),
            "--browser-results",
            str(browser_results),
            "--model-id",
            model_id,
            "--ollama-api",
            ollama_api,
        ],
        cwd=ROOT.parent.parent.parent,
        check=True,
    )


def _failure_bucket(repair: dict[str, Any], probe: dict[str, Any]) -> str:
    if repair.get("skip_reason"):
        return str(repair["skip_reason"])
    if repair.get("repair_status") == "HANDOFF" or repair.get("status") == "HANDOFF":
        return str((repair.get("reason_codes") or ["handoff"])[0])
    return str(probe.get("reason") or probe.get("expected") or "behavior_failed")


def _path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path).resolve()


def _rel(path: Path) -> str:
    return _relpath_from(Path.cwd(), path)


def _optional_rel(path: Path) -> str:
    return _relpath_from(ROOT, path) if path.is_file() else ""


def _relpath_from(base: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_route_trace(run_dir: Path, prompt: str, prompt_row: dict[str, Any], score: dict[str, Any]) -> None:
    receipt = _read_json(run_dir / "receipt.json") if (run_dir / "receipt.json").is_file() else {}
    diagnostics = receipt.get("diagnostics_packet") if isinstance(receipt.get("diagnostics_packet"), dict) else {}
    behavior_contract = score.get("behavior_contract") if isinstance(score.get("behavior_contract"), dict) else {}
    if not behavior_contract:
        behavior_contract = diagnostics.get("behavior_contract") if isinstance(diagnostics.get("behavior_contract"), dict) else {}
    probe_targets = behavior_contract.get("probe_targets") if isinstance(behavior_contract.get("probe_targets"), list) else []
    first_probe = probe_targets[0] if probe_targets and isinstance(probe_targets[0], dict) else {}
    normalized = _normalize_prompt(prompt)
    family_candidates, family_match_reasons = _family_candidates(normalized, prompt_row, first_probe)
    standalone_signals = _standalone_artifact_signals(normalized)
    real_repo_signals = _real_repo_signals(normalized)
    selected_preview_path = str(score.get("selected_preview_path") or "")
    trace = {
        "original_prompt": prompt,
        "normalized_prompt": normalized,
        "family_candidates": family_candidates,
        "family_match_reasons": family_match_reasons,
        "standalone_artifact_signals": standalone_signals,
        "real_repo_signals": real_repo_signals,
        "explicit_target_path_detected": bool(re.search(r"\b[\w./@()\\-]+\.(?:tsx?|jsx?|py|css|html|json|md|xml|ya?ml|toml)\b", prompt)),
        "selected_artifact_family": str(prompt_row.get("family") or prompt_row.get("baseline_neighbor") or ""),
        "behavior_contract_probe_id": str(first_probe.get("probe_id") or ""),
        "normalized_intent_before_route": str(diagnostics.get("task_shape") or score.get("task_shape") or ""),
        "normalized_intent_after_route": str(score.get("task_shape") or diagnostics.get("task_shape") or ""),
        "route_decision": str(score.get("route_status") or score.get("status") or ""),
        "route_decision_reason": _route_decision_reason(score, diagnostics, standalone_signals, real_repo_signals),
        "disposable_candidate_true_false": str(score.get("task_shape") or diagnostics.get("task_shape") or "") == "disposable_small_file_bundle",
        "blocking_reason_if_any": "; ".join(str(item) for item in (score.get("blocked_reasons") or diagnostics.get("blocked_reasons") or [])),
        "selected_preview_path": selected_preview_path,
        "why_no_preview_if_blocked": "" if selected_preview_path else _why_no_preview_if_blocked(score),
    }
    _write_json(run_dir / "route_trace.json", trace)


def _normalize_prompt(prompt: str) -> str:
    return re.sub(r"\s+", " ", (prompt or "").strip().lower())


def _family_candidates(normalized: str, prompt_row: dict[str, Any], first_probe: dict[str, Any]) -> tuple[list[str], list[str]]:
    candidates: list[str] = []
    reasons: list[str] = []
    declared = str(prompt_row.get("family") or prompt_row.get("baseline_neighbor") or "")
    if declared:
        candidates.append(declared)
        reasons.append(f"prompt_set_family:{declared}")
    probe_id = str(first_probe.get("probe_id") or "")
    if probe_id:
        reasons.append(f"behavior_contract_probe:{probe_id}")
    checks = [
        ("calculator/splitter", r"\b(costs?|fees?|share|sharer|splits?|splitter|bill|tip|calculator)\b"),
        ("theme/mode toggle", r"\b(theme|palette|dusk|dawn|sunrise|sunset|dark|light|switch|toggle|mode|flipper)\b"),
        ("weather/forecast/tile", r"\b(weather|forecast|temperature|condition|balcony|porch|tile)\b"),
        ("password/passphrase strength", r"\b(password|passphrase|phrase|strength|strong|gauge|meter|safety)\b"),
        ("drawing/canvas/sketch", r"\b(drawing|draw|doodle|sketch|canvas|paint)\b"),
    ]
    for family, pattern in checks:
        if re.search(pattern, normalized):
            if family not in candidates:
                candidates.append(family)
            reasons.append(f"keyword_family:{family}")
    return candidates, reasons


def _standalone_artifact_signals(normalized: str) -> list[str]:
    signals: list[str] = []
    if re.search(r"\b(init|initialize|make|create|build|new|scaffold|start|draft)\b|\bshow me\b", normalized):
        signals.append("creation_or_show_me_verb")
    if re.search(r"\b(app|tool|widget|card|meter|gauge|pad|board|switch|toggle|flipper|calculator|splitter|sharer|forecast|tile)\b", normalized):
        signals.append("small_tool_widget_or_interactive_noun")
    if re.search(r"\b(costs?|fees?|share|sharer|splits?|palette|dusk|dawn|phrase|passphrase|strength|paint|doodle|forecast)\b", normalized):
        signals.append("interactive_family_signal")
    return signals


def _real_repo_signals(normalized: str) -> list[str]:
    signals: list[str] = []
    for label, pattern in [
        ("existing_or_current", r"\b(existing|current app|real app)\b"),
        ("production", r"\bproduction\b"),
        ("repo_or_src", r"\b(repo|src|source tree)\b|src[\\/]"),
        ("component_or_route", r"\b(component|route)\b"),
        ("modify_fix_update", r"\b(edit|modify|fix|update|repair|refactor|integrate)\b"),
        ("test_file", r"\btest file\b"),
    ]:
        if re.search(pattern, normalized):
            signals.append(label)
    return signals


def _route_decision_reason(score: dict[str, Any], diagnostics: dict[str, Any], standalone: list[str], real_repo: list[str]) -> str:
    task_shape_source = str(score.get("task_shape_source") or diagnostics.get("task_shape_source") or "")
    if str(score.get("route_status") or score.get("status") or "").upper() == "EXPECTED-BLOCKED":
        return "blocked_by_route_or_target_scope"
    if task_shape_source:
        return task_shape_source
    if real_repo:
        return "real_repo_signals_present"
    if standalone:
        return "standalone_artifact_signals_present"
    return "not_recorded"


def _why_no_preview_if_blocked(score: dict[str, Any]) -> str:
    reason_codes = score.get("preview_resolution_reason_codes") or []
    blocked = score.get("blocked_reasons") or []
    if reason_codes or blocked:
        return "; ".join(str(item) for item in [*reason_codes, *blocked] if item)
    if str(score.get("route_status") or "").upper() == "EXPECTED-BLOCKED":
        return "route blocked before preview selection"
    return "not_recorded"


def _old_context(prompt_doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_status": prompt_doc.get("status", ""),
        "source_title": prompt_doc.get("title", ""),
    }


def _slug(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:80] or "prompt"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _esc(value: Any) -> str:
    return (
        str(value if value is not None else "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


if __name__ == "__main__":
    main()
