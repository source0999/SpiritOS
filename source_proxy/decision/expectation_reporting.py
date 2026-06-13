from __future__ import annotations

import html
import json
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from source_proxy.decision.expectation_scoring import build_expectation_score


REPORT_VERSION = "source-proxy-level-2-expectation-report-v0.1"


class _AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "script" and attr.get("src"):
            self.refs.append(str(attr["src"]))
        if tag == "link" and attr.get("href") and str(attr.get("rel") or "").lower() in {"stylesheet", "preload", "icon"}:
            self.refs.append(str(attr["href"]))
        if tag in {"img", "audio", "video", "source", "iframe"}:
            value = attr.get("src") or attr.get("poster")
            if value:
                self.refs.append(str(value))


def detect_artifact_evidence_gaps(*, workspace: Path, entrypoint: str | Path = "") -> dict[str, Any]:
    root = workspace.resolve()
    entry = _entrypoint_path(root, entrypoint)
    references: list[str] = []
    missing: list[str] = []
    external: list[str] = []
    reason_codes: list[str] = []
    if not entry or not entry.is_file():
        return {
            "entrypoint": str(entry or ""),
            "referenced_local_files": [],
            "missing_local_references": [],
            "external_resources": [],
            "reason_codes": ["entrypoint_missing_for_asset_scan"],
        }
    parser = _AssetParser()
    parser.feed(entry.read_text(encoding="utf-8", errors="replace"))
    for ref in parser.refs:
        if _is_external(ref):
            external.append(ref)
            continue
        if ref.startswith(("data:", "mailto:", "tel:", "#")):
            continue
        local_path = (entry.parent / ref.split("#", 1)[0].split("?", 1)[0]).resolve()
        try:
            relative = local_path.relative_to(root).as_posix()
        except ValueError:
            missing.append(ref)
            continue
        references.append(relative)
        if not local_path.exists():
            missing.append(relative)
    if missing:
        reason_codes.append("missing_linked_local_files")
    if external:
        reason_codes.append("external_resources_present")
    if not missing:
        reason_codes.append("linked_local_files_resolved")
    return {
        "entrypoint": str(entry),
        "referenced_local_files": sorted(set(references)),
        "missing_local_references": sorted(set(missing)),
        "external_resources": sorted(set(external)),
        "reason_codes": sorted(set(reason_codes)),
    }


def build_decision_trace(
    *,
    score: dict[str, Any],
    verified_expectation_score: dict[str, Any],
    receipt: dict[str, Any] | None = None,
    browser_open_result: dict[str, Any] | None = None,
    behavior_probe_result: dict[str, Any] | None = None,
    evidence_refs: dict[str, str] | None = None,
) -> dict[str, Any]:
    initial = score.get("expectation_score") if isinstance(score.get("expectation_score"), dict) else build_expectation_score(score=score, receipt=receipt or {})
    browser = browser_open_result or {}
    behavior = behavior_probe_result or {}
    lane = score.get("model_lane_observability") if isinstance(score.get("model_lane_observability"), dict) else {}
    return {
        "report_version": REPORT_VERSION,
        "original_prompt": score.get("prompt") or verified_expectation_score.get("original_prompt") or "",
        "inferred_intent": verified_expectation_score.get("inferred_intent") or "",
        "route_type": score.get("route_type") or "",
        "task_shape": verified_expectation_score.get("task_shape") or "",
        "artifact_class": verified_expectation_score.get("artifact_class") or "",
        "expected_artifact_kind": verified_expectation_score.get("expected_artifact_kind") or "",
        "expected_interaction_level": verified_expectation_score.get("expected_interaction_level") or "",
        "selected_entrypoint": verified_expectation_score.get("selected_entrypoint") or "",
        "entrypoint_reason": verified_expectation_score.get("entrypoint_reason") or "",
        "model_authored_files": verified_expectation_score.get("model_authored_paths") or [],
        "proxy_suggested_files": verified_expectation_score.get("proxy_suggested_paths") or [],
        "backend_authored_content_detected": verified_expectation_score.get("backend_authored_content_detected"),
        "missing_local_references": verified_expectation_score.get("missing_local_references") or [],
        "external_resources": verified_expectation_score.get("external_resources") or [],
        "browser_open_result": {
            "verdict": verified_expectation_score.get("browser_open_verdict"),
            "opened": bool(browser.get("opened")),
        },
        "console_error_count": verified_expectation_score.get("console_error_count"),
        "page_error_count": verified_expectation_score.get("page_error_count"),
        "behavior_probe_result": {
            "verdict": behavior.get("verdict") or verified_expectation_score.get("behavior_probe_results", {}).get("verdict") or "",
            "reason": behavior.get("reason") or "",
            "passed": behavior.get("passed"),
        },
        "usability_score": verified_expectation_score.get("usability_score"),
        "intent_fit_score": verified_expectation_score.get("intent_fit_score"),
        "context_decision": verified_expectation_score.get("context_decision") or {},
        "web_search_decision": verified_expectation_score.get("web_search_decision"),
        "local_intelligence_decision": {
            "used": verified_expectation_score.get("local_intelligence_used") or [],
            "context_sources": verified_expectation_score.get("context_sources_used") or [],
        },
        "model_lane_selected": verified_expectation_score.get("model_lane_selected"),
        "sidecar_lane_status": {
            "live": bool(verified_expectation_score.get("sidecar_lanes_live")),
            "considered": lane.get("sidecar_lanes_considered") or score.get("sidecar_lanes_considered") or [],
        },
        "initial_live_expectation_verdict": initial.get("product_verdict"),
        "final_verified_expectation_verdict": verified_expectation_score.get("product_verdict"),
        "behavior_evidence_attached": _behavior_evidence_attached(behavior),
        "final_product_verdict": verified_expectation_score.get("product_verdict"),
        "reason_codes": verified_expectation_score.get("score_reason_codes") or [],
        "evidence_refs": evidence_refs or {},
    }


