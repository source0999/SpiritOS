# Plan 5/14: Multimedia Work Chat Lanes Integration

PLAN:
Plan 5/14, Multimedia Work Chat Lanes Integration.

Evidence root:
`/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-5/`

Updated isolated prototype:
`/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html`

Global forbidden actions:
No media storage migration. No destructive browser storage changes. No provider calls. No hidden background workers. No cross-lane mutation. No new persistent storage writes. No production route/component/backend edits. No package install. No git mutation. No Cartographer mutation.

Shared read-only inventory:
- `/home/source/SpiritOS/src/app/chat/page.tsx` renders `SpiritTrinityChatShell`.
- `/home/source/SpiritOS/src/components/chat/*` includes Trinity shell, thread sidebar, folders, model selector, voice/TTS controls, workflow visualizer, message actions, and tests.
- Chat hooks inspected: `useChatThreads`, `useChatFolders`, `usePersistentChat`, `useSpiritChatTransport`.
- Chat risk: Dexie-backed thread/folder persistence and `useChat` provider transport exist in production hooks, so Plan 5 prototype must stay fixture-only.
- `/home/source/SpiritOS/src/app/media/page.tsx` renders `MediaExperience`.
- Media inventory includes `MediaExperience`, media types, demo catalog, browser/database read/write helpers, profile state, local media storage, migration, evidence, and many media tests.
- Media risk: production media surfaces include local profile state, browser database, playback progress, watchlist, migration, and write helpers, so Plan 5 prototype must not call them.

Shared checks:
```text
$ grep -En "Chat Work Lane|Thread/Folder Context|Media Work Lane|Media Catalog Status|Chat/media lane evidence|No provider send|No thread write|No storage write|No media migration" docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html
632: Chat Work Lane
636: No provider send
637: No thread write
642: Thread/Folder Context
651: Media Work Lane
655: No storage write
656: No media migration
661: Media Catalog Status
736: Chat/media lane evidence

$ grep -En "fetch\(|XMLHttpRequest|localStorage|indexedDB|navigator\.sendBeacon|serviceWorker|new Worker|Worker\(|/v1/actions|/v1/tasks|useChat\(|sendMessage\(|createThread\(|deleteThread\(|updateThread|savePlayback|toggleWatchlist|saveProfile|resetProfile|writeProfile|db\." docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html
<no output>

$ node - <<'NODE'
<static assertion script checked 9 required lane labels and 21 forbidden call/storage patterns>
NODE
Plan 5 static assertions passed: 9 required lane labels present; 21 forbidden call/storage patterns absent.

$ git -C /home/source/SpiritOS status --short --branch --untracked-files=normal
## main...origin/main
?? docs/evidence/
?? docs/spirit-os-unified-proxy-coding-design-system-master-plan-of-plans-v0.1.md

$ git -C /home/source/SpiritOS diff --name-status
<no output>
```

## Increment 5.1.1

PLAN:
Plan 5/14.

PHASE:
Phase 5.1, Media/chat surface inventory.

INCREMENT:
5.1.1, Inventory `/home/source/SpiritOS/src/app/chat/page.tsx`.

Objective:
Route inventory.

Isolated proxy lane scope:
Read-only route inspection.

Allowed files or file zones:
Read-only `/src/app/chat/page.tsx`; Plan 5 evidence.

Forbidden files, paths, systems, and actions:
Edits, provider calls, storage writes, production mutation.

Exact work performed:
Read chat route file. It imports chat/dashboard styles and renders `SpiritTrinityChatShell`.

Required tests/checks:
`sed -n '1,220p' /home/source/SpiritOS/src/app/chat/page.tsx`.

Manual validation performed by Codex:
Chat route is readable and not edited.

Evidence artifact:
This file.

Stop conditions checked:
Unreadable: no.

Rollback or recovery note:
No rollback needed; read-only.

GO/NO-GO exit:
GO for Increment 5.1.1.

Next authorized increment only:
5.1.2.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 5.1.2

PLAN:
Plan 5/14.

PHASE:
Phase 5.1.

INCREMENT:
5.1.2, Inventory `/home/source/SpiritOS/src/components/chat/*`.

Objective:
Chat component inventory.

Isolated proxy lane scope:
Read-only component listing.

Allowed files or file zones:
Read-only `/src/components/chat/*`; Plan 5 evidence.

