# F04 — Generic Local Packet Decomposition

## Goal
Decompose large local-model prompts into per-task-shape sub-packets that
validate independently — **generic** decomposition by task shape, never
benchmark-keyed. Makes A5/A9-style prompts locally satisfiable before any API
escalation is considered.

## Why
F3 can emit `LOCAL_DECOMPOSITION_RECOMMENDED`; F4 is the machinery that acts on
it. Without generic decomposition, large prompts hit a capability wall that gets
misread as "needs API" — the exact A5/A9 trap.

## Primary new dir / file
`source_proxy/decision/packet_templates/` (new); touches
`source_proxy/decision/prompt_packet.py` (430 lines).

## Task shapes (generic — frozen)
- multi-node resource planning
- current-tool comparison
- architecture planning
- implementation handoff
- research-backed recommendation

## Sub-packet contract
- use evidence IDs (not inlined substance)
- validate independently
- expose F1 failure classification
- record attempts
- no script-supplied substance (constitution §B/§D)

## Increments (≤12 source files)
1. **4.1** — `packet_templates/` with a generic decomposer keyed on task shape;
   a comparison-shape decomposer first (safe first patch); sub-packet validator;
   tests on **unseen** same-shape prompts.
2. **4.2** — remaining shapes; wire `prompt_packet.py` to use the decomposer when
   F3 recommends decomposition; regression references (A2/A5/A9) as tests only.

## Invariants
- **No benchmark-keyed logic.** A2/A5/A9 are regression references only.
- **No cloud/API models** in F4.
- Internal GO requires **generic improvement** on unseen same-shape prompts, not
  hardcoded success on known prompts.
- Decomposition must not worsen packets (if it does, monolithic is preferred and
  the stage reports NEEDS_FIX).

## Stop conditions
- Decomposition worsens packet quality on holdouts → NEEDS_FIX.
- Any benchmark-specific branch → automatic NEEDS_FIX (constitution §A).

## Rollback
Monolithic path (pre-F4). prompt_packet.py reverts to single-packet emission.

## Approval
Britton. Codex confirms generic-shape behavior + no benchmark keying.
