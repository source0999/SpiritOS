# Dashboard Redesign — Status

**Completed:** Phases 2, 2.5, 2.6, 3A

## What shipped

- Glass panel layout at `/` (palette-driven atmosphere, sticky header, natural scroll)
- Oracle Voice hero widget with inline SVG orb + visualizer
- System Stats card — live cluster telemetry per node (CPU, RAM, uptime)
- Storage card — live drive health grouped by node (SMART, temp, NVME/SSD/HDD tags)
- Daily Briefing widget
- Quick Links panel — static shortcuts to `/chat` and `/oracle`, no fake telemetry
- Theme strip — palette switcher in header
- Right-column sticky panel (Daily Briefing + Quick Links) on xl+

## Architecture notes

- Dashboard calls `useClusterTelemetry()` once at the `SpiritDashboardHome` level
- Telemetry `{ data, state, error }` is passed as props to `HomelabSystemStatsCard` and `HomelabStorageCard`
- Both cards fall back to their own `useClusterTelemetry()` when rendered standalone (tests, future reuse)
- Atmosphere/palette CSS lives in `src/app/globals.css` under `spirit-dashboard-v2-*` classes

## Reference folder

Design reference (Vite prototype) moved to `_reference/dashboardDemo/`. Excluded from lint and typecheck.

## Next phases

- **Phase 3B:** Shared navigation / dock polish (not started)
- **Later:** Replace static Quick Links with a useful live widget
- **Later:** Project tracker surface (see `progress_tracker_roadmap.md`)