Forbidden files, paths, systems, and actions:
Component edits/provider calls.

Exact work performed:
Listed chat components and tests. Key surfaces include `SpiritTrinityChatShell`, `SpiritChat`, thread sidebar/folder components, model selector, mobile sheets, voice/TTS controls, workflow visualizer, and message utilities.

Required tests/checks:
`find /home/source/SpiritOS/src/components/chat -maxdepth 2 -type f -print`.

Manual validation performed by Codex:
Ownership is broad; Plan 5 uses fixture cards only.

Evidence artifact:
This file.

Stop conditions checked:
Ownership unclear enough to block: no, because no production edits.

Rollback or recovery note:
Gate production changes to later approval.

GO/NO-GO exit:
GO for Increment 5.1.2.

Next authorized increment only:
5.1.3.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 5.1.3

PLAN:
Plan 5/14.

PHASE:
Phase 5.1.

INCREMENT:
5.1.3, Inventory chat hooks.

Objective:
Persistence/provider risk inventory.

Isolated proxy lane scope:
Read-only hook inspection.

Allowed files or file zones:
Read-only `useChatThreads`, `useChatFolders`, `usePersistentChat`, `useSpiritChatTransport`.

Forbidden files, paths, systems, and actions:
Storage writes/provider calls.

Exact work performed:
Inspected hooks. `useChatThreads` and `useChatFolders` expose create/rename/delete/collapse writes when enabled. `usePersistentChat` manages thread/folder/message persistence. `useSpiritChatTransport` uses `useChat` transport and provider-oriented submit paths.

Required tests/checks:
Read-only `sed` inspections.

Manual validation performed by Codex:
Storage/provider risk is explicit; prototype must not import or call these hooks.

Evidence artifact:
This file.

Stop conditions checked:
Hidden storage dependency unclear: no; classified and gated.

Rollback or recovery note:
Read-only card only.

GO/NO-GO exit:
GO for Increment 5.1.3.

Next authorized increment only:
5.1.4.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 5.1.4

PLAN:
Plan 5/14.

PHASE:
Phase 5.1.

INCREMENT:
5.1.4, Inventory `/home/source/SpiritOS/src/app/media/page.tsx`.

Objective:
Media route inventory.

Isolated proxy lane scope:
Read-only route inspection.

Allowed files or file zones:
Read-only `/src/app/media/page.tsx`.

Forbidden files, paths, systems, and actions:
Edits/storage writes.

Exact work performed:
Read media route. It renders `MediaExperience` inside dashboard shell/floating nav wrappers.

Required tests/checks:
`sed -n '1,220p' /home/source/SpiritOS/src/app/media/page.tsx`.

Manual validation performed by Codex:
Media route is readable and not edited.

Evidence artifact:
This file.

Stop conditions checked:
Unreadable: no.

Rollback or recovery note:
No rollback needed; read-only.

GO/NO-GO exit:
GO for Increment 5.1.4.

Next authorized increment only:
5.1.5.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 5.1.5

PLAN:
Plan 5/14.

PHASE:
Phase 5.1.

INCREMENT:
5.1.5, Inventory `/components/media/*` and `/lib/media/*`.

Objective:
Media storage/catalog inventory.

Isolated proxy lane scope:
Read-only media listing and targeted inspection.

Allowed files or file zones:
Read-only media files; Plan 5 evidence.

Forbidden files, paths, systems, and actions:
Storage migration/writes.

Exact work performed:
Listed media component/lib files and inspected `MediaExperience`. Identified catalog, browser evidence, durable adapter, browser database, profile state, local media storage, migration, progress, watchlist, and evidence helpers.

Required tests/checks:
`find /home/source/SpiritOS/src/components/media /home/source/SpiritOS/src/lib/media -maxdepth 2 -type f -print`.

Manual validation performed by Codex:
Media has write-capable surfaces; Plan 5 uses display status only.

Evidence artifact:
This file.

Stop conditions checked:
Storage mutation required: no.

Rollback or recovery note:
Display status only.

GO/NO-GO exit:
GO for Increment 5.1.5.

Next authorized increment only:
5.2.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 5.1.1, 5.1.2, 5.1.3, 5.1.4, 5.1.5.
Evidence reviewed: chat route, chat components, chat hooks, media route, media components/libs.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Production chat/media surfaces include provider/storage writes; future work must stay read-only or be separately approved.
Decision: GO.
Next phase or increment: Phase 5.2, Increment 5.2.1.

