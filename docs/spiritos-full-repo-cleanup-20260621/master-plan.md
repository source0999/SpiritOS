# Master Plan — F1–F10 Full-Repo Cleanup

Grounded in GLM full-repo audit §17 (verified at
`docs/full-repo-system-architecture-audit-20260621/glm-full-repo-audit-20260621.md:445`)
and the real source survey performed at P1-prep. Every file path below was
verified to exist (or be absent, where the stage *creates* it) on the cleanup
base. Line counts for the two concentration files were independently confirmed:
`source_proxy/api/decision.py = 7,971` and `source_proxy/tasks/long_running.py = 6,513`.

## Execution model (recap — full protocol in `dependency-map.md` + per-stage contracts)

For each stage: freeze acceptance-contract + holdout-manifest → hash → record in
status.json → capture baseline → execute one responsibility per increment (≤12
source files) → focused checks → compatibility compare → update artifacts → run
`operator-check.sh` → verdict `INTERNAL_GO_PENDING_SECONDARY_REVIEW` only if every
gate passes → commit exact paths → update status/handoff → verify clean tree →
auto-continue. Max 3 repair attempts per increment.

## Stage summary

| Stage | Title | Primary target(s) | Deps | Anti-cheat class |
|---|---|---|---|---|
| F1 | Failure taxonomy + debug receipts | new `source_proxy/diagnostics/status_codes.py`; wire qwen lane first; FIP0 receipt `failure_classification` | none | typed failure contract |
| F2 | Independent anti-cheat registry | new `source_proxy/verification/anticheat/` (copy, not move) | none | negative corpus, parity |
| F3 | Brain-switch verdict contract (recommendation-only, no API) | `decision/model_lanes.py`, `routing/litellm_router.py`, new `escalation_contract.py` | F1 | no handholding, no silent escalation |
| F4 | Generic local packet decomposition | `decision/prompt_packet.py`, new `packet_templates/` | F3 | no canned substance, generic shapes |
| F5 | Split decision transport from domain lanes | `api/decision.py` (7,971→ thin router) → new `decision/lanes/*` | F1 | no behavior change |
| F6 | Split long-running responsibilities | `tasks/long_running.py` (6,513→ engine/apply/trace/recovery/regression) | F1 (prefer F5) | preserve state machine |
| F7 | Coding UI shell cleanup (no deletion) | `src/components/coding/*`, `src/lib/coding/*`; canonical = `CodingCockpitShell` | shared contracts stable | no canonical replacement |
| F8 | Context / memory / Headroom / repomix consistency | `scripts/context/*`, `proxy_memory/`, headroom scripts, repomix configs | none (before F10) | honest fallback (tree-sitter) |
| F9 | Worker / tool adapters (typed contracts) | `decision.py` subprocess/urllib → lane fns; mac-worker contract | F1, F5 | bounded timeouts, redaction |
| F10 | Full cleanup requalification | tests, operator checks, tailoring scan, parity | F1–F9 | terminal gate |

## Per-stage detail (source-grounded)

### F1 — Failure taxonomy + debug receipts
- **Goal:** one canonical typed contract for all 19 failure classes (see
  `F01/acceptance-contract.json` for the frozen list); every lane emits a stable
  `reason_code`; FIP0 receipt gains a top-level `failure_classification`;
  failure event appears in causal traces; legacy string field retained for
  compatibility.
- **Why:** audit's #1 risk; closes the formatting-failure-vs-capability-failure
  ambiguity that misread A2/A5/A9. Unblocks honest verdicts downstream.
- **Primary new file:** `source_proxy/diagnostics/status_codes.py`
  (`diagnostics/` exists today with `gpu.py`; `status_codes.py` is absent — created here).
- **Wire:** qwen lane first (in `decision/model_lanes.py`), prove receipt
  compatibility, then expand to other lanes. Keep old free strings as the
  legacy compat field.
