# Code-Owned Packet Assembler Analysis - 2026-06-23

## Boundary

The current A2/A5/A9 failures come from trusting local models to author provenance-bearing packet fields. The runner should not ask a model to be the final packet notary. Code must own runtime truth, evidence provenance, source URLs, lane metadata, receipt/trace paths, fallback/degraded flags, anti-cheat flags, verifier flags, and the final JSON shell. The model may author only bounded decision body text.

## Field Ownership

Code-owned fields:

- run/task identity: `run_id`, `prompt_id`, `task_id`, route type
- lane truth: expected lane, candidate lanes, selected lane, model/provider/tool, local/api/cli distinction, provider availability, degraded lanes, fallback flags
- call truth: model call attempted, model call result/failure class, timeout/empty/parse/policy classification
- evidence provenance: source URLs, source hosts, source refs, evidence object shape, repo refs, Mac refs
- verification and safety: productive status/reasons, verifier flags, protected path result, anti-cheat flags, failure classification
- artifact paths: created/modified files, receipt path, trace path, redaction status
- final envelope: final JSON wrapping, required packet shell fields, human action flag

Model-owned fields:

- `decision_summary`
- `reasoning_summary`
- `risk_notes`
- `ambiguity_notes`
- `proposed_next_action`
- `action_intent` from a controlled enum
- optional confidence reason

Forbidden model-owned fields:

- source URLs, source refs, hostnames, provider identity, local/api truth, receipt/trace paths, anti-cheat flags, verifier flags, fallback flags, created/modified files, protected-path result, final verdict, final JSON envelope

## Evidence Table

| Prompt | Current model-authored failure | Which fields code should own | Which fields model may author | Proposed assembler behavior |
| --- | --- | --- | --- | --- |
| A2 | fabricated source host/URLs, missing local API distinction, non-JSON wrapping, weak action verb | evidence_items, source URLs/hosts, repo refs, local/API/CLI truth, safe MVP shell, handoff shell, validation envelope | browser-extension decision body, risk notes, next action | Code selects research/repo refs from collected evidence, inserts local API and MV3/native messaging contract terms from the existing contract, and uses model text only inside decision sentences. |
| A5 | fabricated `ollama.ai`, insufficient source refs, thin decisions, non-JSON wrapping | source refs/URLs, Mac refs, Dell/Mac/Windows role evidence, no-new-hardware/privacy contract shell, lane truth | workstation role decision body, risk notes, next action | Code blocks honestly if real research sources are absent; otherwise it assembles source/Mac/repo provenance from collected evidence and validates model text separately. |
| A9 | thin defaults/action verbs, previous fabricated/garbled tokens | source refs/URLs, local-tool comparison evidence, use-now/test-later/skip shell, lane truth | local-tool comparison decision body, risk notes, next action | Code owns comparison categories and provenance; model contributes concise recommendation language only. |

## Implementation Target

Create a code-owned packet assembler in the Stage 4R runner:

1. Ask the model for a bounded decision body only.
2. Parse a single JSON object if present; prose wrapping is recorded but not copied into the final packet.
3. Map `action_intent` only through a controlled enum.
4. Assemble evidence, source URLs, lane truth, handoff, quality self-check, and final JSON shell in code.
5. Validate the assembled packet with the existing validator.
6. Surface both `model_decision_body_status` and `code_owned_packet_shell_status` in receipts/debugger output.
