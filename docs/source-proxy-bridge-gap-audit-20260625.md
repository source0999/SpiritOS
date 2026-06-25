# Source Proxy Bridge Gap Audit Addendum - 2026-06-25

## Scope

Minimal bridge-gap addendum for the Plan 3 generic model contract recovery. This is
not a full Source Proxy product audit and does not start Set B/C or Plan 4.

## Finding

The bridge gap is not fake source acceptance, fake GO acceptance, shared grader state,
or A3-specific cheating. The current gap is the generic model contract for
research/planning work products:

- generic research prompts previously used a weaker local Ollama lane
- concrete decision detection was too narrow for normal planning verbs
- repeated live runs did not have an explicit nondeterminism classification
- latest tracked receipts were overwritten in place without per-run retention

## Recovery Coverage

The recovery implementation addresses the bridge gap by adding:

- a general concrete-decision vocabulary plus vague-line guard
- task-shape generic stabilized lane selection
- observable deterministic/near-deterministic lane metadata
- stability classification helpers
- per-run-id append-only receipt copies
- focused tests that preserve strict fake-source and fake-GO rejection

## Remaining Gap

The remaining gap is live stability proof, not unit-level contract coherence. The
focused test suite proves the generic contract helpers and anti-cheat guardrails, but
the first bounded A3 live proof was unstable:

- `run-20260625T035628Z`: `PASS`
- `run-20260625T040050Z`: `NEEDS_FIX`
- `run-20260625T040556Z`: `NEEDS_FIX`

The prompt contract was then tightened so generic research work products must emit
exact four-line research-to-decision blocks and must not substitute prose-only
`Evidence Used` bullets. The final bounded A3 proof improved to:

- `run-20260625T041716Z`: `PASS`
- `run-20260625T042249Z`: `BLOCKED_ENV` because live research returned no sources
- `run-20260625T042819Z`: `PASS`

Full Set A stability still should not run until A3 produces stable PASS across all
bounded repeats.

## Safety Boundaries Preserved

- No API/frontier call was added.
- No RouteLLM dependency was added.
- No A3 prompt-id branch was added.
- Set B/C was not run.
- Plan 4 was not started.
- SpiritFlix/media/Jellyfin runtime and media files were not touched by this recovery.
