from __future__ import annotations

import hashlib
import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = (
    ROOT
    / "docs"
    / "evidence"
    / "source-proxy-full-integration-pivot"
    / "today-handoff-2026-06-15"
)
FIP_ROOT = ROOT / "docs" / "evidence" / "source-proxy-full-integration-pivot"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def xml_file_entry(path: Path, *, note: str = "", include_content: bool = True) -> str:
    text = read_text(path)
    body = [
        f'  <file path="{escape(rel(path))}" bytes="{path.stat().st_size}" sha256="{sha256_text(text)}">',
    ]
    if note:
        body.append(f"    <note>{escape(note)}</note>")
    if include_content:
        body.append("    <content><![CDATA[")
        body.append(text.replace("]]>", "]]]]><![CDATA[>"))
        body.append("    ]]></content>")
    body.append("  </file>")
    return "\n".join(body)


def write_xml_pack(name: str, title: str, description: str, entries: list[str]) -> Path:
    path = OUT_DIR / name
    content = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<spiritos_source_proxy_pack',
            f'  generated_at="{datetime.now(timezone.utc).isoformat()}"',
            '  generated_for="Britton mobile handoff and external grading"',
            '  accepted_state="Integrated Level 5R2 GO"',
            '>',
            f"  <title>{escape(title)}</title>",
            f"  <description>{escape(description)}</description>",
            *entries,
            "</spiritos_source_proxy_pack>",
            "",
        ]
    )
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def load_json(path: Path) -> dict:
    return json.loads(read_text(path))


def summarize_counts(path: Path) -> str:
    data = load_json(path)
    return json.dumps(data.get("counts", data), indent=2, sort_keys=True)


def level5r2_run_ids() -> list[str]:
    data = load_json(FIP_ROOT / "integrated-level-5R2" / "integrated-level-5R2-results.json")
    return [str(row["run_id"]) for row in data.get("prompt_matrix", [])]


