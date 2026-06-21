# F10 Status

**Stage:** F10 - Full cleanup requalification
**Status:** NOT_STARTED
**Verdict:** pending
**Depends on:** F01, F02, F03, F04, F05, F06, F07, F08, F09

## Frozen artifacts
- `acceptance-contract.json` - frozen at P1. Battery includes taxonomy tests,
  all 19 failure classes, anti-cheat negative corpus, parity, brain-switch
  dry-run, no unapproved provider-call proof, decomposition holdouts,
  benchmark-tailoring scan, receipt/trace compatibility, apply/recovery,
  focused and bounded Python tests, lint, typecheck, build, canonical `/coding`
  tests, bounded smoke if available, Plan 2 and Plan 3 operators, Headroom
  checks, protected-path checks, dirty-tree checks, and `git diff --check`.
- `holdout-manifest.json` - frozen at P1. Cross-stage holdouts cover tailoring,
  no unapproved API, receipt compatibility, contract hashes, protected paths,
  fallback honesty, and no stamped PASS.

## Baseline
F10 may start only after F01-F09 are internally GO and committed. At F10 start,
record the cleanup HEAD, all F-stage commit SHAs, and the frozen contract hashes.

## Increments
- 10.1 - assemble battery harness and run backend battery.
- 10.2 - run frontend/operator/scope/anti-cheat battery.
- 10.3 - write secondary-review handoff, set `READY_FOR_SECONDARY_REVIEW`, and stop.

## Gate results / Caveats
No F10 gates have run. Set A/B/C remain forbidden. Old Set A rerun remains
post-review and Britton-approved only.

## Stop rule
On any red required battery item, skipped test, hidden fallback, unapproved API,
protected-path edit, benchmark-tailored production branch, contract hash
mismatch, or missing raw evidence, F10 is NEEDS_FIX or BLOCKED_ENV/BLOCKED_HUMAN
as appropriate. F10 may not self-accept.
