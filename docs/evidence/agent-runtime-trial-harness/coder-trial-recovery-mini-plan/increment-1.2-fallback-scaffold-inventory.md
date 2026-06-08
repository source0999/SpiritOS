# Increment 1.2 - Fallback and Scaffold Inventory

## Locations found

- `source_proxy/planning/bounded_create.py`
  - `bounded_create_replacement_content` maps exact known Agent Lab app routes to deterministic page content.
  - `_KNOWN_PAGE_SCAFFOLDS` includes `/agent-lab` and exact Coder 10-style child pages.
  - `_scaffold_from_app_page_path` can produce a generic Next app page for `src/app/**/page.tsx`.
  - Affects trial mode through `source_proxy/tasks/long_running.py` when Coder proposal generation falls back to deterministic bounded-create content.
  - Affects normal task composer as a future fallback/scaffold helper.

- `source_proxy/planning/architect.py`
  - `plan_task_deterministically` now checks bounded-create before long-task fallthrough.
  - Affects target/scaffold eligibility for bounded proposal tasks.
  - Not trial-only.

- `source_proxy/tasks/long_running.py`
  - `_deterministic_bounded_create_response` wraps bounded-create content as a Coder response.
  - `propose_coder_agent_diff_payload_from_plan` can use deterministic response before model, after blocked model output, or after validation retry failure.
  - `_mark_scaffold_or_fallback_provenance` records backend scaffold/fallback provenance.
  - `_trial_scaffold_or_fallback_used` blocks trial-mode PASS when scaffold/fallback provenance is present.
  - Markdown append fallback remains separate and is not a Coder trial PASS path.

- `src/lib/coding/durable-run-types.ts`, `src/lib/coding/durable-run-store.ts`
  - Durable row provenance fields persist trial source/trust state.

- `src/components/coding/CodingCockpitShell.tsx`
  - Trial result rows normalize and copy/display provenance from source-proxy diagnostics.
  - No-diff model response classification prevents provider-call-only PASS.

- `scripts/coder-frontend-acceptance-v2.js`
  - Frontend acceptance diagnostics changed in the dirty tree and should be treated as in-scope trial evidence support.

## Tailored to Coder 10 / Agent Lab

Known exact scaffold paths include:

- `src/app/agent-lab/page.tsx`
- `src/app/agent-lab/calculator/page.tsx`
- `src/app/agent-lab/cards/page.tsx`
- `src/app/agent-lab/counter/page.tsx`
- `src/app/agent-lab/form/page.tsx`
- `src/app/agent-lab/model-picker/page.tsx`
- `src/app/agent-lab/notes/page.tsx`
- `src/app/agent-lab/proxy-health/page.tsx`
- `src/app/agent-lab/theme/page.tsx`
- `src/app/agent-lab/todo/page.tsx`

## Self-check

- Every Coder trial-impacting fallback has file/function/caller/behavior recorded: yes.
- Normal task-composer impact separated from trial-mode impact: yes.
- Coder 10 / Agent Lab tailored scaffolds flagged: yes.
