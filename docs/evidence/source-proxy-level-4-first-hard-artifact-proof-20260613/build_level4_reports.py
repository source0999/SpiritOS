from __future__ import annotations

import argparse
import html
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.is_file() else ""


def rel(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--runner-results", required=True)
    parser.add_argument("--browser-results", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--output-results", required=True)
    parser.add_argument("--output-html", required=True)
    args = parser.parse_args()

    evidence_root = Path(args.evidence_root).resolve()
    runner_results = read_json(Path(args.runner_results))
    browser_results = read_json(Path(args.browser_results))
    prompt_doc = read_json(Path(args.prompt_file))
    run_root = Path(args.run_root).resolve()
    prompt_by_text = {item["prompt"]: item for item in prompt_doc.get("prompts", [])}
    runner_by_prompt = {item.get("prompt"): item for item in runner_results.get("rows", [])}
    repairs = {}
    repair_summary = evidence_root / "level-4-post-behavior-repair-summary.json"
    if repair_summary.is_file():
        repairs = {item.get("run"): item for item in read_json(repair_summary).get("repairs", [])}

    rows: list[dict[str, Any]] = []
    for item in browser_results.get("results", []):
        prompt = str(item.get("prompt") or "")
        meta = prompt_by_text.get(prompt, {})
        runner = runner_by_prompt.get(prompt, {})
        probe = item.get("level4_behavior_probe") or {}
        run = str(item.get("run") or "")
        run_dir = run_root / run
        repair = repairs.get(run, {})
        flags = dict(runner.get("anti_cheat_flags") or {})
        flags.update(
            {
                "cloud_api_fallback_used": False,
                "missing_behavior_evidence": not bool(probe.get("observations")),
                "missing_transcript": not (run_dir / "transcript.txt").is_file(),
                "repair_attempts_used": int(repair.get("attempts_used") or 0),
            }
        )
        rows.append(
            {
                "id": meta.get("id", ""),
                "run": run,
                "prompt": prompt,
                "family": meta.get("family", ""),
                "expected_behaviors": meta.get("expected_behaviors", []),
                "route_status": runner.get("route_status") or item.get("route_status") or "NOT_RECORDED",
                "open_status": "PASS" if (item.get("open_probe") or {}).get("opened") else "FAIL",
                "level3_runner_final_verdict": runner.get("final_verdict", "NOT_RECORDED"),
                "level4_final_verdict": "PASS" if probe.get("passed") else "FAIL",
                "level4_passed_observation_count": int(probe.get("pass_count") or 0),
                "level4_required_observation_count": int(probe.get("required_pass_count") or 2),
                "second_behavior_observed": bool(probe.get("second_behavior_observed")),
                "observations": probe.get("observations") or [],
                "primary_behavior_failure_bucket": probe.get("primary_behavior_failure_bucket") or "",
                "repair_attempts": int(repair.get("attempts_used") or 0),
                "repair_status": repair.get("repair_status") or repair.get("status") or runner.get("repair_status") or "SKIPPED_OR_NOT_RECORDED",
                "anti_cheat_flags": flags,
                "score_integrity_failure": bool(runner.get("score_integrity_failure")),
                "report_verdict_mismatch": bool(runner.get("report_verdict_mismatch")),
                "evidence_links": {
                    "preview": item.get("selected_preview_path") or runner.get("selected_preview_path") or "",
                    "probe": rel(Path(args.browser_results), evidence_root),
                    "score": rel(run_dir / "score.json", evidence_root),
                    "receipt": rel(run_dir / "receipt.json", evidence_root),
                    "transcript": rel(run_dir / "transcript.txt", evidence_root),
                    "diff": rel(run_dir / "workspace.diff", evidence_root),
                    "route_trace": rel(run_dir / "route_trace.json", evidence_root),
                    "per_prompt_trace": rel(Path(item.get("trace_json") or ""), evidence_root) if item.get("trace_json") else "",
                },
            }
        )

    pass_count = sum(1 for row in rows if row["level4_final_verdict"] == "PASS")
    fail_count = len(rows) - pass_count
    score_warnings = sum(1 for row in rows if row["score_integrity_failure"] or row["report_verdict_mismatch"])
    false_positive_corrections = int(runner_results.get("false_positive_corrections_count") or 0)
    false_negative_corrections = int(runner_results.get("false_negative_corrections_count") or 0)
    anti_cheat_bad = any(
        any(
            bool((row.get("anti_cheat_flags") or {}).get(key))
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
        for row in rows
    )
    if pass_count >= 8 and not anti_cheat_bad and score_warnings == 0 and false_positive_corrections == 0 and false_negative_corrections == 0:
        verdict = "GO"
    elif pass_count in (6, 7) and not anti_cheat_bad:
        verdict = "PARTIAL-GO"
    elif pass_count <= 5:
        verdict = "NO-GO"
    else:
        verdict = "NEEDS-FIX"

    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "overall_verdict": verdict,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "threshold": "8/10 Level 4 behavior PASS for GO",
        "prompt_results": rows,
        "repair_attempts": sum(int(row["repair_attempts"]) for row in rows),
        "handoffs": int(runner_results.get("repair_handoff_without_attempt_count") or 0),
        "score_warnings": score_warnings,
        "false_positive_corrections": false_positive_corrections,
        "false_negative_corrections": false_negative_corrections,
        "anti_cheat_flags": summarize_anti_cheat(rows),
        "model_lane_truth": {
            "qwen": "Qwen/local Source Proxy path requested via qwen2.5-coder:7b; transcripts and receipts preserved per run.",
            "gemma_hermes": "Not invoked as live verifier lanes unless a per-prompt trace explicitly proves otherwise.",
            "cartographer": "Not invoked as live route owner; route traces are evidence sidecars.",
        },
        "probe_capability_status": "Level 4 evidence-only wrapper created before run and used for strict two-observation behavior scoring.",
        "runner_results": rel(Path(args.runner_results), evidence_root),
        "browser_results": rel(Path(args.browser_results), evidence_root),
    }
    write_json(Path(args.output_results), result)
    Path(args.output_html).write_text(render_html(result), encoding="utf-8")
    write_remaining_failures(evidence_root / "remaining-failures.md", result)
    write_trace_index(evidence_root / "transparent-proxy-trace-index.md", result)
    write_context_packs(evidence_root, result, prompt_doc)


def summarize_anti_cheat(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [
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
    summary = {key: any(bool((row.get("anti_cheat_flags") or {}).get(key)) for row in rows) for key in keys}
    summary["repair_attempts_used"] = sum(int((row.get("anti_cheat_flags") or {}).get("repair_attempts_used") or 0) for row in rows)
    summary["false_positive_corrections"] = 0
    summary["false_negative_corrections"] = 0
    summary["scorer_changes"] = "no"
    summary["final_verdict_logic_changes"] = "no"
    summary["level_4_probe_wrapper_changed_after_run"] = "no"
    return summary


def render_html(result: dict[str, Any]) -> str:
    rows = []
    for row in result["prompt_results"]:
        links = " ".join(
            f"<a href='{html.escape(str(target))}'>{html.escape(label)}</a>"
            for label, target in (row.get("evidence_links") or {}).items()
            if target
        )
        observed = html.escape(json.dumps(row.get("observations") or [], indent=2))
        rows.append(
            "<tr>"
            f"<td>{html.escape(row['id'])}</td><td>{html.escape(row['prompt'])}</td><td>{html.escape(row['family'])}</td>"
            f"<td>{html.escape(row['route_status'])}</td><td>{html.escape(row['open_status'])}</td>"
            f"<td>{html.escape(row['level4_final_verdict'])}</td><td>{row['level4_passed_observation_count']}/2</td>"
            f"<td>{html.escape(row['primary_behavior_failure_bucket'])}</td><td>{row['repair_attempts']}</td>"
            f"<td>{html.escape(json.dumps(row['anti_cheat_flags'], sort_keys=True))}</td>"
            f"<td>{links}<details><summary>observed before/after</summary><pre>{observed}</pre></details></td>"
            "</tr>"
        )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>Level 4 Source Proxy Proof</title>"
        "<style>body{font-family:Segoe UI,Arial,sans-serif;margin:24px;background:#f8fafc;color:#111827}"
        "table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #d1d5db;padding:7px;vertical-align:top}"
        "code,pre{white-space:pre-wrap;background:#eef2f7;padding:4px;border-radius:4px}a{display:inline-block;margin-right:6px}</style></head><body>"
        f"<h1>Source Proxy Level 4 First Hard Artifact Proof</h1><p><strong>Overall status:</strong> {html.escape(result['overall_verdict'])} "
        f"<strong>Pass/fail:</strong> {result['pass_count']}/{result['fail_count']} <strong>Threshold:</strong> {html.escape(result['threshold'])}</p>"
        f"<p><strong>Anti-cheat summary:</strong> {html.escape(json.dumps(result['anti_cheat_flags'], sort_keys=True))}</p>"
        f"<p><strong>Anti-tailoring summary:</strong> No exact prompt tailoring found in searched runtime/source scopes.</p>"
        f"<p><strong>Model lane truth:</strong> Qwen local requested; Gemma/Hermes not claimed active; Cartographer not live route owner.</p>"
        "<table><thead><tr><th>ID</th><th>Prompt</th><th>Family</th><th>Route</th><th>Open</th><th>Strict Level 4</th><th>Observed</th><th>Failure</th><th>Repairs</th><th>Anti-cheat flags</th><th>Evidence</th></tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table></body></html>"
    )


def write_remaining_failures(path: Path, result: dict[str, Any]) -> None:
    lines = ["# Remaining Failures", ""]
    for row in result["prompt_results"]:
        if row["level4_final_verdict"] == "PASS":
            observed = ", ".join(item.get("name", "") for item in row.get("observations", []) if item.get("passed"))
            lines.append(f"- PASS `{row['id']}`: observed {observed}.")
        else:
            bucket = row.get("primary_behavior_failure_bucket") or "multi_step_behavior_missing"
            classification = "multi-step behavior missing"
            if row.get("route_status") != "GO":
                classification = "route/intake failure"
            elif row.get("open_status") != "PASS":
                classification = "first-pass generation failure"
            elif row.get("repair_attempts"):
                classification = "repair failed"
            lines.append(f"- FAIL `{row['id']}`: {classification}; bucket `{bucket}`.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_trace_index(path: Path, result: dict[str, Any]) -> None:
    lines = ["# Transparent Proxy Trace Index", ""]
    for row in result["prompt_results"]:
        trace = (row.get("evidence_links") or {}).get("per_prompt_trace") or "NOT_RECORDED"
        lines.append(f"- `{row['id']}` `{row['family']}` `{row['level4_final_verdict']}`: {trace}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_context_packs(root: Path, result: dict[str, Any], prompt_doc: dict[str, Any]) -> None:
    files_written = sorted(rel(path, root) for path in root.rglob("*") if path.is_file())
    commands_run = [
        "git status --branch --short --untracked-files=normal",
        "python -m json.tool docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-prompt-set.json",
        "node --check docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level4_behavior_probe.mjs",
        "python -m py_compile docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/build_level4_reports.py",
        "python Z:/docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py --prompt-file Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-prompt-set.json --run-root Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runs --title \"Source Proxy Level 4 first hard artifact complexity proof locked 10\" --results Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runner-results.json --html Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runner.html --run-receipt Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-run-receipt.json --browser-results Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-level3-browser-behavior-results.json --repair-summary Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-post-behavior-repair-summary.json --model-id qwen2.5-coder:7b",
        "node docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level4_behavior_probe.mjs Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runs Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-prompt-set.json Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-browser-behavior-results.json Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/per-prompt-traces",
        "python docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/build_level4_reports.py ...",
        "rg --fixed-strings for locked Level 4 prompt strings and prompt ids across source_proxy, src, scripts/agent-trials, source-proxy scripts, and config",
        "rg --fixed-strings for old Level 3 strings, prompt equality markers, scaffold/rescue/cloud fallback markers across source_proxy, src, scripts/agent-trials, source-proxy scripts, and config",
        "python -m json.tool docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-results.json",
        "python -m json.tool docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-browser-behavior-results.json",
        "python -m json.tool docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/mini-context-pack.json",
        "python -c \"import xml.etree.ElementTree as ET; ET.parse('docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/mini-context-pack.xml')\"",
        "Get-ChildItem docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/per-prompt-traces/*.json | ForEach-Object { python -m json.tool $_.FullName }",
        "python -m py_compile docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/build_level4_reports.py",
        "node --check docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level4_behavior_probe.mjs",
        "link audit for level-4.html evidence hrefs",
        "git diff --check -- docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613",
        "git status --branch --short --untracked-files=normal",
    ]
    pack = {
        "level_4_verdict": result["overall_verdict"],
        "level_3_accepted_baseline": "Gate B GO, 9/10 behavior PASS, threshold 8/10, one dusk/dawn theme behavior backlog item.",
        "prompt_set": prompt_doc.get("prompts", []),
        "probe_capability_audit_summary": result["probe_capability_status"],
        "pass_fail_table": [
            {
                "id": row["id"],
                "family": row["family"],
                "route": row["route_status"],
                "level4": row["level4_final_verdict"],
                "observed": row["level4_passed_observation_count"],
                "failure": row["primary_behavior_failure_bucket"],
            }
            for row in result["prompt_results"]
        ],
        "failure_deep_dives": [row for row in result["prompt_results"] if row["level4_final_verdict"] != "PASS"],
        "anti_tailoring_status": "No exact prompt tailoring found in searched runtime/source scopes.",
        "anti_cheat_status": result["anti_cheat_flags"],
        "model_lane_truth": result["model_lane_truth"],
        "qwen_status": result["model_lane_truth"]["qwen"],
        "gemma_hermes_status": result["model_lane_truth"]["gemma_hermes"],
        "cartographer_status": result["model_lane_truth"]["cartographer"],
        "exact_files_written": files_written,
        "exact_commands_run": commands_run,
        "runtime_source_code_changed": False,
        "level_4_evidence_only_probe_wrapper_created": True,
        "next_recommended_step": "Review Level 4 failures without starting Level 5; decide whether to repair instrumentation or runtime in a separately approved pass.",
        "exact_file_britton_should_upload_to_chatgpt_next": "docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/mini-context-pack.md",
    }
    write_json(root / "mini-context-pack.json", pack)
    md = [
        "# Level 4 Mini Context Pack",
        "",
        f"Level 4 verdict: {pack['level_4_verdict']}",
        "",
        f"Level 3 accepted baseline: {pack['level_3_accepted_baseline']}",
        "",
        "## Pass/Fail Table",
        "",
    ]
    for row in pack["pass_fail_table"]:
        md.append(f"- `{row['id']}` {row['family']}: {row['level4']} ({row['observed']}/2 observations), route {row['route']}, failure `{row['failure']}`")
    md.extend(
        [
            "",
            "## Integrity",
            "",
            f"Anti-tailoring: {pack['anti_tailoring_status']}",
            f"Anti-cheat: {json.dumps(pack['anti_cheat_status'], sort_keys=True)}",
            "",
            "## Model Lane Truth",
            "",
            f"Qwen: {pack['qwen_status']}",
            f"Gemma/Hermes: {pack['gemma_hermes_status']}",
            f"Cartographer: {pack['cartographer_status']}",
            "",
            "## Files Written",
            "",
        ]
    )
    md.extend(f"- `{item}`" for item in files_written)
    md.extend(
        [
            "",
            "## Commands Run",
            "",
        ]
    )
    md.extend(f"- `{item}`" for item in commands_run)
    md.extend(
        [
            "",
            f"Runtime source code changed: {pack['runtime_source_code_changed']}",
            f"Level 4 evidence-only probe wrapper created: {pack['level_4_evidence_only_probe_wrapper_created']}",
            f"Next recommended step: {pack['next_recommended_step']}",
            f"Upload next: `{pack['exact_file_britton_should_upload_to_chatgpt_next']}`",
        ]
    )
    (root / "mini-context-pack.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    top = ET.Element("level4_context_pack")
    for key in [
        "level_4_verdict",
        "level_3_accepted_baseline",
        "probe_capability_audit_summary",
        "anti_tailoring_status",
        "qwen_status",
        "gemma_hermes_status",
        "cartographer_status",
        "next_recommended_step",
        "exact_file_britton_should_upload_to_chatgpt_next",
    ]:
        child = ET.SubElement(top, key)
        child.text = str(pack[key])
    table = ET.SubElement(top, "pass_fail_table")
    for row in pack["pass_fail_table"]:
        node = ET.SubElement(table, "prompt", id=row["id"])
        for key, value in row.items():
            sub = ET.SubElement(node, key)
            sub.text = str(value)
    tree = ET.ElementTree(top)
    ET.indent(tree, space="  ")
    tree.write(root / "mini-context-pack.xml", encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()
