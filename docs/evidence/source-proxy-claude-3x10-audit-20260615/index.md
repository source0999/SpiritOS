# Claude 3x10 Audit — LLM Context Index

Generated: 2026-06-16T01:38:49+00:00

## Purpose

Elevated context pack for LLMs reviewing the SpiritOS Source Proxy
Claude Opus Max 3x10 basic coding battery audit (2026-06-15/16 UTC).

## Executive summary

- **Verdict:** C (high confidence)
- **Battery:** 30/30 prompts on real integrated path (FIP-4 Qwen + FIP-5 verifier)
- **Scores:** 22 productive_go, 8 verifier_blocked_browser, 0 hard-fails
- **Receipts/traces:** 30/30 durable, 30/30 trace matches receipt
- **Critical caveat:** productive_go = structural validity only, NOT working apps
- **Top gap:** no real browser verifier; synthetic pass only with harness flag

## Context packs (XML)

| Pack | Path | Contents |
| --- | --- | --- |
| Master | `claude-3x10-audit-mini-context-pack.xml` | All summaries + reports + matrix |
| Pack 01 | `llm-context/pack-01-executive-battery.xml` | Executive + battery closeouts + matrix |
| Pack 02 | `llm-context/pack-02-audit-reports.xml` | Full audit reports (7) |
| Pack 03 | `llm-context/pack-03-remediation-plan.xml` | Pivot remediation plan |
| Pack 04 | `llm-context/pack-04-battery-data.xml` | JSON results + matrix |
| Pack 05 | `llm-context/pack-05-receipts-traces-manifest.xml` | 31 receipt + 31 trace file index |
| Pack 06 | `llm-context/pack-06-runner-script.xml` | Battery runner source |

## Consolidated markdown

| File | Role |
| --- | --- |
| `ALL-AUDIT-SUMMARY.md` | Single-file concatenation of all audit MD |
| `receipts-traces-manifest.md` | Receipt/trace path + verdict index |
| `claude-3x10-audit-mini-context-pack.md` | Manifest (start here) |

## Markdown artifacts

| File | Role |
| --- | --- |
| `battery-closeout.md` | evidence doc |
| `claude-3x10-audit-mini-context-pack.md` | evidence doc |
| `fixes/00-fixes-and-observations.md` | evidence doc |
| `preflight.md` | evidence doc |
| `receipts-traces-manifest.md` | evidence doc |
| `reports/anti-cheat-security-audit.md` | evidence doc |
| `reports/full-proxy-audit.md` | evidence doc |
| `reports/model-lane-audit.md` | evidence doc |
| `reports/pivot-remediation-plan.md` | evidence doc |
| `reports/receipt-trace-audit.md` | evidence doc |
| `reports/search-context-audit.md` | evidence doc |
| `reports/verifier-repair-audit.md` | evidence doc |
| `set-1-closeout.md` | evidence doc |
| `set-2-closeout.md` | evidence doc |
| `set-3-closeout.md` | evidence doc |

## Machine-readable data

| File | Role |
| --- | --- |
| `battery-matrix.json` | 30 prompt definitions |
| `battery-results.json` | scored matrix summary |
| `battery-raw.json` | full per-row runner records |
| `battery-console.log` | runner log |
| `receipts/*.json` | 31 durable FIP-0 receipts (incl. smoke duplicate) |
| `traces/*.json` | 31 FIP-6 operator traces |

## Runner

`scripts/source_proxy_claude_3x10_battery_runner.py`

## Regenerate

`python3 docs/evidence/source-proxy-claude-3x10-audit-20260615/generate-llm-context-packs.py`
