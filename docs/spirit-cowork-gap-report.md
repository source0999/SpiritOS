# Spirit Cowork Gap Report

Status date: 2026-05-18
Phase: 11.0.3
Branch: main

## Boundary

This is a gap report only. No proposal file was created, no source code was changed, and no provider implementation was started.

Evidence reviewed:

- Codex adapter trial and closeout: `docs/codex-real-task-trial.md`
- AionUi local toy-repo evaluation: `docs/aionui-reference-study.md`
- Agent wrapper comparison: `docs/agent-wrapper-reference-study.md`
- Existing `proxyCLI.md` Phase 11 plan

## Executive Summary

SpiritOS already has the right trust model: Source Proxy controls task specs, allowed files, diff review, verifier/reviewer flow, approval gates, evidence capture, commit gates, push gates, and Cartographer logging.

The main gaps are not the safety core. The main gaps observed during the detour are provider routing, worker orchestration, and a clearer multi-agent/operator console around the safety core.

Recommendation: close this detour as UX/reference research. Do not turn it into a new roadmap increment inside `proxyCLI.md`.

Do not integrate AionUi as a foundation. Borrow UX patterns only.

## What SpiritOS Already Does Better

| Area | Existing Strength | Evidence |
| --- | --- | --- |
| Trust boundary | Source Proxy owns task shape, path safety, diff review, approval, and evidence. | Codex adapter trial, 10.8 through 10.11 receipts. |
| Read-only/proposal posture | Codex work can be previewed without apply, commit, or push authority. | `docs/codex-real-task-trial.md` |
| Evidence capture | Codex evidence packets record task IDs, changed files, authority flags, HEAD, excerpts, and recommendations. | `source_proxy/codex/evidence.py` |
| Cartographer visibility | Codex evidence appears as read-only project context and audit events. | 10.11.1 receipt. |
| Blueprinter posture | Blueprinter receives Codex trial summaries as proposal-only drafts. | 10.11.2 receipt. |
| Commit/push governance | Commit readiness and push remain separate human approval gates. | 10.11.3 receipt. |
| External tool caution | AionUi was tested only against a toy repo and did not receive SpiritOS authority. | `docs/aionui-reference-study.md` |

## Gap Table

| Gap | Current State | Risk | Recommendation |
| --- | --- | --- | --- |
| Worker orchestration | Codex worker exists, but provider routing is not generalized. | Medium: adding UI before routing would show fake capability. | Reassess in production readiness review. |
| Provider adapters | Codex CLI adapter exists; Ollama/Gemini/API adapters are not implemented. | Medium: local model support is model-dependent and tools may fail. | Reassess in production readiness review. |
| Task queue | Work is visible through individual flows, but there is no unified queue of active/past provider tasks. | Low/medium: operator has to stitch state from logs and docs. | Reassess in production readiness review. |
| Multi-agent UI | Coding UI has evidence panel, but no unified cowork workspace. | Medium: easy to overbuild before backend truth exists. | Wait; no Cowork build is authorized. |
| Agent comparison | AionUi and wrapper comparison exist; no scored decision table by build priority. | Low: research is enough for direction, not enough for product scope. | Use this gap report as the decision point. |
| Live logs | Evidence excerpts exist, but provider tool steps are not yet a live timeline surface. | Medium: hard to debug long tasks without structured live steps. | Reassess before any new production plan. |
| Replay | Evidence packets are replayable at a summary level, but not full task replay. | Medium: full replay can be expensive and misleading if context changed. | Reassess before any new production plan. |
| Artifact shelf | Coding UI has artifact/evidence concepts, but provider artifacts are not unified across providers. | Low/medium. | Reassess before any new production plan. |
| Mobile controls | No SpiritOS mobile control layer for provider tasks. | High if it can execute actions remotely. | Wait; make mobile review-only first. |
| Notifications | No notification lane for provider completion or blocked approval. | Low. | Borrow later from AionUi/Codex App ideas. |
| Scheduling | No scheduled provider tasks. | High: scheduled writes can bypass human attention. | Wait until allowlists, approvals, and notification gates are mature. |
| Model fallback | No common fallback policy across providers. | Medium: failed provider calls may be retried unsafely. | Reassess before any new production plan. |
| Cost tracking | No shared cost/token accounting across providers. | Medium for API providers, lower for local Ollama. | Reassess before any new production plan. |
| Rollback UX | Rollback is documented guidance, not a first-class console flow. | Medium: rollback controls can become destructive if rushed. | Keep guidance-only until apply/commit gates are mature in UI. |
| Cross-project onboarding | Cartographer can discover project candidates, but provider tasks are not cross-project aware. | Medium/high: wrong root means wrong authority. | Require explicit workspace/project selection in provider layer. |

## Build, Borrow, Integrate, Or Wait

### Build

No build is authorized by this detour. Treat these findings as readiness-assessment inputs only.

### Borrow

- AionUi: workspace picker, model selector, permission dropdown, visible tool steps, provider configuration panel, history/task sidebar.
- Codex App: parallel task/worktree mental model and review flow.
- Continue: repo-defined checks and rules.
- Cline: Plan/Act language and explicit approval UX.
- Goose: permission mode vocabulary.
- OpenCode: provider-agnostic configuration posture.

### Integrate

Do not integrate AionUi. Do not start new provider integration from this report.

### Wait

- AionUi bridge.
- Spirit Cowork Console MVP.
- Scheduled provider tasks.
- Mobile execution controls.
- Worktree automation.
- Automatic model fallback that can write files.
- Any provider API adapter that can bypass local evidence capture.

## Recommended Next Step

The AionUi/Cowork review is closed as UX/reference research.

AionUi is not being integrated into SpiritOS right now. SpiritOS may borrow useful UI/UX ideas later, but this report does not authorize Phase 11 continuation, a provider-layer implementation plan, or a Cowork Console build.

The original `proxyCLI.md` plan should be treated as having reached its planned endpoint if the final planned item was 10.8.1.

Next step: freeze the completed proxyCLI baseline and run a current-state production readiness assessment before writing any new production plan.

## Manual Checks

```bash
cd /home/source/SpiritOS
git status --short
git diff --check
git diff -- docs/spirit-cowork-gap-report.md
```

Expected:

- only documentation changes are present
- no source code files changed
- no `_blueprints/proposals/spirit-cowork-console.md` file is created
- `git diff --check` has no output

## Final Recommendation

Freeze this detour.

Do not start Spirit Cowork Console, an AionUi bridge, provider adapter implementation, or any new roadmap phase from this report.

Next step: freeze the completed proxyCLI baseline and run a current-state production readiness assessment before writing any new production plan.
