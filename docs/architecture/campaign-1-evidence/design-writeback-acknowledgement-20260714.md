# Design writeback acknowledgement receipt

- Schema: `spiritos-campaign-1/design-writeback-acknowledgement/v1`
- Campaign/run: `spiritos-campaign-1` / `2026-07-14-ar003`
- Mutable source: `/home/source/SpiritOS-campaign-1-20260712`; protected source heads are the immutable values recorded in the Campaign ledger.
- Profile: focused production-route/unit contract; not browser or production-runtime evidence.
- Result: pass.

The server resolves the persisted Design preview before authenticated operator issuance. The canonical Design writer consumes that approval transactionally, writes only after its verified gate, and finalizes through the Approval Authority. The finalization contract creates design-writeback, reviewer, verifier, and evidence-recorder acknowledgements from the same server-issued approval binding and generation; callers cannot supply or alter acknowledgement values.

The durable evidence body contains only a redaction marker, acknowledgement consumer names, generation, result status, and one-way hashes of acceptance, target, and trace values. It contains no approval ID, preview ID, raw target, trace, acceptance value, credential, cookie, or secret.

Claim ceiling: AR-003 focused structural acceptance only. Final Phase 1 acceptance still requires the full truthful profile matrix and AR-001 reconciliation.
