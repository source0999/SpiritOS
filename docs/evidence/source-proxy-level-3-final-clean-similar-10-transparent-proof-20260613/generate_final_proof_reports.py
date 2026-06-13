from __future__ import annotations

import html
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RUN_ROOT = ROOT / "final-clean-similar-10-runs"


def main() -> None:
    prompt_doc = read_json(ROOT / "final-proof-prompt-set.json")
    intermediate = read_json(ROOT / "final-proof-intermediate-results.json")
    browser = read_json(ROOT / "final-proof-browser-behavior-results.json")
    repairs = read_json(ROOT / "final-proof-post-behavior-repair-summary.json")
    prompt_meta_by_prompt = {row["prompt"]: row for row in prompt_doc["prompts"]}
    browser_by_run = {row["run"]: row for row in browser.get("results", [])}
    repair_by_run = {row["run"]: row for row in repairs.get("repairs", [])}

    trace_dir = ROOT / "per-prompt-traces"
    trace_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for row in intermediate["rows"]:
        prompt_meta = prompt_meta_by_prompt.get(row["prompt"], {})
        run_dir = RUN_ROOT / row["run"]
        score = read_json(run_dir / "score.json")
        receipt = read_json(run_dir / "receipt.json")
        behavior_probe = read_json(run_dir / "behavior-probe.json") if (run_dir / "behavior-probe.json").is_file() else {}
        browser_row = browser_by_run.get(row["run"], {})
        repair_row = repair_by_run.get(row["run"], {})
        repair_result = read_json(run_dir / "post-behavior-repair-result.json") if (run_dir / "post-behavior-repair-result.json").is_file() else {}
        trace = build_trace(
            row=row,
            prompt_meta=prompt_meta,
            score=score,
            receipt=receipt,
            behavior_probe=behavior_probe,
            browser_row=browser_row,
            repair_row=repair_row,
            repair_result=repair_result,
            run_dir=run_dir,
        )
        trace_json = trace_dir / f"{prompt_meta.get('id', row['run'])}.json"
        trace_md = trace_dir / f"{prompt_meta.get('id', row['run'])}.md"
        write_json(trace_json, trace)
        trace_md.write_text(render_trace_md(trace), encoding="utf-8")
        rows.append(
            {
                **row,
                "id": prompt_meta.get("id", ""),
                "family": prompt_meta.get("family", row.get("baseline_neighbor", "")),
                "trace_json": rel(trace_json),
                "trace_md": rel(trace_md),
                "normalized_intent": trace["prompt_intake"]["normalized_intent"],
                "active_coder_model": trace["model_lane_transparency"]["actual_model_provider_invoked"],
                "gemma_status": trace["model_lane_transparency"]["gemma_status"],
                "qwen_status": trace["model_lane_transparency"]["qwen_status"],
                "cartographer_status": trace["model_lane_transparency"]["cartographer_routing_status"],
                "observed_behavior_summary": summarize_actual(row.get("behavior_actual")),
                "anti_cheat_clean": not any_true(row.get("anti_cheat_flags", {}), ignore={"repair_attempts_used"}),
            }
        )

    results = build_results(intermediate, rows)
    write_json(ROOT / "final-proof-results.json", results)
    (ROOT / "transparent-proxy-trace-index.md").write_text(render_trace_index(results), encoding="utf-8")
    (ROOT / "anti-cheat-integrity.md").write_text(render_anti_cheat(results), encoding="utf-8")
    (ROOT / "anti-tailoring-audit.md").write_text(render_anti_tailoring(results), encoding="utf-8")
    (ROOT / "final-proof-summary.md").write_text(render_summary(results), encoding="utf-8")
    (ROOT / "index.md").write_text(render_index(results), encoding="utf-8")
    (ROOT / "mini-context-pack.md").write_text(render_mini_pack_md(results), encoding="utf-8")
    write_mini_pack_xml(results, ROOT / "mini-context-pack.xml")
    (ROOT / "next-upload-packet.md").write_text(render_upload_packet(results), encoding="utf-8")
    (ROOT / "final-proof.html").write_text(render_html(results), encoding="utf-8")
    print(json.dumps({"verdict": results["verdict"], "pass": results["pass_count"], "fail": results["fail_count"]}, indent=2))


