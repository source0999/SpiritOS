# Increment 0.1.1: Name The Isolated Proxy Lane And Evidence Root

PLAN:
Plan 0, Isolated Proxy Lane Baseline.

PHASE:
Phase 0.1, Lane Identity And Boundary Packet.

INCREMENT:
Increment 0.1.1, Name the isolated proxy lane and evidence root.

Objective:
Name the isolated proxy lane and evidence root before any implementation, testing, validation, or proof.

Isolated proxy lane scope:
Lane name: `unified-proxy-coding-design-plan-0`.

Evidence root: `/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/`.

Allowed files or file zones:
- Evidence-only Plan 0 artifacts inside `/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/`.
- Read-only repository inspection.
- Source-of-truth plan file read-only reference: `/home/source/SpiritOS/docs/spirit-os-unified-proxy-coding-design-system-master-plan-of-plans-v0.1.md`.

Forbidden files, paths, systems, and actions:
- Production source edits.
- Production route, component, backend, Cartographer runtime, Source Proxy runtime, map state, queue, provider, apply, or execute-approved mutation.
- Cartographer soak logs, Scout soak logs, Cartographer live evidence, Cartographer runtime state, production map state, and production Source Proxy state.
- Git mutation: clean, stash, reset, checkout, stage, commit, push, branch, or worktree.

Exact work performed:
- Read the source-of-truth plan file.
- Confirmed the lane name and evidence root.
- Recorded the isolation rule and no-main/no-soak declaration in this evidence packet.
- Did not touch production source, runtime state, soak logs, live evidence, or git metadata.

Required tests/checks:
```text
$ pwd
/home/source

$ ls -ld /home/source/SpiritOS /home/source/SpiritOS/docs /home/source/SpiritOS/docs/evidence
drwxr-xr-x 28 source source 12288 May 25 12:11 /home/source/SpiritOS
drwxrwxr-x  6 source source 86016 May 25 17:44 /home/source/SpiritOS/docs
drwx------  3 source source  4096 May 25 16:57 /home/source/SpiritOS/docs/evidence
```

Manual validation performed by Codex:
- The evidence root is under `docs/evidence/`, not a runtime, log, queue, map, provider, or Source Proxy state directory.
- The lane name is explicit and unique to Plan 0.
- The allowed Plan 0 mutation zone is evidence-only.

Evidence artifact:
This file.

Stop conditions checked:
- Lane ambiguous: no.
- Evidence root overlaps runtime/shared state: no.
- Main repo execution path mutation required: no.
- Cartographer soak path mutation required: no.
- Git mutation required: no.

Rollback or recovery note:
No stash, reset, clean, checkout, stage, commit, branch, worktree, or push is authorized. If correction is needed, write a correction packet inside the same evidence root or stop for operator review.

GO/NO-GO exit:
GO for Increment 0.1.1. Lane and evidence root are explicit.

Next authorized increment only:
Plan 0, Phase 0.1, Increment 0.1.2.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.
