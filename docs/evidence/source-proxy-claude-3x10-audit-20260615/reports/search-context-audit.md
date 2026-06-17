# Search & Context Audit (evidence-based)

Date: 2026-06-16 (UTC). Basis: 30-row battery receipts + source inspection.

## Summary

The battery prompts did not request current information, so the search lanes were correctly
INACTIVE. Context lanes (Cartographer/Obsidian/Design) are read-only and were not counted as
coder success. No false `used`, no silent omission. The honesty of these lanes is GOOD; their
ACTUAL CONTRIBUTION to acceptance is near zero (advisory, non-gating).

## Per-lane truth (30 rows)

| Lane | Status across battery | Honest? | Notes |
|---|---|---|---|
| Scout | `skipped` 30/30 | Yes | `search_needed=False` (no current-info); diagnostics gate is honest |
| SearXNG | `skipped` 30/30 | Yes | same; receipt guard forces `used`->`failed` without a real provider call |
| Repo research | not surfaced as `used` | Yes | repo-first only fires on `needs_codebase_context`/research-recommended |
| Cartographer | advisory, read-only | Yes | real repo map; `can_apply/commit/push/worker=false`; not route owner |
| Obsidian | advisory, read-only | Yes | needs `data/design-vault`; typically skipped; secret redaction in excerpts |
| Design | advisory, read-only | Yes | globs design docs/components; skipped when refs absent |
| Mac worker | `skipped` (hardcoded stub) | Honest-but-cosmetic | never invoked; no capability behind it |
| TinyFish | `skipped` (deferred) | Yes | correctly deferred; not created |
| xersearch | `skipped` (missing alias) | Yes | correctly absent; not created |

## Gating reality

Context/search lane outcomes did not affect any verdict. Even when an advisory MODEL lane
failed (Gemma ReadTimeout), the GO stood. So "integrated context" is real plumbing but NOT a
gate on acceptance: a row passes on Qwen + structural deterministic + Hermes verifier alone.

## Search quality risks (source)

- `research.py::run_local_research_preview`: a SearXNG exception returns `[]`, discarding
  already-gathered repo+scout sources (latent context-loss bug). Not exercised by the battery
  (search not needed), but real.
- Repo research is a FIXED file allowlist (`REPO_RESEARCH_PATHS`) with hand-tuned scoring —
  narrow context selection.
- Scout default timeout 500ms — fragile under load.

## Recommendations

1. Make context-need a first-class classification recorded per row, and let a REQUIRED context
   lane's failure downgrade the verdict (no decorative lanes).
2. Fix the SearXNG-exception-discards-sources bug.
3. Add at least a few current-info battery rows in future runs to exercise Scout/SearXNG truth
   under real provider calls (this battery deliberately did not, to isolate coding behavior).
4. Either implement the Mac-worker lane or relabel it `not_implemented` instead of `skipped`.