## Increment 5.2.1

PLAN:
Plan 5/14.

PHASE:
Phase 5.2, Work-lane data contract.

INCREMENT:
5.2.1, Define chat lane contract.

Objective:
Chat lane display model.

Isolated proxy lane scope:
Fixture/read-only contract.

Allowed files or file zones:
Plan 5 evidence and prototype fixture display.

Forbidden files, paths, systems, and actions:
Provider/storage writes.

Exact work performed:
Defined fields: lane id, title, thread count, folder count, active profile/status, last activity, blocked actions, evidence refs.

Required tests/checks:
Contract review against chat hook risks.

Manual validation performed by Codex:
Contract does not require persistence or provider calls.

Evidence artifact:
This file.

Stop conditions checked:
Requires persistence: no.

Rollback or recovery note:
Disabled/read-only if persistence is needed.

GO/NO-GO exit:
GO for Increment 5.2.1.

Next authorized increment only:
5.2.2.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 5.2.2

PLAN:
Plan 5/14.

PHASE:
Phase 5.2.

INCREMENT:
5.2.2, Define media lane contract.

Objective:
Media lane display model.

Isolated proxy lane scope:
Catalog/status display contract.

Allowed files or file zones:
Plan 5 evidence and prototype fixture display.

Forbidden files, paths, systems, and actions:
Storage migration, catalog/profile/watchlist/progress writes.

Exact work performed:
Defined fields: lane id, catalog source, storage status, recent media label, profile status, playback status, blocked actions, evidence refs.

Required tests/checks:
Contract review against media storage risks.

Manual validation performed by Codex:
Contract is read-only and does not require media storage mutation.

Evidence artifact:
This file.

Stop conditions checked:
Write needed: no.

Rollback or recovery note:
Read-only/disabled status if write needed.

GO/NO-GO exit:
GO for Increment 5.2.2.

Next authorized increment only:
5.3.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 5.2.1, 5.2.2.
Evidence reviewed: chat and media lane contracts.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Contracts are fixture-level; no live data integration.
Decision: GO.
Next phase or increment: Phase 5.3, Increment 5.3.1.

## Increment 5.3.1

PLAN:
Plan 5/14.

PHASE:
Phase 5.3, Read-only media lane preview.

INCREMENT:
5.3.1, Add read-only media lane card.

Objective:
Media card.

Isolated proxy lane scope:
UI display in isolated prototype.

Allowed files or file zones:
`docs/evidence/unified-proxy-coding-design-plan-2/prototype/index.html`.

Forbidden files, paths, systems, and actions:
Storage writes.

Exact work performed:
Added Media Work Lane card with read-only catalog, no storage write, and no media migration badges.

Required tests/checks:
Static grep for `Media Work Lane` and `No storage write`; no forbidden storage/call patterns.

Manual validation performed by Codex:
Media card is fixture-only.

Evidence artifact:
Prototype and shared checks.

Stop conditions checked:
Storage write: no.

Rollback or recovery note:
Fixture-only.

GO/NO-GO exit:
GO for Increment 5.3.1.

Next authorized increment only:
5.4.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 5.4.1

PLAN:
Plan 5/14.

PHASE:
Phase 5.4, Chat-thread lane mapping.

INCREMENT:
5.4.1, Add read-only chat lane card.

Objective:
Chat card.

Isolated proxy lane scope:
UI display in isolated prototype.

Allowed files or file zones:
Prototype HTML.

Forbidden files, paths, systems, and actions:
Provider/storage writes.

Exact work performed:
Added Chat Work Lane card with no provider send and no thread write badges.

Required tests/checks:
Static grep for `Chat Work Lane`, `No provider send`, and no provider call patterns.

Manual validation performed by Codex:
Chat card is read-only fixture.

Evidence artifact:
Prototype and shared checks.

Stop conditions checked:
Provider call: no.

Rollback or recovery note:
Fixture-only.

GO/NO-GO exit:
GO for Increment 5.4.1.

Next authorized increment only:
5.4.2.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 5.4.2

PLAN:
Plan 5/14.

PHASE:
Phase 5.4.

INCREMENT:
5.4.2, Add thread/folder context display.

Objective:
Context display.

Isolated proxy lane scope:
UI read-only fixture.

