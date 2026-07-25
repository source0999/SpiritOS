# Campaign 0 Segment 0B - Base Construction Receipt

status: `SEGMENT_0B_SETUP_CANDIDATE`

This receipt records Segment 0B documentation and setup only. It does not mark
Campaign 0 complete, does not mark the base regression-green, does not repair
LumaCart, and does not authorize Segment 0C.

## Objective

Construct one isolated Campaign 0 implementation branch/worktree from pushed
Campaign 3.5 ancestry `ede643c7e18535125efde807d5937f265dcc75f9` while
preserving and explicitly deferring the unpushed `6616846d` changes.

## Segment 0A Evidence Corrections

- Dirty-path counts reported for `/home/source/SpiritOS` are timestamped
  observations only because that live checkout is actively changing. The
  Segment 0B pre-creation observation at `2026-07-25T22:42:45Z` was 4,842 whole
  worktree dirty paths.
- The previously reported `161 OpenAPI routes` value is `UNVERIFIED` for
  Campaign 0 evidence unless a later segment safely re-fetches the route
  surface and binds the route count/digest to the observed runtime identity.
  Segment 0B does not rely on that route count.

## New Branch And Worktree Identity

Observed at `2026-07-25T22:42:45Z`.

| Field | Observed value |
|---|---|
| Repository | `/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725` |
| Worktree | `/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725` |
| Branch | `codex/source-proxy-campaign-0-authoritative-base-20260725` |
| HEAD | `ede643c7e18535125efde807d5937f265dcc75f9` |
| Parent/base | `345047eed51f5c67abf5693dbca9f138e961a9b3`; created from exact approved base `ede643c7e18535125efde807d5937f265dcc75f9` |
| Tree | `1ec69bee8837e220654d05cc1697759b8edbefca` |
| Remote | `origin=/home/source/SpiritOS` |
| Remote ref before Segment 0B push | absent for `codex/source-proxy-campaign-0-authoritative-base-20260725` |
| Ahead/behind before Segment 0B push | no upstream configured; remote branch absent |
| Dirty count before Segment 0B docs | whole `0`; Source Proxy scoped `0` |

## Base Truth Retained

| Item | Status |
|---|---|
| `ede643c7e18535125efde807d5937f265dcc75f9` | `PUSHED / EVIDENCE-COMPLETE / REGRESSION-RED` |
| `6616846d7584af0318fe18fbaf7c3b1195ea03b0` | `CLEAN LOCAL / UNPUSHED / UNVALIDATED` |
| New Campaign 0 branch | `ISOLATED CANDIDATE / NOT YET GREEN` |
| Daily runtime checkout `/home/source/SpiritOS` | `DIRTY / ACTIVELY DRIFTING / NOT AUTHORITATIVE` |

## Isolation Proof

Observed at `2026-07-25T22:42:45Z`.

| Worktree or ref | Observed state |
|---|---|
| Campaign 3.5 execution worktree | `/home/source/SpiritOS-campaign-3-5-execution-20260719`, HEAD `6616846d7584af0318fe18fbaf7c3b1195ea03b0`, dirty count `0` |
| Planning worktree | `/home/source/SpiritOS-campaign-0-kickoff-planning-20260723`, HEAD `f45a7851ec688bcc99045f4c05ad80c4903ce094`, dirty count `0` |
| Daily checkout | `/home/source/SpiritOS`, HEAD `85dee8b59cce39afe1fbe7d674c066ccca1e6f13`, dirty count `4,842` as a timestamped observation |
| Manifest Source Proxy checkout | `/home/source/SpiritOS-source-proxy-20260711`, HEAD `594d66ef8280953af767a273d7c91be765d1a6eb`, dirty count `1` |
| Origin Campaign 3.5 ref | `refs/heads/codex/campaign-3-5-execution-20260719` remained `ede643c7e18535125efde807d5937f265dcc75f9` before Segment 0B push |
| Existing runtime | No service stop, start, restart, port change, or configuration change was performed in Segment 0B |

## Segment 0B Mutation Boundary

Allowed changes are limited to documentation/evidence artifacts under:

- `docs/campaign-0-authoritative-repository-runtime-truth/segment-0b-base-construction-20260725.md`
- `docs/campaign-0-authoritative-repository-runtime-truth/6616846d-disposition-ledger-20260725.md`

No production behavior change is authorized in Segment 0B. No code from
`6616846d` is cherry-picked, copied, rewritten, or accepted into this branch by
these documents.

## Baseline Checks

Segment 0B checks are setup checks only. Passing checks do not make this branch
regression-green.

| Category | Command | Expected mutation | Segment 0B result |
|---|---|---:|---|
| Repository identity | `git rev-parse HEAD`, `git rev-parse HEAD^{tree}`, `git status --porcelain=v1` | none | observed at `2026-07-25T22:44:22Z`: branch `codex/source-proxy-campaign-0-authoritative-base-20260725`, HEAD `ede643c7e18535125efde807d5937f265dcc75f9`, tree `1ec69bee8837e220654d05cc1697759b8edbefca`, Source Proxy scoped dirty count `0` |
| Unit/focused registry command | `.venv-source-proxy/bin/pytest -q source_proxy/tests/test_canonical_context_broker.py source_proxy/tests/test_context_source_readiness.py source_proxy/tests/test_prompt_packet_context_metadata.py` | none expected | not runnable directly: this isolated worktree has no `.venv-source-proxy` |
| Unit/focused fallback | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725 /home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python -m pytest -p no:cacheprovider -q source_proxy/tests/test_canonical_context_broker.py source_proxy/tests/test_context_source_readiness.py source_proxy/tests/test_prompt_packet_context_metadata.py` | none expected | `99 passed, 2 skipped in 20.27s`; fallback dependency runner only, not local dependency proof |
| Integration | none | n/a | not run in Segment 0B |
| Live/runtime | no route-surface proof | n/a | runtime identity only checked for non-mutation, not acceptance |
| Formal benchmarks | none | n/a | not authorized |

Post-test status check showed only the intended untracked docs directory and no
`__pycache__` or `.pytest_cache` residue within the checked depth.

## Rollback Method

Safe abandonment method for the isolated Segment 0B setup:

1. Verify no process CWD is `/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725`.
2. From `/home/source/SpiritOS-campaign-3-5-execution-20260719`, run:
   `git worktree remove /home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725`.
3. Delete only the Segment 0B branch if the operator rejects it:
   `git branch -D codex/source-proxy-campaign-0-authoritative-base-20260725`.
4. If the branch was pushed and must be withdrawn, delete only that remote ref:
   `git push origin :refs/heads/codex/source-proxy-campaign-0-authoritative-base-20260725`.

Do not reset, clean, stash, or alter `/home/source/SpiritOS`,
`/home/source/SpiritOS-campaign-3-5-execution-20260719`, or
`/home/source/SpiritOS-campaign-0-kickoff-planning-20260723` as part of this
rollback.

## Segment 0C Boundary

Segment 0C must reproduce the LumaCart
`coding_semantic_review_scope_invalid` failure in this isolated branch before
repair. Segment 0B does not repair or waive it.
