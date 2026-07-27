# Campaign Contradiction Matrix

| ID | Evidence A | Evidence B | Reconciliation | Effect |
| --- | --- | --- | --- | --- |
| C-01 | Worktree manifest expected Source Proxy `918a347f` | Named checkout was `594d66ef...` plus `.spirit-backups` | Manifest is stale for that checkout; preserve both facts | Recorded divergence; do not write there |
| C-02 | Dirty main is the visible SMB/source runtime | Current accepted/pending chain is C0 `bbe195111` -> C1 `4e5772182` -> C2 `1641ddb1` | Runtime identity and campaign authority are different questions | Main runtime cannot validate this candidate |
| C-03 | C2 implementation/tests are complete | Acceptance matrix says operator pending | Implementation completion is not campaign acceptance | Blocks C3-C6 and live JCode trial |
| C-04 | Historical remote receipts refer to campaign refs | C2 and qualification branches currently have no upstream; C2 remote ref absent | Historical publication may have been true; current remote state diverged | No push/merge; local evidence only |
| C-05 | Historical Campaign 3 design checkout appears current by name | Corrected extended-lane tag/checkout is later and clean | Treat design checkout as historical, corrected checkout as later historical proof | Neither is current Gate B authority |
| C-06 | Campaign 3.5 path resembles a worktree | It is a separate Git repository absent from main worktree metadata | Preserve as independent historical evidence | Never borrow its state |
| C-07 | Historical Campaign 4 means `/coding` UI | Current Gate B Campaign 4 means Scout/Obsidian causal integration | Same label, different scope | Both remain paused/not started |
| C-08 | Extended-lane registry names production callers | Only normal call site found is the explicit `extended-lanes` proof endpoint | Registry intent exceeds current core-lifecycle wiring | Classify partial, not fully active |
| C-09 | Model registry names multiple challengers | Qwen14B/Ornith are benchmark-prep, Gemma/Hermes advisory, cloud future | Registration is not live selection | Do not claim availability |
| C-10 | JCode has a safety classifier | Normal agent tool execution calls the registry directly; `request_permission` is ambient-only | Safety design is not a universal enforcement boundary | Live write trial blocked pending external containment |
| C-11 | JCode exposes a harness API | Permission response is unsupported and session listing is partial in the bridge | Sidecar API is incomplete for Proxy authority | Reject persistent sidecar now |
| C-12 | User requests Terra High integration | No canonical Terra High component exists in tracked current/planning code | Treat it as downstream intent | No product integration claim |

No contradiction required mutation of an existing campaign artifact. The safe
resolution is an isolated, disabled qualification annex based on C2's candidate
HEAD, with no campaign advancement.
