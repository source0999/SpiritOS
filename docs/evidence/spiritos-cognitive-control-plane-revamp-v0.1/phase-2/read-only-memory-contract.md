# Read-only Memory Contract

## Purpose

Phase 2 defines how SpiritOS may use existing Obsidian notes, evidence docs, and durable run records as read-only memory sources for the cognitive control plane.

This is an evidence-only contract. It does not implement a new memory service, does not change Source Proxy behavior, and does not write to Obsidian.

## Core Rule

Memory may inform context and risk, but memory is not approval, not proof by itself, and not an automatic learning loop.

## Allowed Read Sources

- `source_proxy/context/obsidian.py`
- `source_proxy/api/obsidian_context.py`
- `source_proxy/api/context_index.py`
- `source_proxy/api/context_inventory.py`
- `data/design-vault/**` when selected by existing safe Obsidian context rules
- `docs/evidence/**` as evidence docs
- `data/coding-runs.json` as durable run records
- Phase 1 truth contract and fixture requirements

## Forbidden Writes and Mutations

- No Obsidian write-back.
- No automatic memory updates.
- No `.env` or provider config changes.
- No generated benchmark artifact mutation.
- No production source changes from memory retrieval.
- No new worker starts.
- No provider/model calls.
- No git mutation.

## Memory Record Shape

Future memory adapters should emit records with:

- `source_type`: obsidian, evidence_doc, durable_run, truth_contract, fixture, repo_inventory.
- `source_path`: repo-relative path or safe external descriptor.
- `source_anchor`: heading, line, run ID, fixture ID, or receipt ID.
- `summary`: short operator-safe summary.
- `truth_label`: optional Phase 1 canonical label.
- `reason_codes`: stable reason codes when available.
- `evidence_strength`: Phase 1 evidence strength classification.
- `privacy_level`: public, internal, sensitive, redacted.
- `read_only`: must be true for Phase 2.
- `used_for`: context, risk, verifier input, route hint, or operator receipt.
- `not_authority_for`: approval, product PASS, worker start, provider spend, Obsidian write.

## Selection Rules

- Prefer recent, scoped, and directly relevant evidence over broad historical context.
- Prefer current repo evidence over stale memory when cheap to verify.
- Preserve raw evidence by reference instead of copying large payloads.
- Redact secret-shaped values in summaries.
- Keep Obsidian `.obsidian/**`, `private/**`, `secrets/**`, and `archive/**` excluded unless separately approved.
- Carry Phase 1 truth labels with evidence but do not promote weak evidence to PASS.
- Mark unavailable or skipped memory reads as `UNVERIFIED`, not PASS.

## Integration Requirement

Phase 3 may use this contract to build an intake/context router preview. Phase 3 must not duplicate the existing Obsidian or context inventory systems; it should wrap them and produce a preview packet used by tests, UI, or evidence reports.

