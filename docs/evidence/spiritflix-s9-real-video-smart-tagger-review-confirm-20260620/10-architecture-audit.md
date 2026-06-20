# SpiritFlix S9 Architecture Audit

## Existing flow

Batch smart analysis already scanned video metadata, extracted sampled frames into `.spiritflix-admin/analysis-cache/frames`, wrote analysis sidecars, let the operator save review metadata, and exported approved metadata sidecars. S8.3 deliberately left visual content tagging disabled.

## S9 additions

- `visual-analysis.ts` sends cached frame samples to local Ollama (`gemma3n:e4b` by default).
- VLM responses are constrained to controlled vocabulary ids and stored as review-required sample tags plus `contentTagEvidence` with source `vlm`.
- The review pipeline writes scanner evidence, then local visual evidence, then rebuilds suggested tags and names from that sidecar evidence.
- The review UI now exposes a `confirmMetadata` action that writes approved tags and display-name overrides to `.spiritflix-admin/metadata`.
- Confirm remains metadata-only: no Level 2 execute path, physical rename, move, delete, Jellyfin mutation, restart, cloud API, or paid API.

## Confidence and review semantics

All visual tags from the local model are marked `reviewRequired: true`. Confirm only persists operator-reviewed tags/name fields to metadata sidecars.
