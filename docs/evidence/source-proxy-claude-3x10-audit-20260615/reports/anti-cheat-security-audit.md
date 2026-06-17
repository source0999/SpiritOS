# Anti-Cheat & Security Audit (evidence-based)

Date: 2026-06-16 (UTC). Basis: 30-row battery + source inspection + runtime receipts.

## Anti-cheat: battery behavior (runtime)

| Check | Result | Evidence |
|---|---|---|
| Hardcoded prompt-specific payload as success | NOT triggered | 0 `hardcoded_used`; no `coder_no_changes_needed`/`deterministic_agent_trials_ui_test_preview`/trial bundles in any of 30 receipts |
| Preview-only/read-only lane counted as integration | No | Productive GO required FIP-5 result + qwen used + deterministic; context lanes are read-only and not counted as coder success |
| Old artifact-only path as scoring authority | No | All 22 GOs are `GO: fip5_...`; 0 `preview_only_go` (foundation/fip3) accepted |
| Qwen used for planning/verification | No | Qwen role = coder; planning=Gemma, critique=Hermes-critic, verify=Hermes-verifier (separate functions) |
| Hermes verifier acting as pre-coder critic | No | Distinct lanes; verifier is post-code only |
| Gemma/Hermes failure hidden behind GO | Recorded but NON-GATING | `s2-10-health` gemma `failed (ReadTimeout)` -> still `GO: fip5`; visible in `model_errors`, not hidden, but does not downgrade verdict |
| SearXNG/Scout `used` without provider evidence | No | Scout/SearXNG `skipped` 30/30 (no current-info requested); receipt has guard forcing `used`->`failed` without a provider call |
| Trace diverges from receipt | No | 30/30 trace verdict == receipt verdict |
| Protected path touched | No | 30/30 changed files inside disposable root |
| Malformed Qwen output applied | No | Output contract validated; proxy never applies diffs |
| Private hidden reasoning displayed | PARTIAL | operator_trace embeds raw Qwen output excerpt (see receipt-trace-audit.md) |
| Hidden commit/push/stage/apply/worker | No | `anti_tailoring_status` false 30/30; only receipt JSON written |

## Anti-cheat: codebase liabilities (source, dormant in this run)

- `source_proxy/api/decision.py::_product_trial_feature_already_satisfied_payload` (~L3449):
  matches exact target paths (`visible-result-badge.ts`, `reversible-trial-prompts.ts`,
  `CodingCockpitShell.tsx`) + task phrases + file-content substrings to return a synthetic
  "already satisfied" no-op. Prompt-fitted. Reachable when `trial_recover_already_satisfied`
  is sent or via the legacy path.
- `_agent_trials_ui_test_coder_diff_payload` (~L4732): inserts a LITERAL hardcoded test diff
  for a specific prompt phrase + anchor, "generated without model execution".
- `_dummy_*`/`_realistic_reversible_*` builders in `_bounded_coder_diff_or_stub` (~L3326):
  canned payloads served when FIP-4 is DISABLED (default). `_fip4_qwen_enabled()` defaults OFF,
  so a proxy started without env flags serves these.
- VERDICT: these did not fire in the battery (disposable targets, no flags, FIP-4 on), but they
  are live prompt-fitted/scaffold code in the production module and must be quarantined.

## Security / vulnerability

| Area | Posture | Evidence |
|---|---|---|
| Protected paths | STRONG | `safety/paths.py`: blocks `..`, absolute/drive/UNC, `%`-encoding, dotfiles, secret markers (.env/.pem/.key/secret/token/credential/id_rsa) |
| Path traversal | DEFENDED | Above + exact-match allowlist `_fip4_path_allowed`; 30/30 in-scope |
| Secrets | REDACTED in context | `_safe_excerpt`/`_safe_context_excerpt` redact emails, sk- tokens, key/token/password assignments; Obsidian excludes private/**, secrets/** |
| .env / certs / keys / source_proxy/data | NOT touched | battery never targeted them; secret-shape block proven in prior env-trap receipt |
| Local network services | local-only | Ollama 11434, SearXNG 8080, Scout 8077; no cloud |
| Auth boundary | WEAK | `/v1/decisions/fip0-receipts/{latest,run_id,trace}` are unauthenticated and linked from `/coding`; expose raw_prompt + raw model output excerpts |
| Shell execution | BOUNDED | Only `git status --short` (fixed args, 5s); plus `_ensure_fresh_repomix` runs `npx repomix`/`npm run` with fixed args, no user interpolation |
| Model-output injection | BOUNDED | Strict parse; diffs rejected; output NOT applied |
| Search/context injection | MEDIUM (latent) | Local search/Scout snippets feed the coder packet; inert today because output is unapplied; add canary tests before any apply stage |
| Trace leakage | MEDIUM | raw Qwen output excerpt in operator_trace; raw prompt in receipts |
| Stale/reused workspace | OBSERVED | concurrent on-disk edits to `long_running.py`/`package.json`/etc. mid-run without proxy restart |

## Top anti-cheat/security fixes

1. Quarantine `_product_trial_feature_already_satisfied_payload`, `_agent_trials_ui_test_coder_diff_payload`,
   `_dummy_*`/`_realistic_*` behind a test-only flag; `/coding` must refuse them.
2. Add a structured `coder_path` field (`fip4_real|legacy_stub|trial`) + `productive: bool` so
   no legacy/scaffold path can be read as productive.
3. Strip raw model output from FIP-6 operator_trace; auth-gate receipt/trace endpoints.
4. Preflight must assert FIP-4/5 enabled (default-off means default = scaffold path).
