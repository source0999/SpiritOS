# SpiritFlix continuity repair plan — 2026-07-19

**Status:** `PLANNED_NOT_EXECUTED`

This is a separate remediation plan. It does not repair or modify the dirty
`/home/source/SpiritOS` checkout in place.

## Verified facts

- Campaign 1/2 protected commit: `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`.
- Observed external `master`: `85dee8b59cce39afe1fbe7d674c066ccca1e6f13`.
- Observed `master` is behind the protected commit; the protected commit remains
  available through campaign references/tags and their trees differ materially.
- The checkout is pre-existing dirty and strict verification reports pack
  checksum, CRC, and inflate corruption.

See `campaign-1-2-continuity-drift-20260719.md` and its JSON companion for
the evidence. The failure is real and remains an external dependency gate.

## Future workflow

**SF-0 — preserve and identify authority.** Record refs, remotes, tags,
protected commit, dirty status, and repository identity. Preserve local-only
work without mutating it. Determine the authoritative remote or bundle.

**SF-1 — build a clean object source.** Create a new clean clone, mirror, or
verified-bundle object database—not the dirty checkout. Import required objects,
verify hashes, run strict `git fsck`, confirm the protected commit/tags,
ancestry, and expected trees; reject corrupt sources.

**SF-2 — determine approved live head.** Compare the protected commit, existing
approved descendants, later product candidates, and any reconstructed approved
integration branch. Produce ref map, commit graph, protected-path diff,
campaign-tag verification, and approval recommendation. Do not assume current
dirty `master` is authoritative.

**SF-3 — restore only after approval.** Preserve the dirty checkout separately,
create recovery bundles before ref changes, never hard-reset/clean it, and do
not force-push without explicit authority. Prove the chosen head descends from
the protected baseline, then rerun Campaign 1/2 validators against the clean
authoritative reference.

**SF-4 — reconnect dependencies.** Record repository identity, immutable
baseline, approved live ref, allowed relation, and strict verification. Unblock
only the specific dependent operation whose preflight now passes.

Terminal verdicts: `SPIRITFLIX_CONTINUITY_RESTORED`,
`SPIRITFLIX_CONTINUITY_BLOCKED_NO_AUTHORITATIVE_OBJECT_SOURCE`,
`SPIRITFLIX_CONTINUITY_BLOCKED_DIVERGENT_HISTORY`,
`SPIRITFLIX_CONTINUITY_BLOCKED_OPERATOR_REF_DECISION_REQUIRED`, and
`SPIRITFLIX_CONTINUITY_BLOCKED_OBJECT_CORRUPTION`.