- **Invariants:** no change to final-status vocabulary; no change to
  `fake_go_detected`; no benchmark-ID branches; `UNKNOWN_NEEDS_INVESTIGATION`
  may not absorb a known class.
- **Stop:** if existing tests go red for non-new-field reasons → repair (≤3) then
  `NEEDS_FIX`.

### F2 — Independent anti-cheat registry
- **Goal:** standalone `source_proxy/verification/anticheat/` package with
  independent detectors guarding the system from outside.
- **Why:** independence by process, not just function. The system must not grade
  its own honesty.
- **Primary new dir:** `source_proxy/verification/anticheat/`
  (`verification/` exists with `contracts.py,deterministic.py,diff.py`; `anticheat/`
  absent — created here).
- **Method:** COPY existing selftests (4R2/4R4/4R7 lineage) — do not move; run
  legacy + new in parallel; require parity PLUS new negative cases.
- **Negative corpus (frozen before impl):** canned output, static-research-as-live,
  route-existence-as-integration, status-ping-as-behavior, repo-context-as-internet,
  fixture/mock-as-live, preview/advisory-as-executed, fallback-as-primary-success,
  renderer-created decisions, manual PASS/JSON manipulation,
  canned+consumer-event, unavailable-provider-as-success, summary/raw
  contradiction, benchmark-specific runtime branch, test-only production branch.
- **Invariants:** do not retire legacy behavior in the first increment.

### F3 — Brain-switch verdict contract
- **Goal:** a recommendation-only contract that emits one of
  `LOCAL_RETRY_RECOMMENDED / LOCAL_DECOMPOSITION_RECOMMENDED /
  LOCAL_MODEL_INSUFFICIENT / API_ESCALATION_RECOMMENDED / HUMAN_DECISION_REQUIRED`
  **after** bounded local failure, with full evidence — and **no real API call**.
- **Primary new file:** `source_proxy/decision/escalation_contract.py`.
- **Touches:** `decision/model_lanes.py` (835), `routing/litellm_router.py`.
- **Must record:** task shape, local attempts, formatting failures, validation
  failures, reasoning/capability evidence, configured/unconfigured lanes,
  privacy class, cost class, authority required, evidence IDs.
- **Prove (tests):** formatting failure ≠ capability failure; retryable local
  failure ≠ API recommendation; bounded repeated capability failure *can*
  recommend escalation; unavailable provider never reported available; **no
  provider call occurs**.
- **No escalation by task label. No A2/A5/A9 production branch.** Final provider
  policy stays Britton's decision.

### F4 — Generic local packet decomposition
- **Goal:** decompose large local-model prompts into per-task-shape sub-packets
  that validate independently — **generic**, not benchmark-keyed.
- **Primary new dir:** `source_proxy/decision/packet_templates/`. Touches
  `decision/prompt_packet.py` (430).
- **Task shapes:** multi-node resource planning; current-tool comparison;
  architecture planning; implementation handoff; research-backed recommendation.
- **Sub-packets:** use evidence IDs; validate independently; expose F1 failure
  classification; record attempts; no script-supplied substance.
- **Historical A2/A5/A9 are regression references only.** Internal GO requires
  generic improvement on unseen same-shape prompts, not hardcoded success.

### F5 — Split decision transport from domain lanes
- **Goal:** `api/decision.py` (7,971) → thin router; FIP0–FIP6 logic → cohesive
  `source_proxy/decision/lanes/{receipts,context,research,coder,verifier,trace}.py`.
  (`decision/lanes/` is absent today; created here.)
- **Method:** extract a pure helper/serializer first (FIP0 receipt serialize);
  add compatibility import; prove parity; switch canonical call; retire the old
  inline path exactly and only after parity proof.
- **Preserve (see compatibility contract):** route paths, request/response
  shape, FIP0–FIP6 semantics, receipt fields, trace/consumer behavior, final
  status, `fake_go_detected`, preview/advisory/write boundaries.
