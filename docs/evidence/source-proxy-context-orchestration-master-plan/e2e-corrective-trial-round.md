# E2E Corrective Trial Round - Plan 1 + Plan 2

Date: 2026-06-09

Scope:
- Re-ran the eight messy prompts from the earlier agent-lab comparison.
- Used the updated Source Proxy context readiness packet and coder proposal path.
- Kept the default coder route on `qwen2.5-coder:7b`.
- Did not apply generated changes to repo files.
- Did not run Plan 3, Coder 50, Coder 100, hidden workers, commits, pushes, or continuation queues.

## Increment 1 - Model Availability And Prior Baseline

Command summary:
- `ollama list`
- `tests/agent-lab-demo/messy-prompt-comparison-results.json`

Findings:
- `qwen2.5-coder:7b` is installed and was used for the live E2E prompt pass.
- `qwen2.5-coder:14b` is not installed, so 14B comparison is blocked as `blocked_model_not_installed`.
- The prior comparison artifact exists and contains 9 rows:
  - 8 prompt rows for the original messy prompts.
  - 1 extra 14B row for the premium coding cockpit prompt.
- Prior artifact diagnostics showed 1-3 parsed file blocks per prompt, but it did not prove the new Source Proxy context readiness packet or Obsidian source usage.

GO/NO-GO: GO for 7B E2E run. 14B comparison is NO-GO until the exact requested model exists locally.

## Increment 2 - Full Source Proxy Context Packet Per Prompt

Flow:
- Called `build_context_source_readiness_packet(prompt, project_root=/home/source/SpiritOS)` for each prompt.

Result:
- All 8 prompts returned `ready_for_source_proxy_packet=true`.
- All 8 prompts reported:
  - `cartographer=used`
  - `obsidian=used`
  - `scout_search=used`
  - `design=used`
- Obsidian returned real notes from `/home/source/SpiritOS/data/design-vault`.

Per-prompt Obsidian evidence:

| Prompt slug | Obsidian used | Notes selected | Context chars | Paths |
|---|---:|---:|---:|---|
| `init-experimental-homepage` | yes | 5 | 4963 | `README.md`, `packs/internal-dashboard-demo-v4/README.md`, `packs/internal-dashboard-demo-v4/notes.md`, `source-cards/approval-checklist.md`, `token-model-v0.1.md` |
| `coding-cockpit-modern` | yes | 5 | 5929 | `source-cards/approval-checklist.md`, `README.md`, `packs/internal-dashboard-demo-v4/README.md`, `packs/internal-dashboard-demo-v4/notes.md`, `token-model-v0.1.md` |
| `trial-runner-dark-mode` | yes | 5 | 3663 | `packs/internal-dashboard-demo-v4/notes.md`, `README.md`, `packs/internal-dashboard-demo-v4/README.md`, `source-cards/approval-checklist.md`, `token-model-v0.1.md` |
| `agent-dashboard-fake-data` | yes | 5 | 5201 | `README.md`, `packs/internal-dashboard-demo-v4/README.md`, `packs/internal-dashboard-demo-v4/notes.md`, `source-cards/approval-checklist.md`, `token-model-v0.1.md` |
| `dashboard-energy` | yes | 5 | 5929 | `README.md`, `packs/internal-dashboard-demo-v4/README.md`, `packs/internal-dashboard-demo-v4/notes.md`, `source-cards/approval-checklist.md`, `token-model-v0.1.md` |
| `server-health` | yes | 2 | 1934 | `README.md`, `source-cards/approval-checklist.md` |
| `experimental-homepage-fix` | yes | 2 | 2360 | `README.md`, `packs/internal-dashboard-demo-v4/README.md` |
| `premium-coding-cockpit` | yes | 5 | 5929 | `source-cards/approval-checklist.md`, `README.md`, `packs/internal-dashboard-demo-v4/README.md`, `packs/internal-dashboard-demo-v4/notes.md`, `token-model-v0.1.md` |

GO/NO-GO: GO. Obsidian is enabled, read-only, and returning real context packets.

## Increment 3 - 7B E2E Coder Output Contract Trial

Flow:
- Built a scoped `ArchitectPlan` + `CoderPacket` per prompt.
- Ran `propose_coder_agent_diff_payload_from_plan(..., force_live_model=True)`.
- Called local Ollama through HTTP `/api/generate` with `stream=false` to avoid CLI terminal repaint bytes.
- Used temporary workspaces only. No generated changes were applied.

Aggregate:
- Total prompts: 8
- Clean file blocks: 8
- Blocked: 0
- Empty diffs: 0
- Markdown fences in raw output: 0
- Markdown fences in parser diagnostics: 0
- Output mode: `xml_file_block` for all 8
- Validation: `preview_ready` for all 8

Per-prompt output evidence:

| Prompt slug | Clean file block | Fences | Mode | Validation | Diff lines | Notes |
|---|---:|---:|---|---|---:|---|
| `init-experimental-homepage` | yes | no | `xml_file_block` | `preview_ready` | 17 | Clean scoped homepage replacement |
| `coding-cockpit-modern` | yes | no | `xml_file_block` | `preview_ready` | 16 | Clean modernization replacement |
| `trial-runner-dark-mode` | yes | no | `xml_file_block` | `preview_ready` | 13 | Clean dark-mode surface replacement |
| `agent-dashboard-fake-data` | yes | no | `xml_file_block` | `preview_ready` | 45 | Clean dashboard replacement |
| `dashboard-energy` | yes | no | `xml_file_block` | `preview_ready` | 16 | Clean higher-energy dashboard replacement |
| `server-health` | yes | no | `xml_file_block` | `preview_ready` | 12 | Clean Markdown report replacement |
| `experimental-homepage-fix` | yes | no | `xml_file_block` | `preview_ready` | 13 | Clean homepage fix replacement |
| `premium-coding-cockpit` | yes | no | `xml_file_block` | `preview_ready` | 17 | Clean premium cockpit replacement |

GO/NO-GO: GO. The updated output contract is stable for the eight messy prompts on 7B when called through the non-interactive Ollama API.

## Harness Issue Found And Resolved

An initial dry-run harness called `ollama run` through the CLI. That produced ANSI cursor-control repaint bytes in stdout for several responses, causing invalid TSX validation failures that were transport noise rather than model output contract failures.

Resolution:
- Switched the harness to Ollama HTTP `/api/generate` with `stream=false`.
- Re-ran all 8 prompts.
- All 8 passed cleanly.

No Source Proxy code change was applied for this issue.

## Comparison To Earlier Runs

Earlier run:
- Prior artifact: `tests/agent-lab-demo/messy-prompt-comparison-results.json`.
- It captured parsed file blocks for the messy prompts, but several prompts produced multiple file blocks.
- It did not verify the updated Source Proxy context readiness packet.
- It did not prove Obsidian was enabled and returning real note context.

Corrective run:
- All 8 7B prompts produced exactly one clean XML file block through the Source Proxy coder proposal path.
- No markdown fences appeared.
- No malformed file blocks appeared.
- No empty diffs appeared.
- Every per-prompt context readiness packet included real Obsidian context plus Cartographer, Scout/Search, and Design.
- 14B comparison remains blocked only because `qwen2.5-coder:14b` is not installed locally.

## Closeout

Plan 1 corrective readiness: GO.

Plan 2 corrective readiness: GO for context packet usability. Obsidian is enabled, read-only, and returning real notes in the Source Proxy context readiness packet.

Stop condition honored:
- Stopped after corrective Plan 1 + Plan 2 E2E verification.
- Did not proceed to Plan 3.
- Did not apply generated model diffs.
- Did not switch the default coder route.
