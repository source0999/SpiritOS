# Campaign 1 Recovery Record

Verdict: `GO_CAMPAIGN_1_COMPLETE`.

## Preserved pre-GO quarantine

- Path: `/home/source/SpiritOS-campaign-1-20260712.recovery-quarantine-20260715T021242-0400`.
- Classification: **pre-GO recovery quarantine**, not a current Campaign worktree and not an implementation source of truth.
- Reconciliation: it contains no unique uncommitted Campaign work. No file was restored from it during final acceptance or closeout-integrity repair.
- Preservation rule: retain the quarantine and its companion manifests unchanged until Campaign 1 archival policy explicitly permits disposal. Do not overwrite, delete, stage, or merge it.

## Final recovery anchor procedure

After the atomic closeout commit, create a local annotated Campaign 1 tag and a bundle outside the worktree, write a SHA-256 manifest, and record the branch, final commit, timestamp, artifact path, included refs, excluded secrets, and restoration instructions in that external anchor. No push is part of this procedure.
