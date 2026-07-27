# Campaign Freeze Receipt

Verdict: `CAMPAIGN_FREEZE_VERIFIED_WITH_RECORDED_DIVERGENCE`

## Frozen authority

| Field | Verified value |
| --- | --- |
| Product scope | Source Proxy |
| Host | `source-server` via SSH alias `spirit` |
| Safe worktree | `/home/source/SpiritOS-source-proxy-jcode-qualification-20260726` |
| Branch | `codex/source-proxy-jcode-qualification-20260726` |
| Base/initial HEAD | `1641ddb1c71e6b364e98aa9aeff4b4719627d926` |
| Base relation | C0 `bbe195111` -> C1 `4e5772182` -> C2 `1641ddb1c` |
| Scoped status at freeze | clean |
| Campaign state | Campaign 2 implementation and negative proof complete; operator acceptance pending |
| Campaign 4 | paused; no change authorized |
| Frozen benchmark | `benchmarks/coder-backend-100/v1.1/`; not run or modified |

`VERIFIED FACT`: `git merge-base --is-ancestor` established the linear accepted
C0/C1 and pending C2 chain. `docs/architecture/campaign-2-evidence/campaign-2-acceptance-matrix-20260726.md:3`
records `IMPLEMENTATION_AND_NEGATIVE_PROOF_COMPLETE_OPERATOR_ACCEPTANCE_PENDING`.

`VERIFIED FACT`: the selected worktree was created from the pending C2 HEAD
because it contains the current campaign implementation while preserving all
numbered worktrees. This does not convert C2 into an accepted campaign.

## Integrity pins

| Artifact | SHA-256 |
| --- | --- |
| `benchmarks/coder-backend-100/v1.1/manifest.json` | `0d6ae09d9ffe885c437236b9a10afad50c49d38eac1a8a8d05b8f7471c7592f4` |
| `benchmarks/coder-backend-100/v1.1/tasks.json` | `d437ccd216d56661e16afba9fe2b81b2c15d142342af0fe3868d7ac84d625b53` |
| `benchmarks/coder-backend-100/v1.1/tasks.jsonl` | `84c00187b9cc3d1932dd2e9286c558c01091d799568d8d8dcc80f7c9cc06f0c6` |
| `benchmarks/coder-backend-100/v1.1/file-hashes.json` | `45b524f74063148b3e91630b4769957ab2a888fe0c0a4c1b34262c0a6841d1d9` |

The suite contains 100 tasks and was treated as a sealed oracle. No task text,
solution, expectation, or run output was exposed to JCode.

Machine receipt SHA-256:
`b38717ed1184466f7ac52f1aea446e82fa8e6f29cc5c3f9eca58816fc313b3de`.

## Recorded divergence

`VERIFIED FACT`: the manifest-named Source Proxy worktree expected
`918a347f`, while `/home/source/SpiritOS-source-proxy-20260711` was at
`594d66ef8280953af767a273d7c91be765d1a6eb` with untracked `.spirit-backups`.

`VERIFIED FACT`: `/home/source/SpiritOS` was on `master` at
`85dee8b59cce39afe1fbe7d674c066ccca1e6f13` with thousands of scoped and
unscoped changes. It was not borrowed, cleaned, staged, or used as the write
surface.

`VERIFIED FACT`: a historical Campaign 3 design checkout had one untracked
goal document, while the corrected extended-lane checkout at
`74ac367faf9a72c652061a5482c0180bb0b0c844` was clean. The separate historical
Campaign 3.5 repository was not silently treated as a worktree of the main repo.

`VERIFIED FACT`: current C2 and this qualification branch had no upstream, and
the historical C2 remote ref was not present at freeze time. This is recorded
as current remote divergence, not retroactively used to invalidate old receipts.

`BLOCKER`: the live daily runtime observed on dirty `master` returned `NO_GO`;
there is no live service identity attached to this qualification checkout.

## Commands

The freeze used read-only `hostname`, `uname`, `date`, `git worktree list
--porcelain`, scoped `git status --short`, `git rev-parse`, `git branch -vv`,
`git merge-base --is-ancestor`, `git tag --points-at`, `git ls-remote`, and
`sha256sum` commands through `ssh spirit`. Freeze observation began at
`2026-07-27T01:35:06Z`; this receipt was finalized after source audit at
`2026-07-27T02:28:53Z`.
