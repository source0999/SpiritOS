#!/usr/bin/env python3
"""Generate MD manifest + XML LLM context packs for Claude 3x10 audit evidence."""
from __future__ import annotations

import hashlib
import json
import xml.sax.saxutils as saxutils
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVID = Path(__file__).resolve().parent
LLM = EVID / "llm-context"
GENERATED_AT = datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cdata(text: str) -> str:
    return f"<![CDATA[\n{text}\n]]>"


def file_entry(path: Path, note: str = "") -> str:
    rel = path.relative_to(ROOT).as_posix()
    body = path.read_text(encoding="utf-8", errors="replace")
    note_xml = f'    <note>{saxutils.escape(note)}</note>\n' if note else ""
    return (
        f'  <file path="{rel}" bytes="{path.stat().st_size}" sha256="{sha256(path)}">\n'
        f"{note_xml}"
        f"    <content>{cdata(body)}</content>\n"
        f"  </file>\n"
    )


def pack_header(title: str, description: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<spiritos_source_proxy_pack
  generated_at="{GENERATED_AT}"
  generated_for="LLM elevated context — Claude 3x10 audit"
  audit_id="claude-3x10-audit-20260615"
  accepted_baseline="Integrated Level 5R2 GO (pre-audit)"
  audit_verdict="C (high confidence)"
>
  <title>{saxutils.escape(title)}</title>
  <description>{saxutils.escape(description)}</description>
"""


def main() -> None:
    LLM.mkdir(exist_ok=True)

    md_files = sorted(EVID.rglob("*.md"))
    md_files = [
        p
        for p in md_files
        if p.name not in ("index.md", "ALL-AUDIT-SUMMARY.md")
        and "generate-llm-context-packs" not in p.name
    ]

    results = json.loads((EVID / "battery-results.json").read_text(encoding="utf-8"))
    matrix_rows = results.get("matrix", [])

    # --- mini context pack manifest ---
    manifest = f"""# Claude 3x10 Audit Mini Context Pack Manifest

Context pack:

- Master XML: `docs/evidence/source-proxy-claude-3x10-audit-20260615/claude-3x10-audit-mini-context-pack.xml`
- Split packs: `docs/evidence/source-proxy-claude-3x10-audit-20260615/llm-context/` (pack-01..06)
- Consolidated MD: `docs/evidence/source-proxy-claude-3x10-audit-20260615/ALL-AUDIT-SUMMARY.md`
- Index: `docs/evidence/source-proxy-claude-3x10-audit-20260615/index.md`
- This manifest: `docs/evidence/source-proxy-claude-3x10-audit-20260615/claude-3x10-audit-mini-context-pack.md`

## Scope

PLAN: Claude 3x10 Basic Coding Battery Audit
PHASE: Live diagnostic execution + evidence-based audit
VERDICT: C (high confidence)

## Battery summary

| Metric | Value |
| --- | --- |
| Total prompts | 30 |
| productive_go | 22 |
| verifier_blocked_browser | 8 |
| unexpected_no_go | 0 |
| trace_mismatch | 0 |
| hardcoded_used | 0 |
| Receipts + traces | 30/30 |
| Proxy code patched | NONE |

## Hard stops honored

- Did not commit, push, or stage.
- Did not add TinyFish or xersearch.
- Did not promote Cartographer to route owner.
- Did not use `expected_result_state=browser_pass_expected` (no synthetic browser cheat).
- Did not mutate unrelated SpiritFlix/media work.

## Changed files (audit artifacts only)

- `scripts/source_proxy_claude_3x10_battery_runner.py` (additive runner)
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/**` (evidence tree)

## Top 10 urgent fixes

1. Real headless browser verifier (replace synthetic probe)
2. Functional verification for non-UI code
3. Quarantine prompt-fitted/scaffold code in decision.py
4. FIP-4 default-ON + preflight assert
5. Gate degraded advisory lanes on verdict
6. Strip raw model output from FIP-6 traces
7. Auth-gate receipt/trace endpoints
8. Structured productive/coder_path receipt fields
9. Collision-proof run_id + archive stale receipts
10. Runtime discipline (no stale on-disk vs in-memory proxy)

## Recommended next gate

```
BRITTON GO SOURCE PROXY HONESTY-HARDENING PLAN PR1 — IMPLEMENTATION (PHASE A ONLY)
```

See `reports/pivot-remediation-plan.md` for full plan.
"""
    (EVID / "claude-3x10-audit-mini-context-pack.md").write_text(manifest, encoding="utf-8")

    # Build 30-row matrix XML snippet
    matrix_xml = ["  <battery_matrix total=\"30\">"]
    for row in matrix_rows:
        matrix_xml.append(
            f'    <row prompt_id="{saxutils.escape(row["prompt_id"])}" set_id="{row["set_id"]}" '
            f'category="{saxutils.escape(row["category"])}" '
            f'score_class="{saxutils.escape(row["score_class"])}" '
            f'expected="{saxutils.escape(row["expected_score_class"])}" '
            f'verdict="{saxutils.escape(str(row.get("durable_verdict","")))}" '
            f'run_id="{saxutils.escape(str(row.get("run_id","")))}" '
            f'trace_match="{row.get("trace_matches_receipt")}" '
            f'elapsed_s="{row.get("elapsed_s")}" '
            f'target="{saxutils.escape(row.get("target",""))}" />'
        )
    matrix_xml.append("  </battery_matrix>")

    report_files = sorted((EVID / "reports").glob("*.md"))
    closeout_files = [
        EVID / "preflight.md",
        EVID / "battery-closeout.md",
        EVID / "set-1-closeout.md",
        EVID / "set-2-closeout.md",
        EVID / "set-3-closeout.md",
        EVID / "fixes/00-fixes-and-observations.md",
    ]
    data_files = [
        EVID / "battery-matrix.json",
        EVID / "battery-results.json",
    ]

    executive_summary = f"""
# Claude 3x10 Audit — Executive Summary for LLM Context

## Verdict: C (high confidence)

SpiritOS Source Proxy ran 30 messy human prompts on the REAL integrated hot path
(`/v1/decisions/prompt-packet`, FIP-1..5 enabled). Results: 22 productive_go, 8 verifier_blocked_browser, zero hard-fails.

## What worked (proven)
- Real Qwen coder path with perfect packet-hash discipline (30/30)
- Durable FIP-0 receipts + matching FIP-6 traces (30/30)
- Perfect scope containment to disposable target root (30/30)
- Scout/SearXNG honestly skipped (no false `used`)
- UI rows honestly NO-GO when no harness flag (no fake browser PASS)
- No hardcoded/trial/scaffold path triggered in battery
- Protected paths strong; no traversal or secret touch

## What failed (proven)
- productive_go means structural validity only — NOT working apps (calculator stub example)
- No real browser automation — synthetic probe only
- Hermes PASS on non-UI rows is low-evidence rubber-stamp
- Gemma/Hermes-critic timeouts do NOT gate GO (decorative lanes)
- Repair loop never fired organically (0/30)
- FIP-6 traces embed raw Qwen output (leakage)
- Prompt-fitted code exists in decision.py (dormant in battery, live liability)
- FIP-4 defaults OFF — legacy stub path is default without env flags

## Generalization
Sets 1/2/3 reworded same families → identical score classes. Shape-driven, not prompt-fitted.

## Files in this audit
- Runner: scripts/source_proxy_claude_3x10_battery_runner.py
- Evidence: docs/evidence/source-proxy-claude-3x10-audit-20260615/
- Reports: reports/full-proxy-audit.md + 6 specialized audits + pivot plan
"""

    # Pack 01 — executive + battery
    p01 = [pack_header("Executive summary and battery evidence", "Verdict, battery results, closeouts, matrix")]
    p01.append(file_entry(EVID / "index.md", "Master index for LLM context"))
    p01.append("  <executive_summary>")
    p01.append(cdata(executive_summary.strip()))
    p01.append("  </executive_summary>")
    p01.extend(matrix_xml)
    for p in closeout_files:
        if p.exists():
            p01.append(file_entry(p))
    p01.append("</spiritos_source_proxy_pack>\n")
    (LLM / "pack-01-executive-battery.xml").write_text("".join(p01), encoding="utf-8")

    # Pack 02 — audit reports
    p02 = [pack_header("Audit reports", "Full proxy audit + 6 specialized domain audits")]
    for p in report_files:
        p02.append(file_entry(p))
    p02.append("</spiritos_source_proxy_pack>\n")
    (LLM / "pack-02-audit-reports.xml").write_text("".join(p02), encoding="utf-8")

    # Pack 03 — remediation
    p03 = [pack_header("Pivot remediation plan", "PR1-PR3 honesty hardening + verification + routing")]
    p03.append(file_entry(EVID / "reports/pivot-remediation-plan.md"))
    p03.append("</spiritos_source_proxy_pack>\n")
    (LLM / "pack-03-remediation-plan.xml").write_text("".join(p03), encoding="utf-8")

    # Pack 04 — battery data JSON
    p04 = [pack_header("Battery machine data", "matrix JSON + results JSON (structured)")]
    for p in data_files:
        p04.append(file_entry(p))
    p04.append("</spiritos_source_proxy_pack>\n")
    (LLM / "pack-04-battery-data.xml").write_text("".join(p04), encoding="utf-8")

    # Pack 05 — receipts/traces manifest (summaries only, not full JSON bodies)
    def receipt_summary(path: Path) -> str:
        data = json.loads(path.read_text(encoding="utf-8"))
        verdict = data.get("verdict") or data.get("final_verdict") or ""
        run_id = data.get("run_id") or path.stem
        qwen = (data.get("qwen_coder_status") or {}).get("status", "")
        return f"{run_id} | {verdict[:80]} | qwen={qwen}"

    receipt_dir = EVID / "receipts"
    trace_dir = EVID / "traces"
    manifest_lines = ["# Receipt and trace file manifest", ""]
    p05 = [pack_header("Receipts and traces manifest", "Per-file summaries; full JSON on disk in receipts/ and traces/")]
    p05.append("  <receipts_manifest count=\"{}\">".format(len(list(receipt_dir.glob("*.json")))))
    for p in sorted(receipt_dir.glob("*.json")):
        rel = p.relative_to(ROOT).as_posix()
        summary = receipt_summary(p)
        manifest_lines.append(f"- `{rel}` — {summary}")
        p05.append(
            f'    <receipt path="{rel}" sha256="{sha256(p)}" bytes="{p.stat().st_size}" '
            f'summary="{saxutils.escape(summary)}" />'
        )
    p05.append("  </receipts_manifest>")
    p05.append("  <traces_manifest count=\"{}\">".format(len(list(trace_dir.glob("*.json")))))
    for p in sorted(trace_dir.glob("*.json")):
        rel = p.relative_to(ROOT).as_posix()
        data = json.loads(p.read_text(encoding="utf-8"))
        verdict = data.get("verdict") or data.get("final_verdict") or ""
        run_id = data.get("run_id") or p.stem
        summary = f"{run_id} | {verdict[:80]}"
        manifest_lines.append(f"- `{rel}` — {summary}")
        p05.append(
            f'    <trace path="{rel}" sha256="{sha256(p)}" bytes="{p.stat().st_size}" '
            f'summary="{saxutils.escape(summary)}" />'
        )
    p05.append("  </traces_manifest>")
    p05.append("</spiritos_source_proxy_pack>\n")
    (LLM / "pack-05-receipts-traces-manifest.xml").write_text("".join(p05), encoding="utf-8")
    (EVID / "receipts-traces-manifest.md").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    # Pack 06 — runner script
    runner = ROOT / "scripts/source_proxy_claude_3x10_battery_runner.py"
    p06 = [pack_header("Battery runner script", "scripts/source_proxy_claude_3x10_battery_runner.py")]
    if runner.exists():
        p06.append(file_entry(runner))
    p06.append("</spiritos_source_proxy_pack>\n")
    (LLM / "pack-06-runner-script.xml").write_text("".join(p06), encoding="utf-8")

    # Consolidated ALL-AUDIT-SUMMARY.md
    all_summary_parts = [executive_summary.strip(), "", "---", ""]
    for p in md_files:
        all_summary_parts.append(f"## Source: {p.relative_to(EVID).as_posix()}")
        all_summary_parts.append("")
        all_summary_parts.append(p.read_text(encoding="utf-8", errors="replace"))
        all_summary_parts.append("")
        all_summary_parts.append("---")
        all_summary_parts.append("")
    (EVID / "ALL-AUDIT-SUMMARY.md").write_text("\n".join(all_summary_parts), encoding="utf-8")

    # Master XML — all key MD + matrix + executive
    master = [pack_header(
        "Claude 3x10 Source Proxy Audit — Master LLM Context Pack",
        "Complete audit evidence: executive summary, all MD reports/closeouts, battery matrix, remediation plan",
    )]
    master.append(file_entry(EVID / "claude-3x10-audit-mini-context-pack.md", "Manifest"))
    master.append("  <executive_summary>")
    master.append(cdata(executive_summary.strip()))
    master.append("  </executive_summary>")
    master.extend(matrix_xml)
    for p in md_files:
        master.append(file_entry(p))
    for p in data_files:
        master.append(file_entry(p))
    master.append("</spiritos_source_proxy_pack>\n")
    (EVID / "claude-3x10-audit-mini-context-pack.xml").write_text("".join(master), encoding="utf-8")

    # --- index.md (written last so it lists all generated artifacts) ---
    index_lines = [
        "# Claude 3x10 Audit — LLM Context Index",
        "",
        f"Generated: {GENERATED_AT}",
        "",
        "## Purpose",
        "",
        "Elevated context pack for LLMs reviewing the SpiritOS Source Proxy",
        "Claude Opus Max 3x10 basic coding battery audit (2026-06-15/16 UTC).",
        "",
        "## Executive summary",
        "",
        "- **Verdict:** C (high confidence)",
        "- **Battery:** 30/30 prompts on real integrated path (FIP-4 Qwen + FIP-5 verifier)",
        "- **Scores:** 22 productive_go, 8 verifier_blocked_browser, 0 hard-fails",
        "- **Receipts/traces:** 30/30 durable, 30/30 trace matches receipt",
        "- **Critical caveat:** productive_go = structural validity only, NOT working apps",
        "- **Top gap:** no real browser verifier; synthetic pass only with harness flag",
        "",
        "## Context packs (XML)",
        "",
        "| Pack | Path | Contents |",
        "| --- | --- | --- |",
        "| Master | `claude-3x10-audit-mini-context-pack.xml` | All summaries + reports + matrix |",
        "| Pack 01 | `llm-context/pack-01-executive-battery.xml` | Executive + battery closeouts + matrix |",
        "| Pack 02 | `llm-context/pack-02-audit-reports.xml` | Full audit reports (7) |",
        "| Pack 03 | `llm-context/pack-03-remediation-plan.xml` | Pivot remediation plan |",
        "| Pack 04 | `llm-context/pack-04-battery-data.xml` | JSON results + matrix |",
        "| Pack 05 | `llm-context/pack-05-receipts-traces-manifest.xml` | 31 receipt + 31 trace file index |",
        "| Pack 06 | `llm-context/pack-06-runner-script.xml` | Battery runner source |",
        "",
        "## Consolidated markdown",
        "",
        "| File | Role |",
        "| --- | --- |",
        "| `ALL-AUDIT-SUMMARY.md` | Single-file concatenation of all audit MD |",
        "| `receipts-traces-manifest.md` | Receipt/trace path + verdict index |",
        "| `claude-3x10-audit-mini-context-pack.md` | Manifest (start here) |",
        "",
        "## Markdown artifacts",
        "",
        "| File | Role |",
        "| --- | --- |",
    ]
    for p in md_files:
        rel = p.relative_to(EVID).as_posix()
        index_lines.append(f"| `{rel}` | evidence doc |")
    index_lines.extend(
        [
            "",
            "## Machine-readable data",
            "",
            "| File | Role |",
            "| --- | --- |",
            "| `battery-matrix.json` | 30 prompt definitions |",
            "| `battery-results.json` | scored matrix summary |",
            "| `battery-raw.json` | full per-row runner records |",
            "| `battery-console.log` | runner log |",
            "| `receipts/*.json` | 31 durable FIP-0 receipts (incl. smoke duplicate) |",
            "| `traces/*.json` | 31 FIP-6 operator traces |",
            "",
            "## Runner",
            "",
            "`scripts/source_proxy_claude_3x10_battery_runner.py`",
            "",
            "## Regenerate",
            "",
            "`python3 docs/evidence/source-proxy-claude-3x10-audit-20260615/generate-llm-context-packs.py`",
            "",
        ]
    )
    (EVID / "index.md").write_text("\n".join(index_lines), encoding="utf-8")

    print(f"Generated index.md, ALL-AUDIT-SUMMARY.md, manifest, master XML, and 6 split packs under {LLM}")


if __name__ == "__main__":
    main()
