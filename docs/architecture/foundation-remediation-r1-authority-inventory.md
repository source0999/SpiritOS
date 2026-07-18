# Foundation Remediation R1 Authority Inventory

Schema: `spiritos-foundation-remediation-r1-authority-inventory/v1`

Status values in this baseline are defects to repair. Presence of code or a test is
not proof of a production invocation.

| Surface | Current production caller | Current writer / owner | Baseline defect | Required canonical owner |
| --- | --- | --- | --- | --- |
| Cartographer proposal review | Next `/v1/cartographer/proposals/[id]/review` → Source Proxy review route | `proposal_reviews.review_blueprint_proposal` writes/unlinks JSON | caller actor/snapshot; no approval; response denies writes | server-owned proposal-review authority and transactional consumer |
| Cartographer coding selection | selection preview/operator/transfer routes; test-only orchestrator handoff | selection authority finalizes in transfer route | direct route synthesizes acknowledgements; downstream not proven | CodingOrchestrator consumes persisted selection and records transfer/consumption |
| SpiritFlix tags | `/api/spiritflix/videos/[itemId]/tags` | Jellyfin/tag writer | incomplete payload/state binding; no real issuance UI | SpiritFlix transactional mutation helper |
| SpiritFlix model | `/api/spiritflix/videos/[itemId]/model` | model metadata writer | model/known-set/result state incompletely bound | SpiritFlix transactional mutation helper |
| SpiritFlix face learning | `/api/spiritflix/videos/[itemId]/face-learning` | face-learning writer | review payload/result state incompletely bound | SpiritFlix transactional mutation helper |
| SpiritFlix smart rescan | `/api/spiritflix/library-smart-rescan` | scanner/analysis writers | recursion/force/files/state incompletely bound | SpiritFlix transactional mutation helper |
| SpiritFlix smart batch | `/api/spiritflix/admin/smart/batch` | batch filesystem/media writer | action/file set/result state incompletely bound | SpiritFlix transactional mutation helper |
| SpiritFlix analysis/actions | admin analysis/actions routes | admin filesystem/Jellyfin writer | incomplete bindings and finalization handling | SpiritFlix transactional mutation helper |
| Design writeback | approved-writeback runtime; no proven production issuer/caller | Obsidian note writer | write precedes successful finalization; copied acknowledgements; no rollback | preservation-only Design authority consumer with independent verification/evidence |
| Coding apply | `/v1/tasks/long-running/{id}/execute-approved` → approval gate | `execute_approved_long_running_task` | bypasses CodingOrchestrator; finalizes before verification | persisted CodingOrchestrator |
| Coding review | executor pre-apply verification | same executor call stack | acknowledgement label, not independent invocation | reviewer participant service |
| Coding verification | verification route | `record_post_apply_verification` | route bypasses orchestrator; copied identity | verifier participant service invoked by orchestrator |
| Coding anti-cheat | generation helpers | inline detector call | not a post-apply independent artifact consumer | anti-cheat participant service |
| Coding evidence | task snapshot/ignored e2e receipt | task module/harness | mutable, source-unbound, copied identity | evidence-recorder participant plus immutable closeout manifest |
| Approval identity | Python script and TS/Python adapters | SQLite authority | hard-coded campaign root and shared state namespace | registered-root runtime identity configuration |
| Task truth | Source Proxy SQLite and Next coding-runs JSON | two independent stores | contradictory decision-bearing states possible | Source Proxy/orchestrator; Next bounded read-only view/cache |

## Non-authorities preserved

- Cartographer may discover, map, propose, persist proposal metadata, and provide
  provenance. It may not own filesystem, Git, commands, queues, or coding mutation.
- Lane registry/contracts describe and validate authority boundaries; they do not grant
  a task approval.
- Frontend assertions, callback return values, and receipt labels do not create
  consumer authority or participation proof.
- Design work in R1 is security preservation only.