def build_batch_rollup(traces: list[dict[str, Any]]) -> dict[str, Any]:
    initial_counts = _counts(trace.get("initial_live_expectation_verdict") for trace in traces)
    verified_counts = _counts(trace.get("final_verified_expectation_verdict") for trace in traces)
    rows = []
    for trace in traces:
        rows.append(
            {
                "prompt": trace["original_prompt"],
                "initial_verdict": trace.get("initial_live_expectation_verdict"),
                "final_verdict": trace.get("final_verified_expectation_verdict"),
                "behavior_evidence_attached": trace.get("behavior_evidence_attached"),
                "files_created": len(trace.get("model_authored_files") or []),
                "missing_refs": len(trace.get("missing_local_references") or []),
                "external_resources": len(trace.get("external_resources") or []),
                "context_search_used": bool((trace.get("context_decision") or {}).get("web_search_used")),
                "lane_selected": trace.get("model_lane_selected"),
                "product_verdict": trace.get("final_product_verdict"),
                "key_reason_codes": _key_reasons(trace.get("reason_codes") or []),
            }
        )
    return {
        "report_version": REPORT_VERSION,
        "initial_verdict_counts": initial_counts,
        "verified_verdict_counts": verified_counts,
        "rows": rows,
    }


def render_batch_report_html(*, title: str, traces: list[dict[str, Any]], vocabulary: dict[str, str]) -> str:
    rollup = build_batch_rollup(traces)
    cards = "\n".join(_render_trace_card(trace) for trace in traces)
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(row['prompt']))}</td>"
        f"<td>{html.escape(str(row['initial_verdict']))}</td>"
        f"<td>{html.escape(str(row['final_verdict']))}</td>"
        f"<td>{html.escape(str(row['behavior_evidence_attached']))}</td>"
        f"<td>{html.escape(str(row['files_created']))}</td>"
        f"<td>{html.escape(str(row['missing_refs']))}</td>"
        f"<td>{html.escape(str(row['external_resources']))}</td>"
        f"<td>{html.escape(str(row['context_search_used']))}</td>"
        f"<td>{html.escape(str(row['lane_selected']))}</td>"
        f"<td><code>{html.escape(', '.join(row['key_reason_codes']))}</code></td>"
        "</tr>"
        for row in rollup["rows"]
    )
    vocab = "\n".join(f"<li><code>{html.escape(k)}</code>: {html.escape(v)}</li>" for k, v in sorted(vocabulary.items()))
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>"
        + html.escape(title)
        + "</title><style>body{font-family:Segoe UI,Arial,sans-serif;margin:24px;background:#f8fafc;color:#111827}"
        "table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #d1d5db;padding:7px;vertical-align:top}"
        ".counts{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}.counts div,.card{background:white;border:1px solid #d1d5db;border-radius:8px;padding:12px;margin:12px 0}"
        ".weak{border-left:6px solid #b45309}.pass{border-left:6px solid #15803d}.fail{border-left:6px solid #b91c1c}pre{white-space:pre-wrap;background:#f1f5f9;padding:8px;overflow:auto}code{background:#eef2f7;padding:1px 4px;border-radius:4px}</style></head><body>"
        f"<h1>{html.escape(title)}</h1>"
        "<div class='counts'>"
        f"<div><strong>Initial</strong><pre>{html.escape(json.dumps(rollup['initial_verdict_counts'], indent=2))}</pre></div>"
        f"<div><strong>Verified</strong><pre>{html.escape(json.dumps(rollup['verified_verdict_counts'], indent=2))}</pre></div>"
        "</div>"
        "<h2>Scorer Summary Rollup</h2><table><thead><tr><th>Prompt</th><th>Initial</th><th>Verified</th><th>Behavior evidence</th><th>Files</th><th>Missing refs</th><th>External</th><th>Search used</th><th>Lane</th><th>Key reasons</th></tr></thead><tbody>"
        + rows
        + "</tbody></table><h2>Per-Run Decision Traces</h2>"
        + cards
        + "<h2>Reason-Code Explanations</h2><ul>"
        + vocab
        + "</ul></body></html>"
    )