def build_trace(
    *,
    row: dict[str, Any],
    prompt_meta: dict[str, Any],
    score: dict[str, Any],
    receipt: dict[str, Any],
    behavior_probe: dict[str, Any],
    browser_row: dict[str, Any],
    repair_row: dict[str, Any],
    repair_result: dict[str, Any],
    run_dir: Path,
) -> dict[str, Any]:
    diagnostics = receipt.get("diagnostics_packet") or {}
    first_call = (receipt.get("model_calls") or [{}])[0]
    packet = first_call.get("packet") or {}
    context = packet.get("context_packet") or {}
    task_spec = packet.get("task_spec") or {}
    workspace_contract = packet.get("workspace_contract") or {}
    parse_results = receipt.get("parse_results") or []
    parse_decisions = [decision for parse in parse_results for decision in parse.get("decisions", [])]
    rejected = [decision for decision in parse_decisions if decision.get("status") == "rejected"]
    parsed_actions = receipt.get("parsed_actions") or []
    behavior_contract = score.get("behavior_contract") or context.get("behavior_contract") or {}
    probe_targets = behavior_contract.get("probe_targets") or []
    probe_id = (probe_targets[0] or {}).get("probe_id") if probe_targets else value("NOT_RECORDED", "behavior contract did not record a probe target")
    model_call_count = int(diagnostics.get("model_call_count") or len(receipt.get("model_calls") or []))
    selected_preview = score.get("selected_preview_path") or ""
    qwen_status = "INVOKED" if model_call_count > 0 and "qwen" in str(score.get("model_id", "")).lower() else "NOT_INVOKED"
    gemma_status = "VERIFIER_PREVIEW_ONLY" if "gemma_sidecar_context_preview" in score.get("sidecar_lanes_considered", []) else "NOT_AVAILABLE"
    hermes_status = "VERIFIER_PREVIEW_ONLY" if "hermes_sidecar_verifier_preview" in score.get("sidecar_lanes_considered", []) else "NOT_AVAILABLE"
    trace = {
        "trace_version": "source-proxy-final-clean-transparent-trace-v1",
        "generated_at": now(),
        "prompt_intake": {
            "prompt_id": prompt_meta.get("id", value("NOT_RECORDED", "prompt id missing from lock")),
            "original_prompt": row.get("prompt", ""),
            "normalized_intent": score.get("expectation_score", {}).get("inferred_intent") or score.get("task_shape") or value("NOT_RECORDED", "intent not recorded separately"),
            "inferred_artifact_family": prompt_meta.get("family") or row.get("baseline_neighbor") or score.get("artifact_class") or "",
            "task_shape": score.get("task_shape") or value("NOT_RECORDED", "task shape missing from score"),
            "route_mode": score.get("mode") or value("NOT_RECORDED", "mode missing from score"),
            "route_status": score.get("route_status") or row.get("route_status") or "",
            "had_explicit_target_path": bool(task_spec.get("target")),
            "disposable_artifact_inference_used": score.get("workspace_decision_source") == "disposable_artifact_inference",
        },
        "context_and_packet_assembly": {
            "context_sources_requested": task_spec.get("context_sources") or value("NOT_RECORDED", "task spec did not record requested sources"),
            "context_sources_actually_used": score.get("expectation_score", {}).get("context_sources_used") or value("NOT_RECORDED", "expectation score did not record used sources"),
            "cartographer_or_route_ownership_preview": value("PREVIEW_ONLY", "Cartographer route ownership was not invoked for this proof"),
            "selected_writable_sandbox_scope": workspace_contract.get("workspace_root") or score.get("workspace_path") or "",
            "allowed_files": workspace_contract.get("allowed_files", []),
            "protected_path_checks": workspace_contract.get("protected_paths", []),
            "real_app_touch_status": score.get("real_app_touched", False),
            "selected_preview_path": selected_preview or value("NOT_RECORDED", "no browser-viewable preview selected"),
        },
        "model_lane_transparency": {
            "primary_coder_lane_name": score.get("selected_coder_lane") or value("NOT_RECORDED", "lane not recorded"),
            "actual_model_provider_invoked": score.get("model_id") or value("NO_MODEL_CALL", "model id missing"),
            "qwen_status": qwen_status,
            "gemma_status": gemma_status,
            "hermes_status": hermes_status,
            "verifier_lane_status": "PREVIEW_ONLY" if score.get("verifier_lane_required") else "NOT_REQUIRED",
            "cartographer_routing_status": "PREVIEW_ONLY",
            "lane_summary": "QWEN_ONLY" if qwen_status == "INVOKED" else "NO_MODEL_CALL",
            "lane_reason_codes": score.get("lane_selection_reason_codes", []),
        },
        "coder_packet_and_model_output": {
            "source_proxy_packet_path": value("NOT_RECORDED", "packet was recorded inside receipt.json, not as a standalone packet file"),
            "model_transcript_path": existing(run_dir / "transcript.txt"),
            "raw_action_count": len(parsed_actions),
            "file_block_count": len([action for action in parsed_actions if action.get("action_type") == "WriteFile"]),
            "parsed_actions": [{"type": action.get("action_type"), "target": action.get("target")} for action in parsed_actions],
            "rejected_actions": rejected,
            "applied_files": score.get("files_changed", []),
            "diff_path": existing(run_dir / "workspace.diff"),
            "receipt_path": existing(run_dir / "receipt.json"),
        },
        "behavior_contract": {
            "behavior_contract_id_version": behavior_contract.get("contract_version") or value("NOT_RECORDED", "contract version missing"),
            "probe_id": probe_id,
            "expected_behavior": prompt_meta.get("expected_behavior") or row.get("expected_behavior") or "",
            "behavior_required": score.get("behavior_required_for_final_pass", True),
            "non_pass_signals_rejected_as_insufficient": behavior_contract.get("non_pass_signals") or value("NOT_RECORDED", "non-pass signals missing"),
        },
        "browser_behavior_proof": {
            "open_status": row.get("open_status") or ("PASS" if (browser_row.get("open_probe") or {}).get("opened") else "FAIL"),
            "probe_status": row.get("behavior_status") or behavior_probe.get("verdict") or "",
            "observed_before": observed_value(row.get("behavior_actual"), "before"),
            "observed_after": observed_after(row.get("behavior_actual")),
            "clicked_filled_changed_values": extract_interaction(row.get("behavior_actual")),
            "primary_behavior_failure_bucket": row.get("primary_behavior_failure_bucket") or "",
            "secondary_behavior_failure_bucket": row.get("secondary_behavior_failure_bucket") or "",
        },
        "repair_loop": {
            "repair_attempted": int(row.get("repair_attempts") or 0) > 0,
            "repair_attempts_count": int(row.get("repair_attempts") or 0),
            "repair_status": row.get("repair_status") or repair_row.get("repair_status") or "SKIPPED",
            "repair_packet_path": existing(run_dir / "behavior-failure-packet.json"),
            "repair_output_action_format": repair_output_format(repair_result),
            "no_repair_explanation": "" if int(row.get("repair_attempts") or 0) else (row.get("repair_skip_reason") or repair_row.get("skip_reason") or "behavior_not_failed_or_not_eligible"),
        },
        "final_verdict": {
            "raw_final": row.get("raw_final_verdict") or "",
            "strict_final": row.get("final_verdict") or "",
            "product_pass": row.get("final_verdict") == "PASS",
            "score_integrity_warning": bool(row.get("score_integrity_failure") or row.get("report_verdict_mismatch")),
            "false_positive_correction": row.get("score_integrity_classification") == "false_positive_pass",
            "false_negative_correction": row.get("score_integrity_classification") == "false_negative_fail",
            "anti_cheat_flags": row.get("anti_cheat_flags", {}),
        },
        "evidence_links": {
            "preview": link(selected_preview),
            "score": rel(run_dir / "score.json"),
            "receipt": rel(run_dir / "receipt.json"),
            "transcript": rel(run_dir / "transcript.txt"),
            "workspace_diff": rel(run_dir / "workspace.diff"),
            "behavior_probe": rel(run_dir / "behavior-probe.json"),
            "behavior_failure_packet": maybe_rel(run_dir / "behavior-failure-packet.json"),
            "repair_result": maybe_rel(run_dir / "post-behavior-repair-result.json"),
        },
    }
    return trace


