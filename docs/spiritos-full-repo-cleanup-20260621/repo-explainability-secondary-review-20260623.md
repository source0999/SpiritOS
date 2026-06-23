# Repo Explainability Secondary Review - 2026-06-23

## Scope

Repo explainability cleanup only. This pass did not resume Plan 3, start Plan 4, run Set A/B/C, merge, push, or perform SpiritFlix/media/Jellyfin feature work.

## README changes

`README.md` now includes `LLM Context Packs / Repomix + Headroom` near the top of the file. It explains that external LLMs cannot see the repo directly, focused XML packs should be uploaded for review, raw full-repo evidence/media sludge packs should be avoided, visible XMLs are written to `/home/source/SpiritOS/`, generated XMLs should remain untracked, and Headroom is active only when `compressed="true"` and `tokens_saved > 0`.

The README distinguishes these pack outputs:

- `source-proxy-min-context.xml`: existing Source Proxy/coding-only npm profile.
- `repo-map-context.xml`: repo/docs overview.
- `source-proxy-context.xml`: Source Proxy and coding lane review.
- `frontend-context.xml`: frontend app/lib/components review.
- `spiritflix-media-code-context.xml`: SpiritFlix/media code only, no media files.
- `docs-plans-context.xml`: plans, docs, breakpoints, and audits.

## Context pack commands

Added single-pack commands for `npm run context:repo-map`, `npm run context:source-proxy-min`, and `npm run context:verify` with the repaired Headroom environment variables.

Added an all-packs command that installs an isolated `repomix@1.14.0` runner under `/tmp/spiritos-repomix-bin-20260623`, writes a temporary focused config without the repo-wide `**/*` include, excludes evidence/media/runtime sludge, and writes uploadable XMLs into `/home/source/SpiritOS/`.

The all-packs command was tested with the same focused config and quiet Repomix output to reduce terminal noise. Resulting visible outputs:

- `/home/source/SpiritOS/repo-map-context.xml`: 7.1M.
- `/home/source/SpiritOS/source-proxy-context.xml`: 1.4M.
- `/home/source/SpiritOS/frontend-context.xml`: 260K.
- `/home/source/SpiritOS/spiritflix-media-code-context.xml`: 222K.
- `/home/source/SpiritOS/docs-plans-context.xml`: 7.0M.

The first no-config all-packs test was too broad because Repomix merged the repo config `**/*` include with the CLI include; the README command was repaired before final handoff.

## Runbook

Created `docs/context-export/llm-context-pack-runbook.md` with pack purposes, exclusions, visible output paths, Headroom verification rules, single-pack generation, all-packs generation, first-pack guidance, and the warning not to send `docs/evidence/**` unless auditing receipts specifically.

## Plan index

Created `docs/plans/README.md` as an index only. It classifies active, paused, and archived/historical evidence and includes a table for:

- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/`
- `docs/breakpoints/source-proxy-cleanup-preplan-20260621/`
- `docs/spiritos-full-repo-cleanup-20260621/`
- `docs/media/`
- `docs/media-server/`
- `docs/plans/media/`
- `docs/backup-system/`
- `docs/cartographer-live-evidence/`
- `docs/cartographer-live-receipts/`

The index explicitly says not to resume Set A/B/C, Plan 3, Plan 4, media imports, SpiritFlix feature work, Jellyfin operations, backup changes, or cartographer live work automatically.

## Comments and docstrings added

Targeted ownership/safety comments were added to:

- `source_proxy/diagnostics/status_codes.py`: failure taxonomy ownership and verdict-vocabulary safety.
- `source_proxy/verification/anticheat/registry.py`: anti-cheat registry as audit layer, not verdict repair.
- `source_proxy/decision/escalation_contract.py`: brain-switch recommendations are dry-run/advisory and do not execute provider policy.
- `source_proxy/decision/packet_decomposition.py`: local decomposition and benchmark-label anti-tailoring boundary.
- `source_proxy/decision/worker_tool_adapters.py`: typed subprocess probe contract and evidence echoing.
- `source_proxy/tasks/engine/state.py`: side-effect-free task-state predicates.
- `src/lib/coding/shell-registry.ts`: `/coding` shell canonical/alternate ownership boundary.
- `scripts/source-context-compress.mjs`: uploadable XML boundary and honest Headroom fallback labeling.

## Intentional non-touches

Inspected but did not add comments to the large UI shells or broad API/task modules beyond the registry/helper surfaces. `src/components/coding/CodingCockpitShell.tsx`, `src/components/coding/CodingCommandCenterShell.tsx`, `source_proxy/api/decision.py`, `source_proxy/tasks/long_running.py`, `source_proxy/verification/anticheat/detectors.py`, and `source_proxy/decision/lanes/status_helpers.py` already had enough local context or would have invited noisy comments for this pass.

No old plans were deleted, moved, renamed, or resumed.

## Validation

- Preflight: branch `cleanup/full-repo-20260621`; starting HEAD `01c4779162377c2aa519bdf5cbf9e24d962099f4`; only pre-existing untracked generated `source-proxy-min-context.xml` was visible.
- `git diff --check`: PASS.
- `npm run typecheck`: PASS.
- `/home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py source_proxy/tests/test_brain_switch_contract.py source_proxy/tests/test_packet_decomposition.py -q`: PASS, 40 passed in 11.04s.
- `python3 -m pytest ...`: BLOCKED_ENV, system Python has no `pytest`; the repo/source-proxy venv was used for the actual focused backend test.
- `HEADROOM_PORT=8798 HEADROOM_BASE_URL=http://127.0.0.1:8798 HEADROOM_BIN=/home/source/SpiritOS/.venv-headroom/bin/headroom npm run context:source-proxy-min`: PASS after repairing Repomix CLI resolution.
- `HEADROOM_PORT=8798 HEADROOM_BASE_URL=http://127.0.0.1:8798 HEADROOM_BIN=/home/source/SpiritOS/.venv-headroom/bin/headroom npm run context:verify`: PASS; bundle compression `tree-sitter+headroom`, `compressed="true"`, `tokens_saved=106846`, size 1.2M.
- README all-packs command shape: PASS after focused temporary config repair; visible XMLs written to `/home/source/SpiritOS/` and remain untracked artifacts.

## Caveats

`scripts/source-context-compress.mjs` needed a small robustness repair because the local `node_modules/repomix/bin/repomix.cjs` had been overwritten with the SpiritOS shell shim. The script now uses a valid local Node Repomix CLI when present, otherwise installs/uses an isolated `/tmp/spiritos-repomix-runtime-1.14.0` runner. No package files or `node_modules` artifacts were committed.

The all-packs command uses Repomix Tree-sitter compression. Headroom-positive proof was verified on the maintained `source-proxy-min` npm context path, not on the ad hoc all-packs command.

## Safety readback

- Source Proxy runtime behavior changed: no; comments/docstrings only, plus context-script robustness for pack generation.
- SpiritFlix/media/Jellyfin touched: no runtime/data mutation; only context pack instructions mention SpiritFlix/media code pack.
- Set A/B/C: not run.
- Plan 3/4: not resumed or started.
- Push: not performed.
- Merge: not performed.

## Verdict

REPO_EXPLAINABILITY_READY_FOR_SECONDARY_REVIEW
