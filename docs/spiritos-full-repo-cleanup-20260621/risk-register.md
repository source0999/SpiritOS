# Risk Register — F1–F10 Cleanup

Ranked. Each entry: risk · likelihood · impact · mitigation · owning stage(s).

## R1 — Behavior drift on public receipt/trace contracts (HIGH impact)
- **Likelihood:** medium. **Impact:** high (would invalidate every downstream
  consumer and the Plan 3 verdict surface).
- **Where:** F5 (decision.py split), F6 (long_running split), F9 (adapters).
- **Mitigation:** frozen `compatibility-and-rollback-contract.md`; per-stage
  byte-for-byte or normalized-JSON parity tests; receipt shape, FIP0–FIP6
  semantics, `trace_id`, `consumer_event_id`, `fake_go_detected`, apply/recovery
  behavior must be unchanged. Any drift → stage NEEDS_FIX.

## R2 — Anti-cheat regression / graded honesty (HIGH impact)
- **Likelihood:** low–medium. **Impact:** high (the whole point of cleanup).
- **Where:** F2 (new registry), F3 (brain switch), F10 (terminal scan).
- **Mitigation:** F2 freezes negative corpus before impl; legacy + new run in
  parallel with parity gate; F10 benchmark-tailoring scan; constitution §3/§6.
  No default PASS, no stamped GO, no fallback-as-primary.

## R3 — Benchmark tailoring sneaks in (HIGH impact)
- **Likelihood:** medium (A2/A5/A9 are the exact tempting cases). **Impact:** high.
- **Where:** F3 (escalation), F4 (decomposition) — both touch the A2/A5/A9
  failure surface.
- **Mitigation:** F4 task shapes are generic (multi-node planning, comparison,
  architecture, handoff, recommendation) — not keyed to benchmark IDs; A2/A5/A9
  are regression references only; F10 tailoring scan over runtime paths;
  constitution §1. Any benchmark-specific production branch → automatic NEEDS_FIX.

## R4 — Silent fallback counted as primary success (HIGH impact)
- **Likelihood:** medium (Headroom is already a known BLOCKED_ENV). **Impact:** high.
- **Where:** F8 (Headroom), F9 (tool adapters).
- **Mitigation:** every fallback records primary path / failure class / fallback
  path / `fallback_used=true` / verdict effect / evidence ref (constitution §6);
  Headroom may not be GO without health+compressed+tokens_saved>0; tree-sitter
  keeps work moving but cannot prove Headroom active.

## R5 — Unapproved API/cloud call (HIGH impact, also a hard safety boundary)
- **Likelihood:** low. **Impact:** high (violates a task-level safety boundary).
- **Where:** F3 (brain switch).
- **Mitigation:** F3 is recommendation-only; tests assert no provider call
  occurs; unavailable provider never reported available; final provider policy is
  Britton's. F10 includes no-unapproved-API proof.

## R6 — Split-for-line-count refactor (MEDIUM impact)
- **Likelihood:** medium. **Impact:** medium (creates churn without cohesion gain).
- **Where:** F5, F6.
- **Mitigation:** splits are by responsibility/cohesion, not line count
  (coding-standard.md; constitution §E). Safe-first-patch is a pure extraction
  with parity proof before any canonical switch.

## R7 — Touching a protected path (HIGH impact)
- **Likelihood:** low. **Impact:** high (media/SpiritFlix/Jellyfin are out of scope).
- **Where:** any stage, but especially F8/F9 if they grep broadly.
- **Mitigation:** per-stage path guard; protected paths enumerated in
  `ownership-map.md`; dirty-path guard compares against breakpoint manifest every
  stage; protected-path check is an F10 gate.

## R8 — Lost/fabricated evidence (HIGH impact)
- **Likelihood:** low. **Impact:** high.
- **Mitigation:** constitution §10; `evidence-budget.md` defines what each stage
  retains; raw logs outside Git under recorded evidence root; SHA-256 of retained
  raw evidence; never summarize a command not run.

## R9 — Plan 3 / Set A drift during cleanup (MEDIUM impact)
- **Likelihood:** low. **Impact:** medium–high (would muddy the resume point).
- **Mitigation:** Set A/B/C never run during cleanup; old-plan queue untouched;
  resume point frozen in `resume-old-plan-handoff.md`.

## R10 — Self-acceptance (HIGH impact)
- **Likelihood:** medium (operator pressure to finish). **Impact:** high.
- **Mitigation:** constitution §7; every stage verdict is
  `INTERNAL_GO_PENDING_SECONDARY_REVIEW`; terminal state is
  `READY_FOR_SECONDARY_REVIEW`, never accepted; independent Codex + Britton required.

## R11 — P0 evidence-integrity caveat compounds (LOW–MEDIUM)
- **Likelihood:** low. **Impact:** medium.
- **Where:** the prior-audit XML checksum caveat (CAVEAT-PRIOR-AUDIT-XML).
- **Mitigation:** recorded in cleanup-state.json; flagged for Britton
  reconciliation; does not touch cleanup contracts; honesty preserved.