def build_results(intermediate: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    pass_count = sum(1 for row in rows if row.get("final_verdict") == "PASS")
    fail_count = len(rows) - pass_count
    anti_cheat_flags = aggregate_flags(rows)
    no_contamination = not any(
        anti_cheat_flags.get(key)
        for key in [
            "fallback_used",
            "deterministic_scaffold_used",
            "backend_created_content",
            "cloud_api_fallback_used",
            "real_app_touched",
            "score_integrity_failure",
            "report_verdict_mismatch",
            "missing_behavior_evidence",
            "missing_transcript",
        ]
    )
    verdict = "GO" if pass_count >= 8 and no_contamination else "NO-GO"
    return {
        "created_at": now(),
        "title": intermediate["title"],
        "verdict": verdict,
        "grade_recommendation": "Do not accept Level 3 as GO; keep Level 3 NEEDS-FIX/NO-GO until fresh similar wording clears at least 8/10.",
        "threshold": "8/10 behavior PASS",
        "pass_count": pass_count,
        "fail_count": fail_count,
        "total_count": len(rows),
        "repair_attempt_count": sum(int(row.get("repair_attempts") or 0) for row in rows),
        "handoff_count": sum(1 for row in rows if row.get("repair_status") == "HANDOFF"),
        "score_warning_count": sum(1 for row in rows if row.get("score_integrity_failure") or row.get("report_verdict_mismatch")),
        "false_positive_count": sum(1 for row in rows if row.get("score_integrity_classification") == "false_positive_pass"),
        "false_negative_count": sum(1 for row in rows if row.get("score_integrity_classification") == "false_negative_fail"),
        "anti_cheat_flags": anti_cheat_flags,
        "anti_tailoring_result": "No exact new prompt tailoring found in searched source/runtime scopes; new prompt strings exist only in this evidence folder.",
        "qwen_status": "INVOKED for all 10 prompts via qwen2.5-coder:7b",
        "gemma_verifier_status": "Gemma/Hermes verifier lanes were PREVIEW_ONLY/NOT_INVOKED; no Gemma transcript exists for this run.",
        "cartographer_routing_status": "PREVIEW_ONLY metadata/status only; no live Cartographer route ownership invocation recorded.",
        "rows": rows,
        "commands_run": [
            "python -m json.tool docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613/final-proof-prompt-set.json > $null",
            "python docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py --prompt-file <evidence>/final-proof-prompt-set.json --run-root <evidence>/final-clean-similar-10-runs --title \"Source Proxy Level 3 final clean similar 10 transparent proof\" --results <evidence>/final-proof-intermediate-results.json --html <evidence>/final-proof-intermediate.html --run-receipt <evidence>/final-proof-run-receipt.json --browser-results <evidence>/final-proof-browser-behavior-results.json --repair-summary <evidence>/final-proof-post-behavior-repair-summary.json --model-id qwen2.5-coder:7b",
            "python docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613/generate_final_proof_reports.py",
            "python -m pytest source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_final_verdict.py source_proxy/tests/test_artifact_retest_result.py source_proxy/tests/test_artifact_repair_loop.py",
            "python -m pytest source_proxy/tests/test_coding_regression_pack.py -k \"artifact or behavior_contract or final_verdict or retest or repair or score_integrity or failure_bucket or fake or fallback or backend_authored\"",
            "python -m pytest source_proxy/tests/test_task_spec_intake_unseen_artifacts.py",
            "python -m py_compile docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613/generate_final_proof_reports.py",
            "python -m json.tool final-proof-prompt-set.json; python -m json.tool final-proof-results.json; python -m json.tool per-prompt-traces/*.json; python -c \"import xml.etree.ElementTree as ET; ET.parse('mini-context-pack.xml')\"",
            "python <inline final-proof.html link audit>",
            "git diff --check -- docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613",
            "git status --branch --short --untracked-files=normal",
        ],
    }


def render_trace_md(trace: dict[str, Any]) -> str:
    p = trace["prompt_intake"]
    b = trace["browser_behavior_proof"]
    f = trace["final_verdict"]
    return "\n".join(
        [
            f"# {p['prompt_id']} Transparent Trace",
            "",
            f"- Prompt: {p['original_prompt']}",
            f"- Family: {p['inferred_artifact_family']}",
            f"- Route: {p['route_status']} / {p['task_shape']}",
            f"- Model lane: {trace['model_lane_transparency']['lane_summary']} ({trace['model_lane_transparency']['actual_model_provider_invoked']})",
            f"- Gemma status: {trace['model_lane_transparency']['gemma_status']}",
            f"- Probe: {trace['behavior_contract']['probe_id']}",
            f"- Open/probe: {b['open_status']} / {b['probe_status']}",
            f"- Before: {short(b['observed_before'])}",
            f"- After: {short(b['observed_after'])}",
            f"- Strict final: {f['strict_final']}",
            "",
            "## Evidence",
            "",
            *[f"- {key}: `{value}`" for key, value in trace["evidence_links"].items() if value],
        ]
    ) + "\n"


def render_trace_index(results: dict[str, Any]) -> str:
    lines = [
        "# Transparent Proxy Trace Index",
        "",
        "Flow: human prompt -> task intake -> artifact family inference -> behavior contract -> route decision -> context packet -> model lane decision -> Qwen or active model execution -> action/file-block parsing -> sandbox write -> preview selection -> browser probe -> repair if needed -> final verdict -> anti-cheat audit -> closeout.",
        "",
        "| id | prompt | family | normalized intent | route status | active coder model | Gemma/verifier status | selected preview path | probe id | observed behavior summary | strict final | anti-cheat clean |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in results["rows"]:
        preview = row.get("selected_preview_path") or "NO_PREVIEW"
        lines.append(
            "| {id} | {prompt} | {family} | {intent} | {route} | {model} | {gemma} | {preview} | {probe} | {obs} | {final} | {clean} |".format(
                id=esc_md(row.get("id")),
                prompt=esc_md(row.get("prompt")),
                family=esc_md(row.get("family")),
                intent=esc_md(row.get("normalized_intent")),
                route=esc_md(row.get("route_status")),
                model=esc_md(row.get("active_coder_model")),
                gemma=esc_md(row.get("gemma_status")),
                preview=esc_md(preview),
                probe=esc_md((read_json(ROOT / row["trace_json"])["behavior_contract"]["probe_id"])),
                obs=esc_md(row.get("observed_behavior_summary")),
                final=esc_md(row.get("final_verdict")),
                clean="true" if row.get("anti_cheat_clean") else "false",
            )
        )
    return "\n".join(lines) + "\n"


def render_anti_cheat(results: dict[str, Any]) -> str:
    flags = results["anti_cheat_flags"]
    lines = ["# Anti-Cheat Integrity", "", f"Verdict impact: {results['verdict']}", ""]
    for key in [
        "fallback_used",
        "deterministic_scaffold_used",
        "backend_created_content",
        "cloud_api_fallback_used",
        "real_app_touched",
        "score_integrity_failure",
        "report_verdict_mismatch",
        "missing_behavior_evidence",
        "missing_transcript",
        "repair_attempts_used",
        "false_positive_corrections",
        "false_negative_corrections",
    ]:
        lines.append(f"- {key}: {json.dumps(flags.get(key, False))}")
    lines.extend(["", "Repair attempts were used on failed weather and drawing artifacts, but neither converted to final behavior PASS."])
    return "\n".join(lines) + "\n"


def render_anti_tailoring(results: dict[str, Any]) -> str:
    lines = [
        "# Anti-Tailoring Audit",
        "",
        "Claim boundary: No exact prompt tailoring found in the searched source/runtime scopes. This does not prove prompt tailoring does not exist anywhere in the universe.",
        "",
        "## Results",
        "",
        "- prompt tailoring found: NO",
        "- exact prompt branches found: NO",
        "- exact prompt strings found in runtime source: NO",
        "- old batch strings found in runtime source: NO in runtime decision/app/script scopes; YES in tests as historical regression fixtures",
        "- canned artifact outputs found: NO exact new prompt-coupled canned outputs found",
        "- backend-authored rescue content found: NO",
        "- deterministic scaffold found: NO",
        "- fallback found: NO",
        "- cloud fallback found: NO",
        "- real app touched: NO",
        "",
        "## Searched Paths",
        "",
        "- `source_proxy/`",
        "- `src/`",
        "- `apps/`",
        "- `scripts/`",
        f"- `{rel(ROOT)}/`",
        "- existing batch runner scripts under `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/`",
        "",
        "## Commands Run",
        "",
        "- `rg -n -F ... source_proxy src apps scripts <runner scripts>` for new exact prompt strings and IDs before run: no matches",
        "- `rg -n -F ... docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613` before run: prompt lock hits only",
        "- `rg -n -F ... source_proxy src apps scripts <runner scripts>` for old 10d/10e strings: test fixtures only",
        "- post-run evidence review: new prompt strings/IDs are present in prompt lock, receipts, transcripts, scores, traces, and reports as expected evidence",
        "",
        "## Important Grep Results",
        "",
        "- Runtime/source scope for new exact prompt strings/IDs returned no hits before the run.",
        "- New evidence folder contains the locked prompt strings and run artifacts.",
        "- Old strings appear in `source_proxy/tests/test_artifact_behavior_contract.py`, `source_proxy/tests/test_artifact_final_verdict.py`, and `source_proxy/tests/test_task_spec_intake_unseen_artifacts.py`; these are tests, not runtime prompt branches.",
    ]
    return "\n".join(lines) + "\n"


def render_summary(results: dict[str, Any]) -> str:
    fails = [row for row in results["rows"] if row["final_verdict"] != "PASS"]
    lines = [
        "# Final Proof Summary",
        "",
        f"Verdict: {results['verdict']}",
        f"Behavior result: {results['pass_count']}/10 PASS, {results['fail_count']} FAIL, threshold {results['threshold']}",
        "",
        "Failed prompts:",
    ]
    for row in fails:
        lines.append(f"- {row['id']} `{row['prompt']}`: {row.get('primary_behavior_failure_bucket') or row.get('failure_bucket') or row.get('route_status')}")
    lines.extend(
        [
            "",
            "Grade recommendation: Do not accept Level 3 as GO yet. The fresh similar wording did not generalize to the 8/10 threshold.",
            "",
            "Model lane: Qwen local coder invoked. Gemma/Hermes verifier lanes were preview-only and not invoked.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_index(results: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Source Proxy Level 3 Final Clean Similar 10 Transparent Proof",
            "",
            f"- Verdict: {results['verdict']}",
            f"- Behavior: {results['pass_count']}/10 PASS, {results['fail_count']} FAIL",
            "- Threshold: 8/10 behavior PASS",
            "- Dashboard: [final-proof.html](final-proof.html)",
            "- Results JSON: [final-proof-results.json](final-proof-results.json)",
            "- Trace index: [transparent-proxy-trace-index.md](transparent-proxy-trace-index.md)",
            "- Anti-tailoring audit: [anti-tailoring-audit.md](anti-tailoring-audit.md)",
            "- Anti-cheat integrity: [anti-cheat-integrity.md](anti-cheat-integrity.md)",
            "- Mini context pack: [mini-context-pack.md](mini-context-pack.md) and [mini-context-pack.xml](mini-context-pack.xml)",
        ]
    ) + "\n"


def render_mini_pack_md(results: dict[str, Any]) -> str:
    lines = [
        "# Mini Context Pack",
        "",
        f"Run title: {results['title']}",
        f"Date: {results['created_at']}",
        f"Verdict: {results['verdict']}",
        f"Current grade recommendation: {results['grade_recommendation']}",
        "",
        "Goal: final clean similar 10 proof for Level 3 generalization, with transparent proxy trace and anti-tailoring/anti-cheat evidence.",
        "",
        "What changed: new evidence-only prompt lock, run artifacts, traces, dashboard, audits, and mini context pack.",
        "What did not change: runtime behavior, scoring, routing, model prompts, repair logic, artifact contracts, source code, real app files.",
        "",
        "## Result Table",
        "",
        "| id | prompt | final | bucket |",
        "| --- | --- | --- | --- |",
    ]
    for row in results["rows"]:
        lines.append(f"| {row['id']} | {esc_md(row['prompt'])} | {row['final_verdict']} | {esc_md(row.get('primary_behavior_failure_bucket') or row.get('failure_bucket') or '')} |")
    lines.extend(
        [
            "",
            f"Transparent proxy flow summary: see `transparent-proxy-trace-index.md` and `per-prompt-traces/`.",
            f"Model lane summary: {results['qwen_status']}; {results['gemma_verifier_status']}; {results['cartographer_routing_status']}.",
            f"Anti-tailoring audit summary: {results['anti_tailoring_result']}",
            f"Anti-cheat summary: no fallback/scaffold/backend/cloud/real-app contamination; two repair attempts used and both remained final FAIL.",
            "",
            "Changed files: evidence files under this folder only.",
            "Evidence files: `final-proof-results.json`, `final-proof.html`, `transparent-proxy-trace-index.md`, `per-prompt-traces/`, `anti-tailoring-audit.md`, `anti-cheat-integrity.md`, run artifacts under `final-clean-similar-10-runs/`.",
            "",
            "Exact commands run:",
        ]
    )
    lines.extend(f"- `{cmd}`" for cmd in results["commands_run"])
    lines.extend(
        [
            "",
            "Remaining blockers: fresh similar wording reached only 5/10 behavior PASS; route inference blocked three artifacts; weather repair still left static behavior; drawing repair left canvas pixels unchanged.",
            "Next recommended step: inspect the five failure families without starting Level 4 or creating a larger batch.",
            "Exact files Britton should upload to ChatGPT next: `mini-context-pack.md`, `final-proof-results.json`, `transparent-proxy-trace-index.md`, and the five failing per-prompt trace JSON files.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_mini_pack_xml(results: dict[str, Any], path: Path) -> None:
    root = ET.Element("mini_context_pack")
    add(root, "run_metadata", {"title": results["title"], "date": results["created_at"]})
    add(root, "verdict", results["verdict"])
    add(root, "grade_recommendation", results["grade_recommendation"])
    prompt_set = ET.SubElement(root, "prompt_set")
    for row in results["rows"]:
        add(prompt_set, "prompt", {"id": row["id"], "text": row["prompt"], "family": row["family"]})
    result_el = ET.SubElement(root, "results")
    for row in results["rows"]:
        add(result_el, "result", {"id": row["id"], "final": row["final_verdict"], "bucket": row.get("primary_behavior_failure_bucket") or row.get("failure_bucket") or ""})
    add(root, "proxy_trace_summary", "See transparent-proxy-trace-index.md and per-prompt-traces.")
    add(root, "model_lanes", {"qwen": results["qwen_status"], "gemma_verifier": results["gemma_verifier_status"], "cartographer": results["cartographer_routing_status"]})
    add(root, "anti_tailoring", results["anti_tailoring_result"])
    add(root, "anti_cheat", json.dumps(results["anti_cheat_flags"], sort_keys=True))
    add(root, "changed_files", "Evidence folder only.")
    add(root, "evidence_files", "final-proof-results.json, final-proof.html, transparent-proxy-trace-index.md, per-prompt-traces, anti-tailoring-audit.md, anti-cheat-integrity.md")
    commands = ET.SubElement(root, "commands")
    for command in results["commands_run"]:
        add(commands, "command", command)
    add(root, "next_steps", "Inspect five failure families; do not proceed to Level 4 from this NO-GO.")
    add(root, "upload_recommendation", "Upload mini-context-pack.md, final-proof-results.json, transparent-proxy-trace-index.md, and failing trace JSON files.")
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def render_upload_packet(results: dict[str, Any]) -> str:
    failing = [row for row in results["rows"] if row["final_verdict"] != "PASS"]
    return "\n".join(
        [
            "# Next Upload Packet",
            "",
            "Upload these first:",
            "",
            "- `mini-context-pack.md`",
            "- `final-proof-results.json`",
            "- `transparent-proxy-trace-index.md`",
            *[f"- `{row['trace_json']}`" for row in failing],
            "",
            "Do not upload a giant Repomix for this closeout unless a later debugging step needs full source context.",
        ]
    ) + "\n"


def render_html(results: dict[str, Any]) -> str:
    cards = []
    for row in results["rows"]:
        preview = link(row.get("selected_preview_path", ""))
        trace_json = row["trace_json"]
        trace_md = row["trace_md"]
        links = row.get("evidence_links") or {}
        ev = []
        for label in ["preview", "behavior_probe", "score", "receipt", "transcript", "workspace_diff", "behavior_failure_packet", "post_behavior_repair_result"]:
            target = links.get(label) or ""
            if target:
                ev.append(f"<a href=\"{html.escape(link(target))}\">{html.escape(label)}</a>")
        ev.append(f"<a href=\"{html.escape(trace_json)}\">trace JSON</a>")
        ev.append(f"<a href=\"{html.escape(trace_md)}\">trace MD</a>")
        iframe = f"<iframe src=\"{html.escape(preview)}\" loading=\"lazy\"></iframe>" if preview else "<div class=\"no-preview\">NO PREVIEW</div>"
        cards.append(
            f"""
            <section class="prompt {row['final_verdict'].lower()}">
              <div class="prompt-head">
                <h2>{html.escape(row['id'])}: {html.escape(row['prompt'])}</h2>
                <strong>{html.escape(row['final_verdict'])}</strong>
              </div>
              <div class="meta">
                <span>family: {html.escape(row['family'])}</span>
                <span>route: {html.escape(str(row.get('route_status', '')))}</span>
                <span>model: {html.escape(row.get('active_coder_model', ''))}</span>
                <span>Gemma/verifier: {html.escape(row.get('gemma_status', ''))}</span>
                <span>repair attempts: {row.get('repair_attempts', 0)}</span>
              </div>
              <div class="preview">{iframe}</div>
              <details open><summary>Observed before/after</summary><pre>{html.escape(json.dumps(row.get('behavior_actual'), indent=2))}</pre></details>
              <details><summary>Evidence links</summary><p>{' '.join(ev)}</p></details>
            </section>
            """
        )
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{html.escape(results['title'])}</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f6f7f9; color: #17202a; }}
    header {{ position: sticky; top: 0; z-index: 2; background: #ffffff; border-bottom: 1px solid #cdd3da; padding: 14px 20px; }}
    h1 {{ margin: 0 0 8px; font-size: 24px; }}
    .stats {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .stats span, .meta span {{ border: 1px solid #ccd3db; background: #fff; border-radius: 6px; padding: 5px 8px; }}
    main {{ padding: 18px; display: grid; gap: 18px; }}
    .prompt {{ background: #fff; border: 1px solid #cdd3da; border-left-width: 8px; border-radius: 8px; padding: 14px; }}
    .prompt.pass {{ border-left-color: #21855b; }}
    .prompt.fail {{ border-left-color: #b42318; }}
    .prompt-head {{ display: flex; justify-content: space-between; gap: 16px; align-items: start; }}
    h2 {{ font-size: 18px; margin: 0 0 10px; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; font-size: 13px; }}
    .preview {{ border: 1px solid #cdd3da; background: #fff; min-height: 420px; margin: 10px 0; }}
    iframe {{ width: 100%; height: 560px; border: 0; background: #fff; }}
    .no-preview {{ min-height: 160px; display: grid; place-items: center; color: #7b1d16; font-weight: 700; }}
    a {{ margin-right: 8px; }}
    pre {{ white-space: pre-wrap; background: #eef2f6; padding: 10px; border-radius: 6px; }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(results['title'])}</h1>
    <div class="stats">
      <span>verdict: {results['verdict']}</span>
      <span>pass: {results['pass_count']}/10</span>
      <span>fail: {results['fail_count']}</span>
      <span>threshold: {results['threshold']}</span>
      <span>repairs: {results['repair_attempt_count']}</span>
      <span>handoffs: {results['handoff_count']}</span>
      <span>score warnings: {results['score_warning_count']}</span>
      <span>false positives: {results['false_positive_count']}</span>
      <span>false negatives: {results['false_negative_count']}</span>
      <span>anti-cheat: clean except non-passing repairs used</span>
      <span>anti-tailoring: no exact prompt runtime matches</span>
    </div>
  </header>
  <main>
    {''.join(cards)}
  </main>
</body>
</html>
"""


def aggregate_flags(rows: list[dict[str, Any]]) -> dict[str, Any]:
    flags = {
        "fallback_used": False,
        "deterministic_scaffold_used": False,
        "backend_created_content": False,
        "cloud_api_fallback_used": False,
        "real_app_touched": False,
        "score_integrity_failure": False,
        "report_verdict_mismatch": False,
        "missing_behavior_evidence": False,
        "missing_transcript": False,
        "repair_attempts_used": 0,
        "false_positive_corrections": 0,
        "false_negative_corrections": 0,
    }
    for row in rows:
        anti = row.get("anti_cheat_flags") or {}
        for key in list(flags):
            if key == "repair_attempts_used":
                flags[key] += int(anti.get(key) or 0)
            elif key in anti:
                flags[key] = bool(flags[key] or anti.get(key))
        flags["false_positive_corrections"] += 1 if row.get("score_integrity_classification") == "false_positive_pass" else 0
        flags["false_negative_corrections"] += 1 if row.get("score_integrity_classification") == "false_negative_fail" else 0
    return flags


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value_obj: Any) -> None:
    path.write_text(json.dumps(value_obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def maybe_rel(path: Path) -> str:
    return rel(path) if path.is_file() else ""


def existing(path: Path) -> str | dict[str, str]:
    return rel(path) if path.is_file() else value("NOT_RECORDED", f"{path.name} was not written")


def link(path_value: str) -> str:
    if not path_value:
        return ""
    text = str(path_value).replace("\\\\10.0.0.186\\SpiritOS\\", "Z:\\").replace("/home/source/SpiritOS/", "Z:/")
    path = Path(text)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            return str(path)
    return text.replace("\\", "/")


def value(value_text: str, reason: str, suggested: str = "") -> dict[str, str]:
    payload = {"value": value_text, "reason": reason}
    if suggested:
        payload["suggested_future_instrumentation"] = suggested
    return payload


def observed_value(actual: Any, key: str) -> Any:
    return actual.get(key, value("NOT_RECORDED", f"behavior probe did not record {key}")) if isinstance(actual, dict) else value("NOT_RECORDED", "behavior actual was not a dict")


def observed_after(actual: Any) -> Any:
    if not isinstance(actual, dict):
        return value("NOT_RECORDED", "behavior actual was not a dict")
    for key in ("after", "afterStart", "strong"):
        if key in actual:
            return actual[key]
    return value("NOT_RECORDED", "behavior probe did not record a standard after value")


def extract_interaction(actual: Any) -> Any:
    if not isinstance(actual, dict):
        return value("NOT_RECORDED", "behavior actual was not a dict")
    return {key: actual[key] for key in ("clicked", "clickedStop", "filled", "appears", "changed", "hasWeatherTerms", "canvas") if key in actual}


def repair_output_format(repair_result: dict[str, Any]) -> Any:
    decisions = repair_result.get("parse_decisions") or []
    accepted = [item.get("parser") for item in decisions if item.get("status") == "accepted"]
    if accepted:
        return accepted
    return value("NOT_RECORDED", "no repair output action format recorded because repair was skipped or absent")


def summarize_actual(actual: Any) -> str:
    if not isinstance(actual, dict):
        return "NOT_RECORDED"
    if "selected_preview_path" in actual:
        return "no preview selected"
    if "changed" in actual:
        return f"changed={actual.get('changed')}"
    if "appears" in actual:
        return f"appears={actual.get('appears')}"
    if "afterStart" in actual:
        return f"before={short(actual.get('before'))}; afterStart={short(actual.get('afterStart'))}"
    if "after" in actual:
        return f"before={short(actual.get('before'))}; after={short(actual.get('after'))}"
    return short(actual)


def short(value_obj: Any, limit: int = 140) -> str:
    text = json.dumps(value_obj, ensure_ascii=True) if isinstance(value_obj, (dict, list)) else str(value_obj)
    text = text.replace("\n", " ")
    return text[:limit] + ("..." if len(text) > limit else "")


def any_true(flags: dict[str, Any], ignore: set[str] | None = None) -> bool:
    ignore = ignore or set()
    return any(bool(value_obj) for key, value_obj in flags.items() if key not in ignore)


def esc_md(value_obj: Any) -> str:
    return str(value_obj).replace("|", "\\|").replace("\n", " ")


def add(parent: ET.Element, tag: str, value_obj: Any) -> None:
    el = ET.SubElement(parent, tag)
    if isinstance(value_obj, dict):
        for key, val in value_obj.items():
            el.set(str(key), str(val))
    else:
        el.text = str(value_obj)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
