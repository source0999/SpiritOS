# Stage 4R5 Contract Alignment

## What was misaligned

- A2 packet validation accepted source and safe-MVP evidence, but the renderer did not preserve exact raw source URLs in the final `Source:` lines and could pair decisions with unrelated source facts.
- A5 packet generation saw Mac evidence, but the validator did not give the model a clear shared contract for exact `mac:<key>` refs and role/cost/privacy decisions.
- A9 used one live research query, so a zero-source provider response became an environment block without the requested query-variant coverage.

## Shared contract fix

- `PACKET_CONTRACTS` now defines required rendered sections, raw source refs, repo refs, Mac refs, prompt-specific terms, and final grader expectations for A2/A5/A9.
- The packet prompt includes the same contract, the validator enforces it, and the renderer uses decision evidence refs to choose the exact raw source/repo/Mac evidence it renders.
- A9 now attempts the approved live query variants through the same research/provider path and writes all attempts to raw evidence.

## Why this does not weaken the grader

- The existing hardened grader still computes `final_status`, `fake_go_detected`, materiality, prompt-specific gates, and blocker status after rendering.
- The change raises the upstream packet bar and preserves evidence in the rendered output; it does not remove any final grader check.

## Why this is not canned output

- Decisions still come from the live model packet generated from current research, repo context, and Mac evidence.
- The renderer formats validated packet fields and raw evidence references; it does not invent recommendations or flip statuses.