def build_markdown_summary() -> Path:
    summary_path = OUT_DIR / "britton-spiritos-proxy-work-summary-2026-06-15.md"
    level5r2_counts = summarize_counts(
        FIP_ROOT / "integrated-level-5R2" / "integrated-level-5R2-results.json"
    )
    text = f"""# Britton SpiritOS Source Proxy Work Summary

Date prepared: 2026-06-15

Purpose: portable handoff for Britton, group review, GPT grading, and future Codex threads.

## Executive Summary

This work took Source Proxy from the post-FIP-7 uncertainty point through FIP-7R, Integrated Levels 3, 4, 5, 5R, 5R2, and post-Level-5 stabilization. The accepted current state is **Integrated Level 5R2 GO**.

No post-Level-5 expansion has started. TinyFish was not added. xersearch was not created. Cartographer was not promoted to route ownership. No commit or push was performed.

## Timeline

1. Reconciled the repo after a duplicate/stale FIP-4 chat and confirmed the accepted FIP-5/FIP-6/FIP-7 work was still present.
2. Ran FIP-7R remediation only. Fixed slow/local Qwen timeout behavior, Scout overlong-query/no-allowed-packet truth handling, and gauntlet runner timeout issues. FIP-7R closed as GO.
3. Ran Integrated Level 3 against the live Source Proxy stack. Level 3 closed as GO with durable receipts and FIP-6 traces.
4. Ran Integrated Level 4 with a stricter 12-prompt stability/behavior matrix. Level 4 closed as GO.
5. Ran Integrated Level 5 with a 20-prompt full-stack matrix. Level 5 was CONFIG-BLOCKED by two Hermes verifier no-op output-contract failures.
6. Ran Integrated Level 5R. It fixed the no-op Hermes output-contract issue but exposed three unexpected NO-GO rows: two browser/Hermes evidence mismatch rows and one malformed Qwen action output row.
7. Ran Integrated Level 5R2. It remediated the accepted 5R blockers and closed as GO.
8. Wrote post-Level-5 stabilization and active-context handoff docs.
9. Prepared a commit/stage planning recommendation without staging, committing, pushing, deleting, or reverting anything.

## Accepted Final Proof

Integrated Level 5R2 full matrix counts:

```json
{level5r2_counts}
```

Latest accepted Level 5R2 run:

- Run ID: `fip0-2aa8cc99f2fc1657`
- Verdict: `GO: fip5_required_verifier_and_repair_complete`
- Trace version: `fip6.operator_trace.v1`

## What Changed In Source Proxy

- Durable FIP-0 receipts became the universal truth record for runtime lane state.
- FIP-1 context lanes were wired as advisory context: Obsidian, Cartographer, Design, Mac advisory status.
- FIP-2 local research truth was wired with honest Scout/SearXNG attribution and no false `used` marking.
- FIP-3 local Gemma/Hermes pre-coder lanes were added while keeping Qwen coding-only.
- FIP-4 final coder packet and Qwen action-output contract were enforced.
- FIP-5 deterministic/browser/Hermes verifier and bounded Qwen repair loop were added.
- FIP-6 operator trace endpoints projected receipt truth without private reasoning.
- FIP-7R made local Qwen slow-output behavior and Scout no-allowed-packet truth durable enough for gauntlet proof.
- Integrated Levels 3, 4, 5, 5R, and 5R2 proved the full stack with receipts and traces.

## Current Runtime Runbook

- Authoritative runtime checkout: Linux `source-server`, `/home/source/SpiritOS`
- Launch command: `npm run proxy:https:lan`
- Source Proxy URL: `https://127.0.0.1:8787`
- Latest receipt: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest`
- Latest trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest/trace`
- By-run trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/<run_id>/trace`

## Important Boundaries

- TinyFish remains deferred and requires Britton approval.
- xersearch remains missing and must not be created without approval.
- Cartographer remains advisory/preview context, not route owner.
- No post-Level-5 expansion has started.
- Old artifact-only ladders are not scoring authority.
- Safety blocks are scored separately from productive GO.

## Dirty Tree State

The worktree is intentionally broad and dirty. Accepted Source Proxy/FIP work sits beside unrelated SpiritFlix/media work and duplicate/stale FIP-4 artifacts. Do not bulk-stage or bulk-commit.

Recommended next gate: commit/stage preparation approval, with reviewable slices:

1. Source Proxy runtime/code/tests.
2. FIP/integrated runners and evidence, with duplicate/stale FIP-4 exclusions.
3. Stabilization/active-context docs.

## Bundle Contents

This directory contains:

- `britton-spiritos-proxy-work-summary-2026-06-15.md`: this human summary.
- `pack-00-index.xml`: index and grading map.
- `pack-01-governance-closeouts.xml`: closeouts and active context.
- `pack-02-runtime-source.xml`: Source Proxy runtime source and tests.
- `pack-03-runners.xml`: FIP and integrated runner scripts.
- `pack-04-results-matrices.xml`: accepted result matrices and key evidence JSON.
- `pack-05-level5r2-receipts.xml`: Level 5R2 durable receipt set.

## How To Grade

Read the packs in order:

1. `pack-00-index.xml`
2. `pack-01-governance-closeouts.xml`
3. `pack-02-runtime-source.xml`
4. `pack-03-runners.xml`
5. `pack-04-results-matrices.xml`
6. `pack-05-level5r2-receipts.xml`

The shortest review path is summary + Level 5R2 closeout + Level 5R2 results JSON + representative receipts.
"""
    summary_path.write_text(text, encoding="utf-8", newline="\n")
    return summary_path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = build_markdown_summary()

    packs: list[Path] = []

    index_entries = [
        "  <grading_map>",
        "    <accepted_state>Integrated Level 5R2 GO</accepted_state>",
        "    <current_runtime>/home/source/SpiritOS via npm run proxy:https:lan on https://127.0.0.1:8787</current_runtime>",
        "    <do_not_start>post-Level-5 expansion, TinyFish, xersearch, new model lanes, Cartographer ownership promotion</do_not_start>",
        "    <recommended_review_order>summary, governance closeouts, runtime source, runners, results matrices, Level 5R2 receipts</recommended_review_order>",
        "  </grading_map>",
        xml_file_entry(summary_path, note="Human-readable mobile/group/GPT summary."),
    ]
    packs.append(
        write_xml_pack(
            "pack-00-index.xml",
            "Index and grading map",
            "Entry point for reviewing the accepted SpiritOS Source Proxy full-integration work.",
            index_entries,
        )
    )

    governance_files = [
        "active-context.md",
        "post-level-5-stabilization-closeout.md",
        "fip-state-reconciliation-after-duplicate-fip4.md",
        "fip-7R-closeout.md",
        "integrated-level-3-closeout.md",
        "integrated-level-4-closeout.md",
        "integrated-level-5-closeout.md",
        "integrated-level-5R-closeout.md",
        "integrated-level-5R2-closeout.md",
    ]
    packs.append(
        write_xml_pack(
            "pack-01-governance-closeouts.xml",
            "Governance and closeouts",
            "Authority docs and closeouts from reconciliation through Integrated Level 5R2 and stabilization.",
            [
                xml_file_entry(FIP_ROOT / file_name, note="Accepted governance/evidence closeout.")
                for file_name in governance_files
            ],
        )
    )

    source_files = [
        "source_proxy/api/decision.py",
        "source_proxy/decision/model_lanes.py",
        "source_proxy/decision/research.py",
        "source_proxy/decision/scout_research.py",
        "source_proxy/tests/test_prompt_packet_context_metadata.py",
        "source_proxy/tests/test_scout_research_bridge.py",
        "src/app/coding/page.tsx",
        "src/app/v1/decisions/fip0-receipts/latest/route.ts",
        "src/app/v1/decisions/fip0-receipts/latest/trace/route.ts",
        "src/app/v1/decisions/fip0-receipts/[runId]/route.ts",
        "src/app/v1/decisions/fip0-receipts/[runId]/trace/route.ts",
    ]
    packs.append(
        write_xml_pack(
            "pack-02-runtime-source.xml",
            "Runtime source and tests",
            "Core Source Proxy implementation, route projection, and focused tests needed to grade runtime behavior.",
            [
                xml_file_entry(ROOT / file_name, note="Runtime source/test file.")
                for file_name in source_files
                if (ROOT / file_name).exists()
            ],
        )
    )

    runner_files = [
        "scripts/fip7_gauntlet_runner.py",
        "scripts/integrated_level3_runner.py",
        "scripts/integrated_level4_runner.py",
        "scripts/integrated_level5_runner.py",
        "scripts/integrated_level5r_runner.py",
        "scripts/integrated_level5r2_runner.py",
    ]
    packs.append(
        write_xml_pack(
            "pack-03-runners.xml",
            "Runner scripts",
            "Gauntlet and integrated proof runners used for FIP-7R and Integrated Levels 3 through 5R2.",
            [
                xml_file_entry(ROOT / file_name, note="Accepted proof runner.")
                for file_name in runner_files
                if (ROOT / file_name).exists()
            ],
        )
    )

    result_files = [
        "fip-7R-gauntlet/fip-7R-gauntlet-rerun-results.json",
        "integrated-level-3/integrated-level-3-results.json",
        "integrated-level-4/integrated-level-4-results.json",
        "integrated-level-5/integrated-level-5-results.json",
        "integrated-level-5R/integrated-level-5R-results.json",
        "integrated-level-5R2/integrated-level-5R2-targeted-results.json",
        "integrated-level-5R2/integrated-level-5R2-results.json",
        "integrated-level-5R2/integrated-level-5R2-console.log",
    ]
    packs.append(
        write_xml_pack(
            "pack-04-results-matrices.xml",
            "Results matrices",
            "Accepted result matrices and console proof needed to grade receipt/trace, lane truth, model stability, search truth, verifier/repair, and safety-block behavior.",
            [
                xml_file_entry(FIP_ROOT / file_name, note="Accepted result/evidence artifact.")
                for file_name in result_files
                if (FIP_ROOT / file_name).exists()
            ],
        )
    )

    receipt_entries: list[str] = []
    receipt_root = FIP_ROOT / "fip-0-receipts"
    for run_id in level5r2_run_ids():
        receipt_path = receipt_root / f"{run_id}.json"
        if receipt_path.exists():
            receipt_entries.append(
                xml_file_entry(
                    receipt_path,
                    note="Durable receipt from accepted Integrated Level 5R2 full matrix.",
                )
            )
    packs.append(
        write_xml_pack(
            "pack-05-level5r2-receipts.xml",
            "Integrated Level 5R2 receipts",
            "Durable receipt set for the accepted Level 5R2 full matrix.",
            receipt_entries,
        )
    )

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": rel(summary_path),
        "packs": [rel(path) for path in packs],
        "zip_name": "britton-spiritos-source-proxy-handoff-2026-06-15.zip",
        "accepted_state": "Integrated Level 5R2 GO",
    }
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
