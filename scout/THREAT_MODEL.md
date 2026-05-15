# Scout Threat Model

Scout reads untrusted public content and turns it into local intelligence packets. This document names the main threat categories for v0.1 and maps each one to a concrete mitigation phase.

## Threats And Mitigations

| Threat | Risk | Mitigations |
|---|---|---|
| Indirect prompt injection via README, AGENTS.md, .cursorrules, RSS item bodies, or extracted Markdown | External content may try to instruct an AI reader or override system behavior. | Phase 4.2 Tier 0 envelope wraps all untrusted content before LLM calls. Phase 5.2 Tier 1 regex screen flags likely injection text. Phase 5.4 Tier 3 LLM screen performs a second-pass injection check. |
| Malicious or typosquatted source repos | Scout may ingest misleading or hostile content from a lookalike source. | Phase 0.3 defines an allowlist. Phase 2.5 registry loading rejects non-allowlisted hosts and sources. |
| Stale information presented as current | Old releases, old docs, or old reports may be surfaced as if they are fresh. | Phase 5.2 adds a staleness flag with per-source TTL rules. Packet timestamps are preserved for consumers. |
| LLM hallucination in packet summaries or impact analysis | Summaries may contain claims not supported by the source text. | Phase 5.4 Tier 3 hallucination check compares summary claims against wrapped raw extracted text. |
| Resource exhaustion from very large pages, very large repos, or deeply paginated feeds | Scout could consume excessive CPU, memory, disk, or network budget. | `SCOUT_FETCH_MAX_BYTES`, request timeouts, and per-source poll budgets bound external fetches. Phase 2 polling persists state and rate-limit metadata. |
| License confusion from code snippets surfaced into proxy context | Copyleft or restricted content may be mixed into downstream context without warning. | Packet `entity_tags` includes detected SPDX identifiers when present. Phase 6 proxy bridge surfaces those identifiers in returned results. |

## OWASP LLM Top 10 Alignment

Scout v0.1 directly addresses OWASP LLM01, Prompt Injection, by treating all fetched source content as untrusted and requiring a Tier 0 envelope before any LLM interaction. Later debugger phases add deterministic and LLM-based screens for suspected injection attempts.

Scout v0.1 also addresses OWASP LLM08, Excessive Agency, by keeping Scout read-only outside `scout/data/`, forbidding execution of fetched code, forbidding Scout-initiated proxy calls, and requiring human approval before any Phase 7 promotion into proxy memory.

## Review Rule

Any future implementation choice that relaxes a mitigation above must update this document first. If the rollback for a mitigation cannot be tested, the mitigation is not complete.

## Implementation Choices

Phase 3 uses `tree-sitter==0.22.*` with `tree-sitter-languages==1.10.*`. This is Option A from the plan: a prebuilt grammar bundle for v0.1 so Scout can parse common repository languages without compiling grammars during the Docker build.

Phase 5 keeps `sentence-transformers` optional for the CPU-only v0.1 image. The debugger imports it lazily only when a packet reaches Tier 3 embedding storage; if the package is unavailable, the embedding subcheck records a skipped finding and the verdict still completes. This avoids pulling CUDA Torch wheels into the default Scout container and preserves the Phase 1 CPU-only decision.