Allowed files or file zones:
Prototype HTML.

Forbidden files, paths, systems, and actions:
Browser storage mutation.

Exact work performed:
Added Thread/Folder Context card with fixture counts/status and no create/rename/delete/reorder/collapse write.

Required tests/checks:
Static grep for `Thread/Folder Context`; no thread/folder write call patterns.

Manual validation performed by Codex:
Thread/folder context is read-only and does not call persistence hooks.

Evidence artifact:
Prototype and shared checks.

Stop conditions checked:
Storage write: no.

Rollback or recovery note:
Fixture-only.

GO/NO-GO exit:
GO for Increment 5.4.2.

Next authorized increment only:
5.3.2.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 5.3.2

PLAN:
Plan 5/14.

PHASE:
Phase 5.3.

INCREMENT:
5.3.2, Add media catalog/storage status display.

Objective:
Media status truth.

Isolated proxy lane scope:
UI read-only status display.

Allowed files or file zones:
Prototype HTML.

Forbidden files, paths, systems, and actions:
Catalog mutation and storage migration/write.

Exact work performed:
Added Media Catalog Status card with fixture/manual source reference, storage unavailable for mutation, and no playback progress write.

Required tests/checks:
Static grep for `Media Catalog Status`; no media write patterns.

Manual validation performed by Codex:
Media status is display-only.

Evidence artifact:
Prototype and shared checks.

Stop conditions checked:
Migration/write: no.

Rollback or recovery note:
Disabled state if storage is needed.

GO/NO-GO exit:
GO for Increment 5.3.2.

Next authorized increment only:
5.5.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 5.3.1, 5.4.1, 5.4.2, 5.3.2.
Evidence reviewed: chat lane card, thread/folder context, media lane card, media catalog status.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Cards are fixture-only and do not navigate live chat/media.
Decision: GO.
Next phase or increment: Phase 5.5, Increment 5.5.1.

## Increment 5.5.1

PLAN:
Plan 5/14.

PHASE:
Phase 5.5, Evidence drawer integration.

INCREMENT:
5.5.1, Add evidence drawer entries for chat/media.

Objective:
Receipt entries.

Isolated proxy lane scope:
UI display only.

Allowed files or file zones:
Prototype HTML and Plan 5 evidence.

Forbidden files, paths, systems, and actions:
Live writes.

Exact work performed:
Added `Chat/media lane evidence` entry to the evidence drawer.

Required tests/checks:
Static grep for `Chat/media lane evidence`.

Manual validation performed by Codex:
Evidence entry is display-only and does not write outside the lane.

Evidence artifact:
Prototype and shared checks.

Stop conditions checked:
Writes evidence outside lane: no.

Rollback or recovery note:
Fixture-only.

GO/NO-GO exit:
GO for Increment 5.5.1.

Next authorized increment only:
5.6.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 5.5.1.
Evidence reviewed: evidence drawer chat/media entry.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Evidence rows are static.
Decision: GO.
Next phase or increment: Phase 5.6, Increment 5.6.1.

## Increment 5.6.1

PLAN:
Plan 5/14.

PHASE:
Phase 5.6, Responsive behavior.

INCREMENT:
5.6.1, Add mobile collapse behavior.

Objective:
Narrow layout.

Isolated proxy lane scope:
Existing prototype responsive CSS.

Allowed files or file zones:
Prototype HTML/CSS.

Forbidden files, paths, systems, and actions:
CSS-wide polish.

Exact work performed:
Reused existing isolated prototype media queries that collapse layout to one column, stack chips, and stretch controls on narrow screens; added lane cards inside existing responsive containers.

Required tests/checks:
Manual source review of `@media (max-width: 900px)` and `@media (max-width: 560px)`.

Manual validation performed by Codex:
Lane cards live in `.side` grid and collapse with existing one-column responsive layout.

Evidence artifact:
Prototype source and this file.

Stop conditions checked:
Overlap by source inspection: no.

Rollback or recovery note:
Targeted prototype CSS fix only if screenshot proof later finds overlap.

GO/NO-GO exit:
GO for Increment 5.6.1.

Next authorized increment only:
5.7.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 5.6.1.
Evidence reviewed: responsive source inspection.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: No screenshot captured.
Decision: GO.
Next phase or increment: Phase 5.7, Increment 5.7.1.

## Increment 5.7.1

