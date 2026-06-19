# Plan 2/6 - Complete Subsystem Integration

Status: `PLAN_WRITTEN_NOT_STARTED`. Plan gate: `BLOCKED_PENDING_PLAN_0_COMPRESSION_DECISION`.

This plan is written but not started. GLM may execute it only after Britton approval for this exact plan. Codex reviews independently and must return NEEDS_FIX rather than silently patching GLM work.

## Phase 2.1 Mac live worker execution

- live capability before: established by previous phase verdict, never assumed from docs.
- live capability after: must be strictly greater than before or the phase cannot close.
- canonical route used: `/coding` -> `CodingCockpitShell` -> Next v1 route -> Source Proxy canonical handler unless Plan 0 records a Britton-approved replacement.
- real subsystem invoked: named per increment.
- real output consumed: downstream event and state fields required.
- operator-visible difference: route/result/status visibly changes when the subsystem succeeds or fails.
- all increment checks to rerun: focused tests, JSON validation, operator script, git status, forbidden-state scans.
- cross-increment contract checks: state/event schema, evidence budget, no duplicate machinery, no fake GO.
- deep Codex review: required at phase close.
- compression-trigger evaluation: required before phase close.

### Increment 2.1.1

- increment ID: `2.1.1`
- brain stage: `2`
- user-visible value: one required subsystem becomes honest, traceable, and decision-bearing in the canonical workflow.
- current defect: live integration is unproven or historically contradicted.
- exact current files/symbols to inspect: src/app/api/coding/mac-worker/route.ts, src/lib/mac-worker/*, scripts/mac-worker/*, source_proxy/decision/scout_research.py, source_proxy/decision/research.py, scout/src/scout, backend/docker-compose.yml
- proposed files allowed to change: future GLM may change only files named by this increment after approval; no changes are authorized by this packet.
- proposed new files, clearly marked NEW_PROPOSED: only files named by future approved increment.
- forbidden paths: unrelated Source Proxy, Next/frontend, Cartographer, Obsidian, Mac worker, Scout, model lane, verifier, systemd, Docker, runtime script, media, commit, push, and service files outside the approved increment.
- implementation behavior: implement the phase capability with real invocation, consumption, decisive failure, and no preview-only substitute
- input contract: real upstream task state, current source, and trace identifiers; no fixture substitution.
- output contract: typed output with `task_id`, `trace_id`, `invocation_event_id`, output hash, and status.
- downstream consumer: canonical task state, phase verifier, and /coding operator surface.
- focused automated checks: focused unit tests for touched modules plus JSON/schema checks for new contracts.
- real live proof: future live canonical-route proof with task_id, trace_id, invocation event, consumer event, changed state fields, and focused checks.
- Codex Quick Gate: verify scope, focused checks, live invocation, downstream consumption, forbidden-state scan, and causal identifiers.
- phase-boundary deep review assertions: no preview/advisory/read-only completion, no unconsumed output, no skipped required lane, no parallel state engine.
- rollback: disable the new integration point and return to the previous canonical route without deleting evidence.
- commit boundary: one focused implementation commit in future GLM work; no commit in this planning task.
- dependencies: previous increment GO, required runtime availability, Britton decisions where listed.
- hard stop conditions: protected path, credential/auth conflict, first Obsidian write, first Mac write, authority expansion, new framework proposal, or missing causal proof.
- GO criteria: invocation event and consumer event appear in one trace and failure changes the final route or verdict.
- forbidden fake-GO conditions: code exists, route exists, schema exists, status says available, packet created, preview success, advisory packet, fixture/mock success, unconsumed output, skipped lane, backend substitute output.
### Increment 2.1.2

- increment ID: `2.1.2`
- brain stage: `2`
- user-visible value: one required subsystem becomes honest, traceable, and decision-bearing in the canonical workflow.
- current defect: live integration is unproven or historically contradicted.
- exact current files/symbols to inspect: src/app/api/coding/mac-worker/route.ts, src/lib/mac-worker/*, scripts/mac-worker/*, source_proxy/decision/scout_research.py, source_proxy/decision/research.py, scout/src/scout, backend/docker-compose.yml
- proposed files allowed to change: future GLM may change only files named by this increment after approval; no changes are authorized by this packet.
- proposed new files, clearly marked NEW_PROPOSED: only files named by future approved increment.
- forbidden paths: unrelated Source Proxy, Next/frontend, Cartographer, Obsidian, Mac worker, Scout, model lane, verifier, systemd, Docker, runtime script, media, commit, push, and service files outside the approved increment.
- implementation behavior: implement the phase capability with real invocation, consumption, decisive failure, and no preview-only substitute
- input contract: real upstream task state, current source, and trace identifiers; no fixture substitution.
- output contract: typed output with `task_id`, `trace_id`, `invocation_event_id`, output hash, and status.
- downstream consumer: canonical task state, phase verifier, and /coding operator surface.
- focused automated checks: focused unit tests for touched modules plus JSON/schema checks for new contracts.
- real live proof: future live canonical-route proof with task_id, trace_id, invocation event, consumer event, changed state fields, and focused checks.
- Codex Quick Gate: verify scope, focused checks, live invocation, downstream consumption, forbidden-state scan, and causal identifiers.
- phase-boundary deep review assertions: no preview/advisory/read-only completion, no unconsumed output, no skipped required lane, no parallel state engine.
- rollback: disable the new integration point and return to the previous canonical route without deleting evidence.
- commit boundary: one focused implementation commit in future GLM work; no commit in this planning task.
- dependencies: previous increment GO, required runtime availability, Britton decisions where listed.
- hard stop conditions: protected path, credential/auth conflict, first Obsidian write, first Mac write, authority expansion, new framework proposal, or missing causal proof.
- GO criteria: invocation event and consumer event appear in one trace and failure changes the final route or verdict.
- forbidden fake-GO conditions: code exists, route exists, schema exists, status says available, packet created, preview success, advisory packet, fixture/mock success, unconsumed output, skipped lane, backend substitute output.
## Phase 2.2 Scout and SearXNG real research

- live capability before: established by previous phase verdict, never assumed from docs.
- live capability after: must be strictly greater than before or the phase cannot close.
- canonical route used: `/coding` -> `CodingCockpitShell` -> Next v1 route -> Source Proxy canonical handler unless Plan 0 records a Britton-approved replacement.
- real subsystem invoked: named per increment.
- real output consumed: downstream event and state fields required.
- operator-visible difference: route/result/status visibly changes when the subsystem succeeds or fails.
- all increment checks to rerun: focused tests, JSON validation, operator script, git status, forbidden-state scans.
- cross-increment contract checks: state/event schema, evidence budget, no duplicate machinery, no fake GO.
- deep Codex review: required at phase close.
- compression-trigger evaluation: required before phase close.

### Increment 2.2.1

- increment ID: `2.2.1`
- brain stage: `2`
- user-visible value: one required subsystem becomes honest, traceable, and decision-bearing in the canonical workflow.
- current defect: live integration is unproven or historically contradicted.
- exact current files/symbols to inspect: src/app/api/coding/mac-worker/route.ts, src/lib/mac-worker/*, scripts/mac-worker/*, source_proxy/decision/scout_research.py, source_proxy/decision/research.py, scout/src/scout, backend/docker-compose.yml
- proposed files allowed to change: future GLM may change only files named by this increment after approval; no changes are authorized by this packet.
- proposed new files, clearly marked NEW_PROPOSED: only files named by future approved increment.
- forbidden paths: unrelated Source Proxy, Next/frontend, Cartographer, Obsidian, Mac worker, Scout, model lane, verifier, systemd, Docker, runtime script, media, commit, push, and service files outside the approved increment.
- implementation behavior: implement the phase capability with real invocation, consumption, decisive failure, and no preview-only substitute
- input contract: real upstream task state, current source, and trace identifiers; no fixture substitution.
- output contract: typed output with `task_id`, `trace_id`, `invocation_event_id`, output hash, and status.
- downstream consumer: canonical task state, phase verifier, and /coding operator surface.
- focused automated checks: focused unit tests for touched modules plus JSON/schema checks for new contracts.
- real live proof: future live canonical-route proof with task_id, trace_id, invocation event, consumer event, changed state fields, and focused checks.
- Codex Quick Gate: verify scope, focused checks, live invocation, downstream consumption, forbidden-state scan, and causal identifiers.
- phase-boundary deep review assertions: no preview/advisory/read-only completion, no unconsumed output, no skipped required lane, no parallel state engine.
- rollback: disable the new integration point and return to the previous canonical route without deleting evidence.
- commit boundary: one focused implementation commit in future GLM work; no commit in this planning task.
- dependencies: previous increment GO, required runtime availability, Britton decisions where listed.
- hard stop conditions: protected path, credential/auth conflict, first Obsidian write, first Mac write, authority expansion, new framework proposal, or missing causal proof.
- GO criteria: invocation event and consumer event appear in one trace and failure changes the final route or verdict.
- forbidden fake-GO conditions: code exists, route exists, schema exists, status says available, packet created, preview success, advisory packet, fixture/mock success, unconsumed output, skipped lane, backend substitute output.
### Increment 2.2.2

- increment ID: `2.2.2`
- brain stage: `2`
- user-visible value: one required subsystem becomes honest, traceable, and decision-bearing in the canonical workflow.
- current defect: live integration is unproven or historically contradicted.
- exact current files/symbols to inspect: src/app/api/coding/mac-worker/route.ts, src/lib/mac-worker/*, scripts/mac-worker/*, source_proxy/decision/scout_research.py, source_proxy/decision/research.py, scout/src/scout, backend/docker-compose.yml
- proposed files allowed to change: future GLM may change only files named by this increment after approval; no changes are authorized by this packet.
- proposed new files, clearly marked NEW_PROPOSED: only files named by future approved increment.
- forbidden paths: unrelated Source Proxy, Next/frontend, Cartographer, Obsidian, Mac worker, Scout, model lane, verifier, systemd, Docker, runtime script, media, commit, push, and service files outside the approved increment.
- implementation behavior: implement the phase capability with real invocation, consumption, decisive failure, and no preview-only substitute
- input contract: real upstream task state, current source, and trace identifiers; no fixture substitution.
- output contract: typed output with `task_id`, `trace_id`, `invocation_event_id`, output hash, and status.
- downstream consumer: canonical task state, phase verifier, and /coding operator surface.
- focused automated checks: focused unit tests for touched modules plus JSON/schema checks for new contracts.
- real live proof: future live canonical-route proof with task_id, trace_id, invocation event, consumer event, changed state fields, and focused checks.
- Codex Quick Gate: verify scope, focused checks, live invocation, downstream consumption, forbidden-state scan, and causal identifiers.
- phase-boundary deep review assertions: no preview/advisory/read-only completion, no unconsumed output, no skipped required lane, no parallel state engine.
- rollback: disable the new integration point and return to the previous canonical route without deleting evidence.
- commit boundary: one focused implementation commit in future GLM work; no commit in this planning task.
- dependencies: previous increment GO, required runtime availability, Britton decisions where listed.
- hard stop conditions: protected path, credential/auth conflict, first Obsidian write, first Mac write, authority expansion, new framework proposal, or missing causal proof.
- GO criteria: invocation event and consumer event appear in one trace and failure changes the final route or verdict.
- forbidden fake-GO conditions: code exists, route exists, schema exists, status says available, packet created, preview success, advisory packet, fixture/mock success, unconsumed output, skipped lane, backend substitute output.
## Phase 2.3 Design/browser and every other confirmed subsystem

- live capability before: established by previous phase verdict, never assumed from docs.
- live capability after: must be strictly greater than before or the phase cannot close.
- canonical route used: `/coding` -> `CodingCockpitShell` -> Next v1 route -> Source Proxy canonical handler unless Plan 0 records a Britton-approved replacement.
- real subsystem invoked: named per increment.
- real output consumed: downstream event and state fields required.
- operator-visible difference: route/result/status visibly changes when the subsystem succeeds or fails.
- all increment checks to rerun: focused tests, JSON validation, operator script, git status, forbidden-state scans.
- cross-increment contract checks: state/event schema, evidence budget, no duplicate machinery, no fake GO.
- deep Codex review: required at phase close.
- compression-trigger evaluation: required before phase close.

### Increment 2.3.1

- increment ID: `2.3.1`
- brain stage: `2`
- user-visible value: one required subsystem becomes honest, traceable, and decision-bearing in the canonical workflow.
- current defect: live integration is unproven or historically contradicted.
- exact current files/symbols to inspect: src/app/api/coding/mac-worker/route.ts, src/lib/mac-worker/*, scripts/mac-worker/*, source_proxy/decision/scout_research.py, source_proxy/decision/research.py, scout/src/scout, backend/docker-compose.yml
- proposed files allowed to change: future GLM may change only files named by this increment after approval; no changes are authorized by this packet.
- proposed new files, clearly marked NEW_PROPOSED: only files named by future approved increment.
- forbidden paths: unrelated Source Proxy, Next/frontend, Cartographer, Obsidian, Mac worker, Scout, model lane, verifier, systemd, Docker, runtime script, media, commit, push, and service files outside the approved increment.
- implementation behavior: implement the phase capability with real invocation, consumption, decisive failure, and no preview-only substitute
- input contract: real upstream task state, current source, and trace identifiers; no fixture substitution.
- output contract: typed output with `task_id`, `trace_id`, `invocation_event_id`, output hash, and status.
- downstream consumer: canonical task state, phase verifier, and /coding operator surface.
- focused automated checks: focused unit tests for touched modules plus JSON/schema checks for new contracts.
- real live proof: future live canonical-route proof with task_id, trace_id, invocation event, consumer event, changed state fields, and focused checks.
- Codex Quick Gate: verify scope, focused checks, live invocation, downstream consumption, forbidden-state scan, and causal identifiers.
- phase-boundary deep review assertions: no preview/advisory/read-only completion, no unconsumed output, no skipped required lane, no parallel state engine.
- rollback: disable the new integration point and return to the previous canonical route without deleting evidence.
- commit boundary: one focused implementation commit in future GLM work; no commit in this planning task.
- dependencies: previous increment GO, required runtime availability, Britton decisions where listed.
- hard stop conditions: protected path, credential/auth conflict, first Obsidian write, first Mac write, authority expansion, new framework proposal, or missing causal proof.
- GO criteria: invocation event and consumer event appear in one trace and failure changes the final route or verdict.
- forbidden fake-GO conditions: code exists, route exists, schema exists, status says available, packet created, preview success, advisory packet, fixture/mock success, unconsumed output, skipped lane, backend substitute output.
### Increment 2.3.2

- increment ID: `2.3.2`
- brain stage: `2`
- user-visible value: one required subsystem becomes honest, traceable, and decision-bearing in the canonical workflow.
- current defect: live integration is unproven or historically contradicted.
- exact current files/symbols to inspect: src/app/api/coding/mac-worker/route.ts, src/lib/mac-worker/*, scripts/mac-worker/*, source_proxy/decision/scout_research.py, source_proxy/decision/research.py, scout/src/scout, backend/docker-compose.yml
- proposed files allowed to change: future GLM may change only files named by this increment after approval; no changes are authorized by this packet.
- proposed new files, clearly marked NEW_PROPOSED: only files named by future approved increment.
- forbidden paths: unrelated Source Proxy, Next/frontend, Cartographer, Obsidian, Mac worker, Scout, model lane, verifier, systemd, Docker, runtime script, media, commit, push, and service files outside the approved increment.
- implementation behavior: implement the phase capability with real invocation, consumption, decisive failure, and no preview-only substitute
- input contract: real upstream task state, current source, and trace identifiers; no fixture substitution.
- output contract: typed output with `task_id`, `trace_id`, `invocation_event_id`, output hash, and status.
- downstream consumer: canonical task state, phase verifier, and /coding operator surface.
- focused automated checks: focused unit tests for touched modules plus JSON/schema checks for new contracts.
- real live proof: future live canonical-route proof with task_id, trace_id, invocation event, consumer event, changed state fields, and focused checks.
- Codex Quick Gate: verify scope, focused checks, live invocation, downstream consumption, forbidden-state scan, and causal identifiers.
- phase-boundary deep review assertions: no preview/advisory/read-only completion, no unconsumed output, no skipped required lane, no parallel state engine.
- rollback: disable the new integration point and return to the previous canonical route without deleting evidence.
- commit boundary: one focused implementation commit in future GLM work; no commit in this planning task.
- dependencies: previous increment GO, required runtime availability, Britton decisions where listed.
- hard stop conditions: protected path, credential/auth conflict, first Obsidian write, first Mac write, authority expansion, new framework proposal, or missing causal proof.
- GO criteria: invocation event and consumer event appear in one trace and failure changes the final route or verdict.
- forbidden fake-GO conditions: code exists, route exists, schema exists, status says available, packet created, preview success, advisory packet, fixture/mock success, unconsumed output, skipped lane, backend substitute output.
## Phase 2.4 Three-task complete subsystem acceptance

- live capability before: established by previous phase verdict, never assumed from docs.
- live capability after: must be strictly greater than before or the phase cannot close.
- canonical route used: `/coding` -> `CodingCockpitShell` -> Next v1 route -> Source Proxy canonical handler unless Plan 0 records a Britton-approved replacement.
- real subsystem invoked: named per increment.
- real output consumed: downstream event and state fields required.
- operator-visible difference: route/result/status visibly changes when the subsystem succeeds or fails.
- all increment checks to rerun: focused tests, JSON validation, operator script, git status, forbidden-state scans.
- cross-increment contract checks: state/event schema, evidence budget, no duplicate machinery, no fake GO.
- deep Codex review: required at phase close.
- compression-trigger evaluation: required before phase close.

### Increment 2.4.1

- increment ID: `2.4.1`
- brain stage: `2`
- user-visible value: one required subsystem becomes honest, traceable, and decision-bearing in the canonical workflow.
- current defect: live integration is unproven or historically contradicted.
- exact current files/symbols to inspect: src/app/api/coding/mac-worker/route.ts, src/lib/mac-worker/*, scripts/mac-worker/*, source_proxy/decision/scout_research.py, source_proxy/decision/research.py, scout/src/scout, backend/docker-compose.yml
- proposed files allowed to change: future GLM may change only files named by this increment after approval; no changes are authorized by this packet.
- proposed new files, clearly marked NEW_PROPOSED: only files named by future approved increment.
- forbidden paths: unrelated Source Proxy, Next/frontend, Cartographer, Obsidian, Mac worker, Scout, model lane, verifier, systemd, Docker, runtime script, media, commit, push, and service files outside the approved increment.
- implementation behavior: implement the phase capability with real invocation, consumption, decisive failure, and no preview-only substitute
- input contract: real upstream task state, current source, and trace identifiers; no fixture substitution.
- output contract: typed output with `task_id`, `trace_id`, `invocation_event_id`, output hash, and status.
- downstream consumer: canonical task state, phase verifier, and /coding operator surface.
- focused automated checks: focused unit tests for touched modules plus JSON/schema checks for new contracts.
- real live proof: future live canonical-route proof with task_id, trace_id, invocation event, consumer event, changed state fields, and focused checks.
- Codex Quick Gate: verify scope, focused checks, live invocation, downstream consumption, forbidden-state scan, and causal identifiers.
- phase-boundary deep review assertions: no preview/advisory/read-only completion, no unconsumed output, no skipped required lane, no parallel state engine.
- rollback: disable the new integration point and return to the previous canonical route without deleting evidence.
- commit boundary: one focused implementation commit in future GLM work; no commit in this planning task.
- dependencies: previous increment GO, required runtime availability, Britton decisions where listed.
- hard stop conditions: protected path, credential/auth conflict, first Obsidian write, first Mac write, authority expansion, new framework proposal, or missing causal proof.
- GO criteria: invocation event and consumer event appear in one trace and failure changes the final route or verdict.
- forbidden fake-GO conditions: code exists, route exists, schema exists, status says available, packet created, preview success, advisory packet, fixture/mock success, unconsumed output, skipped lane, backend substitute output.
### Increment 2.4.2

- increment ID: `2.4.2`
- brain stage: `2`
- user-visible value: one required subsystem becomes honest, traceable, and decision-bearing in the canonical workflow.
- current defect: live integration is unproven or historically contradicted.
- exact current files/symbols to inspect: src/app/api/coding/mac-worker/route.ts, src/lib/mac-worker/*, scripts/mac-worker/*, source_proxy/decision/scout_research.py, source_proxy/decision/research.py, scout/src/scout, backend/docker-compose.yml
- proposed files allowed to change: future GLM may change only files named by this increment after approval; no changes are authorized by this packet.
- proposed new files, clearly marked NEW_PROPOSED: only files named by future approved increment.
- forbidden paths: unrelated Source Proxy, Next/frontend, Cartographer, Obsidian, Mac worker, Scout, model lane, verifier, systemd, Docker, runtime script, media, commit, push, and service files outside the approved increment.
- implementation behavior: implement the phase capability with real invocation, consumption, decisive failure, and no preview-only substitute
- input contract: real upstream task state, current source, and trace identifiers; no fixture substitution.
- output contract: typed output with `task_id`, `trace_id`, `invocation_event_id`, output hash, and status.
- downstream consumer: canonical task state, phase verifier, and /coding operator surface.
- focused automated checks: focused unit tests for touched modules plus JSON/schema checks for new contracts.
- real live proof: future live canonical-route proof with task_id, trace_id, invocation event, consumer event, changed state fields, and focused checks.
- Codex Quick Gate: verify scope, focused checks, live invocation, downstream consumption, forbidden-state scan, and causal identifiers.
- phase-boundary deep review assertions: no preview/advisory/read-only completion, no unconsumed output, no skipped required lane, no parallel state engine.
- rollback: disable the new integration point and return to the previous canonical route without deleting evidence.
- commit boundary: one focused implementation commit in future GLM work; no commit in this planning task.
- dependencies: previous increment GO, required runtime availability, Britton decisions where listed.
- hard stop conditions: protected path, credential/auth conflict, first Obsidian write, first Mac write, authority expansion, new framework proposal, or missing causal proof.
- GO criteria: invocation event and consumer event appear in one trace and failure changes the final route or verdict.
- forbidden fake-GO conditions: code exists, route exists, schema exists, status says available, packet created, preview success, advisory packet, fixture/mock success, unconsumed output, skipped lane, backend substitute output.
## Plan-End Boundary

NEXT PLAN: Plan 3/6 - Durable Execution, Policy, Recovery, and Repair

STOP: No next-plan work may start from this plan.

PERMISSION REQUEST: Approve Plan 3/6 - Durable Execution, Policy, Recovery, and Repair.
