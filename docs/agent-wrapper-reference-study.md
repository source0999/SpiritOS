# Agent Wrapper Reference Study

Status date: 2026-05-18
Phase: 11.0.2
Branch: main

## Boundary

This is a research and comparison increment only. No Spirit Cowork Console proposal was created, no source code was changed, and no provider adapter implementation was started.

SpiritOS remains the system of record. External tools are reference material for UX, workflow, and provider-routing ideas.

## Sources

- AionUi: https://aionui.com/
- OpenAI Codex: https://openai.com/codex
- Continue rules and checks: https://docs.continue.dev/customize/rules and https://docs.continue.dev/
- Cline overview and Plan/Act: https://docs.cline.bot/cline-overview and https://docs.cline.bot/features/plan-and-act
- Goose permissions and CLI providers: https://goose-docs.ai/docs/guides/goose-permissions/ and https://goose-docs.ai/docs/guides/cli-providers/
- OpenCode: https://opencode.ai/ and https://dev.opencode.ai/docs
- Local AionUi evaluation: `docs/aionui-reference-study.md`

## Comparison Table

| Tool | Best idea to borrow | Risk | SpiritOS equivalent | Decision |
| --- | --- | --- | --- | --- |
| AionUi | Workspace picker, model selector, permission mode dropdown, visible tool steps, history/task sidebar, provider configuration panel. | GUI dependency, broad desktop authority, repo-local `.aionrs/` state, uneven local model tool support. | Source Proxy plus future SpiritOS provider console. | Borrow UX only; do not depend on AionUi. |
| Codex App | Parallel agent threads, worktrees/cloud environments, review-focused workflow, long-running background coding tasks. | External agent execution must not bypass Source Proxy, reviewer, or approval gates. | Existing Codex CLI adapter and evidence capture under Source Proxy. | Keep Codex CLI as a worker; borrow review/worktree mental model. |
| Continue | Repo-defined rules and checks that can live with the codebase. | IDE/cloud checks are not the trust boundary; quality rules can drift from Source Proxy gates. | TaskSpec, verifier, reviewer, and Cartographer checks. | Borrow repo-defined check/rule ergonomics. |
| Cline | Plan/Act separation, explicit approval before actions, CLI/headless option, MCP marketplace patterns. | Marketplace/tool installation can expand authority quickly if not governed. | Source Proxy planning vs execution boundary and provider allowlist. | Borrow Plan/Act language and explicit approval UX. |
| Goose | Permission modes such as chat, approve, smart approve, and auto; provider routing through CLI/ACP options. | Auto modes and extension ecosystems can exceed SpiritOS authority if copied directly. | Permission mode policy, provider adapters, and approval gate. | Borrow permission mode vocabulary; keep approval deterministic. |
| OpenCode | Provider-agnostic terminal agent behavior and model/provider configuration. | Terminal-native agent can still write unless wrapped by Source Proxy constraints. | Future provider adapter layer for local Ollama, Codex CLI, Gemini CLI, and optional APIs. | Borrow provider-agnostic configuration model. |
| SpiritOS | TaskSpec, `allowed_files`, diff preview, verifier, reviewer, approval gate, evidence capture, Cartographer logging. | Needs better provider routing UI and multi-agent/task history surfaces. | SpiritOS itself. | Remain system of record. |

## Findings By Category

### Multi-Agent Support

AionUi and Codex App are the strongest references for parallel agent surfaces. SpiritOS should not copy their execution authority, but it should borrow the idea of a visible task list where each worker has status, model, tool steps, and artifacts.

### Repo Context

Continue and Cline show useful repo-local configuration patterns. SpiritOS should prefer repo-owned provider/check configuration only when Source Proxy can validate it and Cartographer can log the outcome.

### Task Queue

AionUi and Codex App suggest a queue-oriented workspace. SpiritOS should add task history and active-worker lanes around Source Proxy tasks, not around raw provider sessions.

### Approval UX

Cline and Goose provide the clearest vocabulary for permission modes. SpiritOS should expose modes such as `read_only`, `proposal`, and `approved_apply`, but keep actual authority in Source Proxy.

### Sandbox Model

SpiritOS should not inherit any external tool sandbox as final authority. Provider sandboxes can be useful as defense-in-depth, but Source Proxy remains responsible for allowed files, protected paths, diff review, and approval.

### Diff Review

Codex App and Cline are good references for human review flow. SpiritOS should keep diffs as first-class artifacts and require verifier/reviewer checks before approval controls appear.

### Test Running

Continue's repo-defined checks are the best idea to borrow. SpiritOS should model checks as explicit verifier plans attached to TaskSpec and Cartographer evidence.

### Logs And Replay

AionUi's visible tool steps are worth copying, but Source Proxy needs structured evidence packets rather than UI-only logs. Provider outputs should be replayable through task packets, stdout/stderr excerpts, final-message excerpts, and diff artifacts.

### Branch And Worktree Support

Codex App is the strongest reference for parallel worktrees. SpiritOS should not add this until commit/push governance and cleanup rules are explicit.

### Commit And Push Governance

SpiritOS already has the stronger posture: commit and push are separate gates. Do not weaken that by copying one-click external flows.

### Mobile Or Remote Controls

AionUi's remote-control concept is interesting but risky. SpiritOS should treat remote/mobile controls as review and notification surfaces first, not execution authority.

### Scheduled Tasks

AionUi and Codex background work are references for scheduling. SpiritOS should require scoped task specs, allowed files, and approval boundaries before any scheduled provider task exists.

### Local Model Support

AionUi's Ollama test showed the model matters: `llama3:latest` lacked tool support, `llama3.1:8b` was unreliable for the edit, and `qwen2.5-coder:7b` showed better tool-call behavior. SpiritOS should design a local Ollama adapter, but treat model/tool capability as probed evidence, not assumed capability.

### MCP Or Tool Protocol Support

Cline and Goose are useful references for MCP/extension ecosystems. SpiritOS should add tool surfaces only through allowlisted providers and Source Proxy policies.

### Integration Complexity

AionUi is too broad and GUI-dependent to become a core dependency. OpenCode, Goose, Codex CLI, Gemini CLI, and local Ollama are better references for a controlled provider layer because they can be wrapped or probed from Source Proxy.

## Direction

Build a SpiritOS-controlled CLI/provider layer instead of adopting AionUi.

Likely provider adapters:

- local Ollama adapter
- Codex CLI adapter
- Gemini CLI adapter
- optional API adapter later

All provider outputs must flow through:

- TaskSpec
- `allowed_files`
- diff preview
- verifier
- reviewer
- approval gate
- evidence capture
- Cartographer logging

## Decision

Use AionUi, Codex App, Continue, Cline, Goose, and OpenCode as references. Do not integrate them as the trust boundary.

SpiritOS should borrow:

- AionUi's workspace/model/provider UI patterns
- Codex App's parallel work/review mental model
- Continue's repo-defined checks
- Cline's Plan/Act split and approval language
- Goose's permission mode vocabulary
- OpenCode's provider-agnostic configuration posture

SpiritOS should keep:

- Source Proxy as the execution boundary
- deterministic path safety
- proposal-first provider outputs
- explicit approval before apply
- separate commit and push gates
- Cartographer as the progress/audit ledger

## Next Step

Proceed to Increment 11.0.3: Gap report.

Do not propose or build Spirit Cowork Console until the gap report shows which pieces are actually missing and worth building.
