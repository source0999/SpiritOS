# Jellyfin Basic Media Server Handoff

Copy-paste this into a new Codex/chat session when ready to execute the plan.

```text
You are Codex working inside my SpiritOS repo on the Dell server.

MISSION:
Execute the existing Jellyfin basic media server plan phase by phase and increment by increment. Start with Phase 0 baseline validation. Do not skip ahead. Do not merge Jellyfin into the SpiritOS /media page. Do not touch YTMClone/999Playr.

PLAN FILE:
docs/media-server/jellyfin-basic-media-server-plan.md

CURRENT STATUS:
The prior chat created the docs-only plan. Jellyfin has not been installed, started, exposed, or configured by that planning run.

STRICT BOUNDARIES:
- Do not edit src/app/media/**
- Do not edit src/components/media/**
- Do not edit apps/ytmclone-android/**
- Do not edit any 999Playr/YTMClone app files
- Do not edit existing production Docker Compose files unless the plan increment allows a compose decision and I approve it
- Do not edit .env files or secrets
- Do not touch backup repositories
- Do not move, rename, delete, or deeply scan existing /mnt/spirit-8tb media contents
- Do not expose Jellyfin publicly
- Do not use Tailscale Funnel
- Do not configure router port forwarding or public DNS

PIVOT STYLE:
- Work one phase at a time.
- Work one increment at a time.
- For each increment, follow the plan's purpose, allowed files, forbidden files, exact commands, expected result, rollback note, and manual check.
- Record evidence under docs/evidence/media-server/<phase>/.
- Each phase must end with a closeout check.
- Continue only when the increment result is GO or when a blocker has a clear fix inside the plan.
- Stop and ask me before installing packages, starting/stopping services outside the Jellyfin increment, changing firewall/network state, changing backup automation, or editing forbidden paths.

START NOW:
1. Read docs/media-server/jellyfin-basic-media-server-plan.md.
2. Run Phase 0 read-only baseline increments only.
3. Report GO/NO-GO for Phase 0.
4. If Phase 0 is GO, ask me before starting Phase 1 because Phase 1 writes to /mnt/spirit-8tb.

END STATE OF FULL PLAN:
Jellyfin runs on the Dell using /mnt/spirit-8tb, has Movies, TV Shows, Music, Anime, and Other libraries, plays my owned media, opens locally, opens from another Tailscale device through a private MagicDNS name or optional private Tailscale Serve HTTPS route, and remains outside the existing SpiritOS /media UI.
```

## Planning-Run Verification Block

```powershell
Set-Location 'Z:\'
$required = @(
  'docs\media-server\jellyfin-basic-media-server-plan.md',
  'docs\media-server\jellyfin-basic-media-server-handoff.md'
)
$forbidden = @(
  'src\app\media',
  'src\components\media',
  'apps\ytmclone-android',
  'backend\docker-compose.yml',
  '.env',
  '.env.local'
)
'Required docs:'
$required | ForEach-Object { if (Test-Path $_) { "OK $_" } else { "MISSING $_" } }
'Created docs lane:'
Get-ChildItem -Path 'docs\media-server' -File | Select-Object Name,Length,LastWriteTime
'Changed tracked forbidden files, if any:'
git diff --name-only -- $forbidden
'Media-server git status:'
git status --short -- docs/media-server
```
