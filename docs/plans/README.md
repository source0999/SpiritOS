# SpiritOS Plan Index

This index separates active work, paused work, and historical evidence. It is intentionally an index only: do not delete, move, or resume old plans from this file without Britton approval and a fresh gate readback.

## Resume rules

- Treat current tracked source and the latest branch-specific state docs as more authoritative than old plan prose.
- Resume Source Proxy pivot work only through the documented plan gate. Plan 3 Set A is still not accepted; Set B, Set C, Stage 5, and Plan 4 are not automatic next steps.
- Cleanup branch F1-F10 is ready for secondary review, not merged or daily-driver accepted.
- Media, backup, and cartographer docs may describe useful systems, but they do not authorize SpiritFlix/media/Jellyfin mutation by themselves.
- Do not resume archived/historical evidence automatically. Use it to understand prior decisions, then ask for the current approval boundary.

| Area | Path | Status | Resume rule | Notes |
| --- | --- | --- | --- | --- |
| Source Proxy pivot plan-00..06 | `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/` | Paused active plan queue | Resume only with Britton approval; next old-plan action remains Plan 3 Set A closure, not Set B/C or Plan 4. | Plan 3 Set A is `NEEDS_FIX`; Plans 4-6 are written/not started. |
| Source Proxy cleanup breakpoint | `docs/breakpoints/source-proxy-cleanup-preplan-20260621/` | Source-of-truth breakpoint | Read before any old Source Proxy resume. | Freezes Set A state, Plan 3 blockers, and cleanup-roadmap count. |
| Cleanup branch F1-F10 | `docs/spiritos-full-repo-cleanup-20260621/` | Ready for secondary review | Secondary review may inspect; do not call fully accepted, daily-driver ready, merged, or Plan 3 resumed. | F1-F10 completed; F10R state hygiene and Headroom repair are separate from old-plan resume. |
| Media docs | `docs/media/` | Mixed media planning and implementation notes | Read-only unless a media task is explicitly approved. | Does not authorize Jellyfin or media data mutation. |
| Media server docs | `docs/media-server/` | Historical/operational media-server notes | Resume only under a media-server task with current host verification. | Check live host state before acting on old instructions. |
| Media plans | `docs/plans/media/` | Media plan archive | Resume only after confirming scope and owner approval. | Existing face-organizer docs are not a current SpiritFlix implementation gate. |
| Backup system | `docs/backup-system/` | Backup planning/operations docs | Resume only through a backup-specific approval. | Keep backup changes separate from Source Proxy cleanup. |
| Cartographer live evidence | `docs/cartographer-live-evidence/` | Evidence/historical receipts | Do not resume automatically. | Use for audit context, not as implementation authority. |
| Cartographer live receipts | `docs/cartographer-live-receipts/` | Evidence/historical receipts | Do not resume automatically. | Receipts can support review but do not open new work. |

## Active, paused, archived

Active plans are the ones Britton names for the current session and approves through the current gate. Paused plans can be resumed only after rereading their state files and confirming the next allowed step. Archived or historical evidence is for audit and orientation; it should not be treated as a queue of authorized work.

## What not to resume automatically

Do not automatically resume Set A/B/C, Plan 3, Plan 4, media imports, SpiritFlix feature work, Jellyfin operations, backup-system changes, or cartographer live work from this index. Use this file to find the right evidence, then re-establish the current approval boundary.