def _render_trace_card(trace: dict[str, Any]) -> str:
    verdict = str(trace.get("final_verified_expectation_verdict") or "").lower()
    cls = "pass" if verdict == "pass" else "weak" if verdict == "weak_pass" else "fail"
    links = trace.get("evidence_refs") or {}
    link_html = " ".join(
        f"<a href='{html.escape(str(target))}'>{html.escape(str(label))}</a>"
        for label, target in links.items()
        if target
    )
    body = {
        key: trace.get(key)
        for key in [
            "inferred_intent",
            "route_type",
            "task_shape",
            "artifact_class",
            "expected_artifact_kind",
            "expected_interaction_level",
            "selected_entrypoint",
            "entrypoint_reason",
            "model_authored_files",
            "proxy_suggested_files",
            "backend_authored_content_detected",
            "missing_local_references",
            "external_resources",
            "browser_open_result",
            "console_error_count",
            "page_error_count",
            "behavior_probe_result",
            "usability_score",
            "intent_fit_score",
            "context_decision",
            "web_search_decision",
            "local_intelligence_decision",
            "model_lane_selected",
            "sidecar_lane_status",
            "initial_live_expectation_verdict",
            "final_verified_expectation_verdict",
            "reason_codes",
        ]
    }
    return (
        f"<section class='card {cls}'><h3>{html.escape(str(trace.get('original_prompt') or ''))}</h3>"
        f"<p><strong>Initial:</strong> {html.escape(str(trace.get('initial_live_expectation_verdict')))} "
        f"<strong>Verified:</strong> {html.escape(str(trace.get('final_verified_expectation_verdict')))} "
        f"<strong>Behavior evidence:</strong> {html.escape(str(trace.get('behavior_evidence_attached')))}</p>"
        f"<p>{link_html}</p><pre>{html.escape(json.dumps(body, indent=2, sort_keys=True))}</pre></section>"
    )


def _entrypoint_path(root: Path, entrypoint: str | Path) -> Path | None:
    if entrypoint:
        path = Path(entrypoint)
        if not path.is_absolute():
            path = root / path
        return path.resolve()
    htmls = sorted(root.glob("*.html"))
    return htmls[0].resolve() if htmls else None


def _is_external(ref: str) -> bool:
    return ref.startswith(("http://", "https://", "//"))


def _behavior_evidence_attached(behavior: dict[str, Any]) -> bool:
    verdict = str(behavior.get("verdict") or "").upper()
    return verdict in {"PASS", "FAIL", "NEEDS_FIX", "ERROR"} and bool(behavior)


def _counts(values: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:
        key = str(value or "UNKNOWN")
        out[key] = out.get(key, 0) + 1
    return out


def _key_reasons(reasons: list[str]) -> list[str]:
    priority = [
        "behavior_pass",
        "behavior_weak",
        "missing_linked_local_files",
        "external_resources_present_review_reasonability",
        "web_search_unnecessary_for_local_artifact_prompt",
        "sidecar_lane_live_requires_approval",
        "backend_authored_content_detected",
        "safety_pass",
    ]
    picked = [reason for reason in priority if reason in reasons]
    return picked or reasons[:4]
