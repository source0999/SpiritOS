# Plan 2 Phase 2.4 - Design Readiness

Status: GO

## Increment 2.4.1 - Design token/context packet

`build_design_context_packet` emits:

- `design_system_refs`
- `token_refs`
- `component_refs`
- `component_style_vocabulary`
- `ui_critique_packet`
- `design_to_coder_handoff`
- `blocked_states`

Live read-only check against `/home/source/SpiritOS`:

- `design`: `used`
- reason: `design_context_ready`
- refs found: `37`

Decision: GO.

## Increment 2.4.2 - Component/style vocabulary

Vocabulary includes:

- `layout_density`
- `component_reuse`
- `interaction_state`
- `visual_hierarchy`
- `responsive_fit`
- `token_alignment`

Test:

`test_design_packet_is_advisory_only_with_refs`

Decision: GO.

## Increment 2.4.3 - UI critique packet

The critique packet includes:

- safe task excerpt
- `critique_mode: advisory_only`
- `visual_evidence_status: path_refs_only`

Decision: GO.

## Increment 2.4.4 - Design-to-coder handoff

Handoff explicitly allows only advisory context:

- style vocabulary
- component references
- token references

It forbids:

- apply
- approval token
- provider call
- queue worker
- git mutation

Decision: GO.

## Increment 2.4.5 - Blocked states

If no design refs are found, Design returns:

- status: `blocked`
- reason: `design_context_unavailable`
- blocked state: `missing_design_refs`

Decision: GO.

## Phase Closeout

Phase 2.4 GO. Design can produce advisory packet context and clear blocked states without claiming apply authority.

