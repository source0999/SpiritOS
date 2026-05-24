# Source Proxy Codex-Class Phase 6 Provider Status Inventory

status: Phase 6, Increment 6.1 receipt
date: 2026-05-22
scope: `/coding` model/provider switching contract

## Inventory Summary

Phase 6 starts from an honest-but-thin provider contract.

- `src/lib/coding/model-provider-status.ts` currently exposes two provider ids: `local` and `cloud`.
- `local` is the default visible intent and does not claim a provider call has run.
- `cloud` is unavailable unless `cloudConfigured: true` is explicitly supplied.
- `src/components/coding/CodingCommandCenterShell.tsx` uses the provider status helper for the current `/coding` shell.
- `src/components/coding/CodingAgentInterface.tsx` and `src/components/coding/CodingCockpitShell.tsx` contain older/provider-rich references such as Codex CLI, Codex proposal route, model diagnostics, model-not-configured blockers, and config-blocked routes.
- Existing approval-gate tests already guard model/provider blocked states such as `coder_model_not_configured`, `local_model_unavailable`, `codex_binary_not_found`, and `codex_route_live_execution_not_enabled`.

## Provider Truth Table

| Provider lane | Current display truth | Runtime authority | Required Phase 6 behavior |
| --- | --- | --- | --- |
| Local AI | Default route intent only | No apply, commit, or push authority from switching | May be shown as default intent; actual route use must be proven after a call |
| Cloud AI | Unavailable unless explicitly configured | No external call, apply, commit, or push authority from switching | Must stay unavailable without config and must not imply a provider call ran |
| Codex worker | Present in older cockpit/agent contracts as proposal/evidence route | Proposal/evidence only | Must not arm approval or apply merely because Codex is selected |
| Future providers | Mentioned in older manual handoff language | None | Must be shown as future/unavailable until a safe configured route exists |

## Safety Findings

- Provider switching currently changes visible intent only in the command-center shell.
- No Phase 6 inventory finding requires auth, env, config, package, server, external API, apply, commit, push, or worktree changes.
- Missing configuration must continue to mean unavailable, not usable.
- Codex worker status must remain proposal-only unless a separate human-approved apply path is explicitly satisfied later.

## Increment Check Result

Codex ran the Phase 6.1 inventory grep and baseline status. The repo remains dirty from pre-existing work; no unrelated dirty files were touched.

Next increment: Phase 6, Increment 6.2: Honest Provider Switching UI Contract.
