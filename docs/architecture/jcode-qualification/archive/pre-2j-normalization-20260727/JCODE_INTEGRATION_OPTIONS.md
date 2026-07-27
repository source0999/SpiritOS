# JCode Integration Options

Scores are 1 (poor) to 5 (strong) for this campaign. They compare architecture,
not current production eligibility. Option E remains the operational posture
until Option A's blockers close.

| Criterion | A Per-task CLI | B Persistent sidecar | C Embed/vendor | D Concepts only | E No integration |
| --- | ---: | ---: | ---: | ---: | ---: |
| Architectural fit | 5 | 3 | 2 | 4 | 3 |
| Authority preservation | 5 | 3 | 2 | 5 | 5 |
| Isolation | 5 | 2 | 2 | 4 | 5 |
| Observability | 4 | 4 | 5 | 4 | 1 |
| Raw evidence access | 4 | 4 | 5 | 4 | 1 |
| Cancellation | 4 | 4 | 5 | 4 | 5 |
| Timeout enforcement | 5 | 3 | 5 | 4 | 5 |
| Deterministic configuration | 5 | 3 | 4 | 5 | 5 |
| Local model compatibility | 4 | 4 | 5 | 4 | 1 |
| Stream/tool compatibility | 3 | 3 | 5 | 4 | 5 |
| Context control | 4 | 2 | 4 | 5 | 5 |
| Memory contamination risk | 5 | 1 | 3 | 5 | 5 |
| Command safety | 3 | 2 | 3 | 5 | 5 |
| Worktree isolation | 5 | 2 | 4 | 5 | 5 |
| Concurrency safety | 5 | 2 | 3 | 4 | 5 |
| Maintenance burden | 4 | 3 | 1 | 2 | 5 |
| Update risk | 4 | 2 | 1 | 4 | 5 |
| Supply-chain risk | 3 | 3 | 1 | 5 | 5 |
| License implications | 5 | 5 | 4 | 5 | 5 |
| Performance potential | 3 | 5 | 5 | 3 | 1 |
| Implementation complexity | 4 | 3 | 1 | 2 | 5 |
| Rollback simplicity | 5 | 3 | 2 | 4 | 5 |
| Campaign measurability | 5 | 4 | 3 | 4 | 1 |
| **Total / 115** | **99** | **67** | **76** | **99** | **98** |

## Evaluation

**Option A, per-task external CLI adapter:** selected design for qualification.
It has the cleanest process/worktree/JCODE_HOME boundary, simple rollback, and
paired-run measurability. It still requires external filesystem/network
containment and a complete result mapper.

**Option B, persistent sidecar:** rejected now. The pinned harness bridge returns
`permission_response not yet supported`, lists only its attached session, drops
unknown legacy events, and has an unresolved broken-pipe issue class. Persistent
state also increases contamination and authority ambiguity.

**Option C, embed/vendor crates:** rejected. The large multi-crate workspace,
default-build resource failure, update burden, and coupling would turn a
challenger experiment into a new platform. It offers no campaign evidence yet
that justifies this cost.

**Option D, concepts only:** retained fallback. It preserves authority best but
would not answer whether JCode itself improves coding performance. Use it only
for mechanisms independently worth adopting if Option A fails qualification.

**Option E, no integration:** current runtime posture and permanent fallback.
No live task may use JCode until C2 acceptance and the Option A remediations are
explicitly authorized and validated.
