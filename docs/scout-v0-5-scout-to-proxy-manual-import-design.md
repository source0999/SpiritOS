# Scout v0.5 Phase 5.1 Scout-to-Proxy Manual Import Design

status: planning/manual-controlled

Status date: 2026-05-20

This document designs the Scout-to-Proxy manual import bridge for Scout v0.5. It is planning only. It does not implement an import flow, does not call proxy intake, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not promote packets, does not approve promotions, does not apply code, does not commit, and does not push.

## Current Verified State

The latest manual gate confirmed:

- Scout health is `observing`, version `v0.1`.
- Discovery proposals return `mode: manual_approved_proposals`.
- Discovery proposals are `read_only: true` and `mutation_allowed: false`.
- Discovery proposal approval is required before `create_discovery_job`, `search-preview`, and `extract-candidates`.
- Packet promotion recommendations return `mode: manual_packet_promotion_recommendations`.
- Packet promotion recommendations are `read_only: true` and `mutation_allowed: false`.
- Packet promotion approval is required before `queue_promotion`, `approve_promotion`, and `proxy-memory-write`.
- Level 1 soak passes with `mutated: false`.
- Source count, candidate counts, discovery job count, and promotion queue remain stable during read-only checks.
- Auto-rank fields are visible for 18 source candidates and 44 packets.
- Warnings are empty.

This matches the Scout v0.5 manual-controlled path. Scout can rank and recommend. Scout still cannot import into proxy memory automatically.

## Existing In-Repo Pieces

The repository already contains pieces that matter for a future manual bridge:

- `scout/src/scout/packets/promotions.py` has a `finalize_approved_promotion` path that requires an approved promotion, a signing key, a `promote` verdict, and a proxy intake URL.
- `source_proxy/api/scout_intake.py` exposes `/v1/scout-intake/promotion` and verifies a Scout signature before accepting a promotion payload.
- `source_proxy/proxy_memory/scout_intake.py` writes an append-only intake log only when `SOURCE_PROXY_SCOUT_INTAKE_LOG` is configured.
- The proxy intake response says `applied: false` and `approved_proxy_action: false`.

These pieces are not enough to authorize automatic memory writes. They only show a possible signed append-only evidence path for a future manually approved import.

## Safety Boundary

Phase 5.1 must not:

- auto-promote packets
- finalize promotions automatically
- call `/v1/scout-intake/promotion`
- write proxy memory
- write coding context
- enable `SOURCE_PROXY_SCOUT_INTAKE_LOG` as part of Scout autonomy
- enable `SCOUT_PROMOTION_SIGNING_KEY` as part of Scout autonomy
- approve queued promotions
- reject queued promotions
- create discovery jobs
- run search preview
- extract candidates
- activate sources
- register hidden background workers
- add scheduled writes
- change service configuration
- apply code
- commit
- push
- self-promote Scout to a higher autonomy level

The bridge remains manual-controlled. A human must choose the packet, approve the promotion, explicitly request import, and review the resulting append-only record.

## Manual Import Shape

A future implementation should use three separate gates:

1. Recommendation gate
   - Scout shows packet promotion recommendations.
   - Output is read-only evidence.
   - No promotion queue row is created.

2. Promotion queue gate
   - Operator queues a packet for promotion by explicit action.
   - The packet remains in Scout.
   - No proxy memory write happens.

3. Proxy import gate
   - Operator explicitly imports one approved promotion.
   - The import writes an append-only evidence record only.
   - The record must include packet ID, promotion ID, verdict, payload hash, approved by, written at, and source provenance.
   - The record must not become active coding context automatically.

## Required Provenance

Every future import record must include:

- `packet_id`
- `promotion_id`
- `approved_by`
- approval timestamp
- Scout packet payload
- debugger verdict payload
- payload SHA-256
- source URI
- source trust label when available
- packet status at import time
- verdict decision at import time
- signing key identity or key version if available
- intake log path
- rollback note

The minimum rollback is removing or ignoring the append-only intake record by `promotion_id`. A later implementation may add a tombstone event instead of deleting the record.

## Expected Future Endpoint Contract

If Phase 5.1 later becomes implementation, the safest shape is a manual-only Scout endpoint or command with this contract:

- Method: `POST`
- Input: one approved `promotion_id`
- Required actor: explicit operator identity
- Preconditions:
  - promotion status is `approved`
  - verdict decision is still `promote`
  - payload hash still matches
  - signing key is configured
  - proxy intake URL is configured
  - proxy intake log is configured
- Output:
  - `imported: true` only after append-only intake succeeds
  - `applied: false`
  - `approved_proxy_action: false`
  - `rollback`: exact promotion ID and intake record handling

This endpoint must not be called by scheduler, worker, soak profile, discovery flow, auto-rank, packet recommendation, or UI render.

## Manual Checks For A Future Implementation

Before any implementation can be accepted, checks must prove:

- no import happens from GET requests
- no import happens from page render
- no import happens from recommendation generation
- no import happens from queueing a promotion
- import fails without explicit operator identity
- import fails without an approved promotion
- import fails unless verdict decision is `promote`
- import fails if payload hash changed
- import fails without signing key
- import fails without intake log configuration
- import writes exactly one append-only evidence record
- import does not write coding context
- import does not apply code
- import does not commit
- import does not push
- promotion recommendations remain read-only
- Level 1 soak still passes

## Debug Path

If a future manual import fails:

- Check the promotion status first.
- Check the verdict decision.
- Check the payload hash.
- Check `SCOUT_PROMOTION_SIGNING_KEY`.
- Check the proxy intake URL.
- Check `SOURCE_PROXY_SCOUT_INTAKE_LOG`.
- Check the proxy intake response.
- Check the append-only intake log for the promotion ID.
- Do not retry automatically.

## Rollback

This planning document can be removed with:

```bash
rm docs/scout-v0-5-scout-to-proxy-manual-import-design.md
```

If a future implementation writes an append-only intake record, rollback must be handled by promotion ID. Prefer a tombstone record over deletion once an audit log exists.

## Next Permission Gate

Operator approval is required before implementing any Phase 5.1 code. The recommended next increment is Phase 5.2: Manual Import Dry-Run Contract, which should validate one approved promotion payload without calling proxy intake or writing proxy memory.
