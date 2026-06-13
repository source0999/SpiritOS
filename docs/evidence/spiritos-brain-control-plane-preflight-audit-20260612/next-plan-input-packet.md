# Next Plan Input Packet

This is not the implementation plan.

This packet is the input Britton can use later to authorize a plan. No revamp implementation plan or Codex implementation prompts were created in this audit.

## Future Plan Should Solve

- Turn scattered Source Proxy, `/coding`, Cartographer, evidence, and memory/context systems into one cognitive control-plane loop.
- Make the loop explicit: sense -> understand -> remember -> prioritize -> plan -> choose worker -> act -> verify -> learn.
- Promote Obsidian only to the trust level it can safely support.
- Separate runtime GO from product behavior PASS.
- Define the canonical context packet and canonical result/verdict schema.
- Make worker selection evidence-aware and approval-gated.
- Build Hippocampus v0.1 without polluting memory.

## Future Plan Must Not Do

- Do not make Obsidian authoritative before metadata, freshness, evidence links, and approval boundaries exist.
- Do not enable automatic Obsidian write-back without Britton approval.
- Do not loosen model/provider/spend/apply/git gates.
- Do not treat docs-only plans as working code.
- Do not mark product behavior PASS from artifact existence alone.
- Do not start hidden workers or multi-lane execution without explicit approval.

## Proposed Plan Title

SpiritOS Hippocampus v0.1 And Cognitive Control Plane Readiness Plan

## Proposed High-Level Phases Only

1. Canonical truth model: define result labels, context packet schema, and authority matrix.
2. Hippocampus v0.1 read-only memory: Obsidian + evidence docs + durable runs as separate source classes.
3. Cerebellum v0.1: product behavior verifier fixtures and false-positive blockers.
4. Thalamus/Basal Ganglia v0.1: context-aware routing and worker selection policy.
5. Feedback loop v0.1: approval-gated memory summary/write-back previews.
6. Integration proof: dry-run packets first, then controlled local proofs only after approval.

## Proposed Obsidian Role

Initial role: read-only advisory memory.

Obsidian should provide curated long-term context summaries with source paths, confidence, freshness, and evidence links. Evidence docs and durable run store remain proof-of-record. Obsidian write-back should be approval-gated and previewed as note diffs.

## Open Questions For Britton

- Should Obsidian be read-only memory first, approval-gated write-back memory, or not promoted yet?
- Which real Obsidian vault should be trusted, if any, beyond `data/design-vault`?
- Should evidence docs remain the only authoritative proof trail?
- What memory categories should never be written automatically?
- Should local model failures be stored as memory after every run or only after human-reviewed summaries?
- Which current lanes are allowed in the first control-plane proof: local only, Codex preview, API with approval, or manual handoff only?

## Decision Points Needing Approval

- Obsidian trust mode.
- Obsidian vault path.
- Required note schema/frontmatter.
- Memory write-back approval workflow.
- Whether context-source readiness should affect route choice now or remain advisory.
- Canonical PASS/FAIL/GO/NO-GO schema.
- Whether to repair existing test failures before any architecture work.

## Explicit Obsidian Decision

Should Obsidian be read-only memory first, approval-gated write-back memory, or not promoted yet?