- **No line-count-only refactor. No new parallel engine.**

### F6 — Split long-running responsibilities
- **Goal:** `tasks/long_running.py` (6,513) → engine + `apply/` + `trace/` +
  `recovery/` + `regression/`. **Do not rewrite the state machine.**
- **Preserve:** transitions, apply authority, recovery idempotence,
  duplicate-action protection, causal ordering, consumer semantics, operator
  readback.

### F7 — Coding UI shell cleanup (no deletion, no canonical replacement)
- **Provisional canonical (from runtime import, verified):** `/coding`
  (`src/app/coding/page.tsx`) imports **`CodingCockpitShell`**. The final
  future-development canonical-shell decision remains Britton's.
- **Allowed:** classify shells (active/legacy/experimental); document status;
  extract shared types; extract API adapters/hooks; extract
  timeline/receipt/debug components; add reversible feature metadata.
- **Forbidden:** deleting any shell; replacing `/coding`; choosing between
  competing product behaviors → if required, stop `BLOCKED_HUMAN`.
- **Shells present:** `CodingAgentInterface.tsx`, `CodingCockpitShell.tsx`
  (canonical), `CodingCommandCenterShell.tsx` (exercised by its own test).

### F8 — Context / memory / Headroom / repomix consistency
- **Preserve audited truth:** Cursor occupied 8797 during audit; installed
  Headroom was a Linux venv; Windows Git Bash could not run it; Cursor must not
  be killed; tree-sitter is an honest fallback.
- **Goal:** make port/config/start scripts internally consistent across
  `scripts/context/headroom-check.sh`, `scripts/headroom-proxy-dev.sh`, repomix
  configs.
- **Do not claim Headroom active without:** health success AND `compressed=true`
  AND `tokens_saved > 0`.
- **If config/docs are fixed but runtime remains externally blocked:** record a
  minor environment caveat and `BLOCKED_ENV` for Headroom itself. Tree-sitter
  fallback keeps other work moving but cannot make Headroom GO.

### F9 — Worker / tool adapters (typed contracts)
- **Goal:** move direct `subprocess`/`urllib` behavior in `decision.py`
  (browser/qwen/ollama) behind typed lane adapters Cartographer can inventory;
  mac-worker contract cleanup.
- **Adapter contract:** request/result types, timeout, attempt count, failure
  classification (from F1), evidence reference, redacted logs, ownership metadata.
- **Preserve output/timing before retiring direct paths. No new engine.**

### F10 — Full cleanup requalification
- **Goal:** after F1–F9, run the complete requalification battery (see
  `F10/acceptance-contract.json`): taxonomy tests, failure-class tests,
  anti-cheat negative corpus, legacy/new parity, brain-switch dry-run, no-
  unapproved-API proof, generic decomposition holdouts, **benchmark-tailoring
  scan**, receipt/trace/consumer compatibility, apply/recovery tests, focused +
  bounded broader Python tests, lint, typecheck, build, canonical `/coding`
  tests, bounded non-battery browser smoke if available, Plan 2 + Plan 3
  operators, Headroom/fallback contract, protected-path checks, dirty-tree
  checks, `git diff --check`.
- **Do NOT run Set A/B/C. Do NOT use known battery prompts for acceptance.**
- **Old Set A is rerun only after independent review + Britton approval.**

## Notes on test infrastructure (from P1-prep survey)

- Pytest has **no config** (no `pytest.ini`/`pyproject.toml`/`conftest.py`); runs
  with defaults. `source_proxy/tests/` has 115 test files.
- `package.json`: `test` (vitest), `test:coding-regression` (one pytest pack),
  `lint` (eslint .), `typecheck` (tsc --noEmit), `build` (next build --webpack),
  `check` (lint+typecheck+build).
- Stages that add commands must do so without inventing a new engine or replacing
  canonical scripts; additions are explicitly labeled and reversible.
