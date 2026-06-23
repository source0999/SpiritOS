# Merge Readiness - 2026-06-23

## Scope

Local-only integration merge of `cleanup/full-repo-20260621` into a branch based on current `master`.

## Heads

- master HEAD: `428792e5bf7fbb7caf57bfcf5e6effc28fcb6127`
- cleanup HEAD: `fdce5c8daa86c857fcfad3b13cb94b19b73f600f`
- merge-base: `ea7aac94d65ab8e06717efeb57399e514772815b`

## Master-Only Commits

- `428792e5` docs: preserve SpiritFlix mobile benchmark evidence
- `a9554366` feat: add SpiritFlix mobile benchmark fast path

These are the expected divergent SpiritFlix/mobile benchmark commits and must be preserved.

## Cleanup-Only Commits

- `fdce5c8d` Fix repo explainability review nits
- `eacbef81` Improve SpiritOS repo explainability and context pack docs
- `01c47791` Write visible context copy to main repo root
- `1b46581f` Write visible Repomix context copy at repo root
- `ec64f28a` Clarify Repomix context output location
- `649ae08a` Repair Headroom Linux compression runtime
- `a054ff25` Repair Headroom context compression wiring
- `f22c39f9` Refresh cleanup secondary-review state
- `eee61415` Prepare SpiritOS cleanup branch for GLM audit
- `60a9631f` Add typed SpiritOS worker and tool adapter contracts
- `63ec6daf` Clarify SpiritOS context and Headroom fallback contract
- `0306cc03` Clarify and split SpiritOS coding UI shell helpers
- `770ed0d0` Split Source Proxy long-running task helpers
- `18f5a1a4` Split Source Proxy decision lane helpers
- `f2c864e7` Add SpiritOS local packet decomposition
- `588e0ff5` Add SpiritOS brain-switch verdict contract
- `6cc39168` Add SpiritOS anti-cheat detector registry
- `b483cc5c` Add SpiritOS failure taxonomy

## Risk

Risk level: medium. The branch topology is expected, but the diff spans Source Proxy diagnostics, context tooling, repository explainability docs, and SpiritFlix mobile benchmark work. Source Proxy and docs conflicts may be resolvable by preserving both sides. Any non-obvious SpiritFlix/mobile benchmark conflict requires a human stop.

## Merge Strategy

Create `integration/cleanup-plan3-debug-20260623` from current `master`, merge `cleanup/full-repo-20260621` with `--no-ff --no-commit`, preserve the two master-only SpiritFlix/mobile benchmark commits, preserve cleanup F1-F10/F10R/explainability/headroom/docstring fixes, resolve only obvious documentation or additive source conflicts, then run the requested merge validation before committing.