PLAN:
Plan 5/14.

PHASE:
Phase 5.7, Tests and manual validation.

INCREMENT:
5.7.1, Add tests.

Objective:
Automated proof.

Isolated proxy lane scope:
Ad hoc static Node assertion; no production test file.

Allowed files or file zones:
Read-only prototype input and evidence output.

Forbidden files, paths, systems, and actions:
Storage/provider calls and package changes.

Exact work performed:
Ran Node static assertion requiring 9 chat/media lane labels and forbidding 21 provider/storage/route/write patterns.

Required tests/checks:
Node assertion passed.

Manual validation performed by Codex:
No forbidden patterns were present.

Evidence artifact:
Shared checks.

Stop conditions checked:
Fail: no.

Rollback or recovery note:
Fix isolated prototype only if assertion fails.

GO/NO-GO exit:
GO for Increment 5.7.1.

Next authorized increment only:
5.7.2.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

## Increment 5.7.2

PLAN:
Plan 5/14.

PHASE:
Phase 5.7.

INCREMENT:
5.7.2, Add manual validation.

Objective:
Operator check.

Isolated proxy lane scope:
Manual/source review.

Allowed files or file zones:
Plan 5 evidence and prototype source.

Forbidden files, paths, systems, and actions:
Storage mutation/provider calls.

Exact work performed:
Reviewed lane cards, badges, evidence drawer, no-call/no-storage checks, status/diff, and responsive placement.

Required tests/checks:
Manual checklist by source and terminal output.

Manual validation performed by Codex:
Chat/media lanes are visible as read-only fixture cards; no navigation or mutation runs.

Evidence artifact:
This file.

Stop conditions checked:
Mutation/overlap by source inspection: no.

Rollback or recovery note:
Fix/gate future ambiguous controls.

GO/NO-GO exit:
GO for Increment 5.7.2.

Next authorized increment only:
5.8.1.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.

PHASE CLOSEOUT:
Completed increments: 5.7.1, 5.7.2.
Evidence reviewed: Node static assertion and manual validation.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: No browser navigation/screenshot proof captured.
Decision: GO.
Next phase or increment: Phase 5.8, Increment 5.8.1.

## Increment 5.8.1

PLAN:
Plan 5/14.

PHASE:
Phase 5.8, Closeout gate.

INCREMENT:
5.8.1, Closeout gate.

Objective:
Decide Plan 6 readiness.

Isolated proxy lane scope:
Evidence summary only.

Allowed files or file zones:
Plan 5 evidence and isolated prototype.

Forbidden files, paths, systems, and actions:
Further implementation without approval.

Exact work performed:
Summarized read-only lane proof and ran final status/diff/no-provider/no-storage checks.

Required tests/checks:
Shared checks above.

Manual validation performed by Codex:
Lanes display safely and do not mutate chat/media/provider/storage state.

Evidence artifact:
This file.

Stop conditions checked:
Storage/provider mutation: no.

Rollback or recovery note:
Return to offender if a future mutation appears; no git cleanup.

GO/NO-GO exit:
GO for Increment 5.8.1.

Next authorized increment only:
Plan 6/14, Phase 6.1, Increment 6.1.1 only if operator approves.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.

PHASE CLOSEOUT:
Completed increments: 5.8.1.
Evidence reviewed: full Plan 5 evidence packet and prototype checks.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Known risks: Plan 6 remains unauthorized until operator permission.
Decision: GO.
Next phase or increment: Plan 6/14, Phase 6.1, Increment 6.1.1 only if operator approves.

PLAN 5/14 CLOSEOUT:
Completed phases: 5.1, 5.2, 5.3, 5.4, 5.3 continuation, 5.5, 5.6, 5.7, 5.8.
Evidence reviewed: this packet, read-only inventories, updated isolated prototype, static feature grep, no-provider/no-storage/no-route grep, Node assertion, status/diff.
Main repo execution path untouched: Yes.
Cartographer soak untouched: Yes.
Forbidden actions avoided: Yes.
Dirty tree preserved without cleanup: Yes.
Known risks: No browser screenshot or live navigation proof was captured; Plan 5 is isolated static prototype evidence, not production chat/media integration.
Decision: GO.
Next authorized plan: Plan 6/14, Phase 6.1, Increment 6.1.1 only.
Permission request: Ask operator before starting Plan 6/14.
