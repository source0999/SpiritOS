# Jellyfin Basic Media Server Plan

Date: 2026-06-02
Status: GO for plan creation only. NO-GO for install, service start, firewall changes, public exposure, or SpiritOS UI integration in this run.

## Mission

Create a basic Dell-hosted Jellyfin media server lane that uses the existing 8 TB drive at `/mnt/spirit-8tb`, keeps Jellyfin outside the SpiritOS `/media` page for now, and makes the service reachable from trusted devices through Tailscale. The end state is a working Jellyfin server at a private Tailscale route such as `http://<dell-tailscale-name>:8096` or, after a later optional Tailscale Serve step, `https://<dell-tailscale-name>.<tailnet>.ts.net`.

This plan is execution-ready but intentionally not executed by this planning run.

## Hard Boundaries

Allowed planning files for this run:

- `docs/media-server/jellyfin-basic-media-server-plan.md`
- `docs/media-server/jellyfin-basic-media-server-handoff.md`

Forbidden during this planning run and every phase unless an increment explicitly allows it:

- No edits under `src/app/media/**`
- No edits under `src/components/media/**`
- No edits under `apps/ytmclone-android/**`
- No edits to any 999Playr/YTMClone app files
- No edits to existing production Compose files until Phase 2 approval chooses a compose location
- No `.env` or secret edits
- No backup repository edits or backup execution
- No reads, writes, moves, or deletes inside existing media contents under `/mnt/spirit-8tb`
- No live service start, stop, restart, install, firewall, or network-state changes during planning
- No public internet exposure in Phase 1

## Repo Inventory Used For This Plan

- Existing Docker Compose pattern:
  - `backend/docker-compose.yml` owns backend services on `backend_spirit-net`, uses `restart: unless-stopped`, explicit `container_name`, healthchecks, and named volumes for backend state.
  - `scout/docker-compose.scout.yml` keeps a service-local compose file under the service folder and joins the external `backend_spirit-net` network when it needs backend access.
- Existing service naming:
  - Backend containers use names such as `spirit-ollama`, `spirit-whisper`, `spirit-openedai-speech`, and `spirit-searxng`.
  - Jellyfin should use `spirit-jellyfin` unless a conflict is found.
- Existing docs/evidence style:
  - Plans are kept under `docs/**`.
  - Execution evidence and closeouts commonly live under `docs/evidence/<lane>/<phase-or-plan>/`.
  - Backup plans use GO/NO-GO phase closeouts and dry-run-first safety gates.
- Existing backup lane:
  - `docs/runbooks/spiritos-backup-runbook.md` and `docs/backup-system/backup-system-v0.1-contract.md` require explicit approval for installs, real writes to `/mnt/spirit-8tb`, Docker volume exports, container changes, backup runs, prune/delete, commits, and pushes.
  - Jellyfin config/cache/media backup decisions must be documented before any automation is added.
- Existing media UI boundary:
  - `src/app/media/page.tsx` renders the existing SpiritOS media experience.
  - `src/components/media/MediaExperience.tsx` is a local browser/media prototype with manual catalog and browser-local state.
  - This Jellyfin lane must remain outside that route and not embed Jellyfin into SpiritOS `/media`.
- Existing Tailscale/LAN conventions:
  - README documents LAN/Tailscale checks with host `10.0.0.186` for some SpiritOS services, local HTTPS dev conventions, and using Tailscale routes for cross-device access.
  - Jellyfin Phase 1 access should prefer Tailscale MagicDNS and port `8096`, not public DNS or public firewall exposure.
- Existing 8 TB mount references:
  - `/mnt/spirit-8tb` is already used in docs/scripts for backups and model storage.
  - Existing evidence has shown `/mnt/spirit-8tb` as an ext4 mount with about 7.3T capacity, but Phase 0 must recheck live state before execution.

## Official References To Check During Execution

- Jellyfin official container setup: https://jellyfin.org/docs/general/installation/container/
- Jellyfin official movie library organization: https://jellyfin.org/docs/general/server/media/movies/
- Jellyfin official show library organization: https://jellyfin.org/docs/general/server/media/shows/
- Jellyfin official music library organization: https://jellyfin.org/docs/general/server/media/music/
- Docker Compose file reference: https://docs.docker.com/reference/compose-file/
- Tailscale MagicDNS: https://tailscale.com/docs/features/magicdns
- Tailscale Serve CLI: https://tailscale.com/docs/reference/tailscale-cli/serve
- Tailscale Serve examples and ACL note: https://tailscale.com/docs/reference/examples/serve

Notes from official docs checked in this planning run:

- Jellyfin publishes the official `jellyfin/jellyfin` container image and recommends persistent config/cache/media mounts for containers.
- Jellyfin movie libraries should use a Movies library type and individual movie folders where practical.
- Tailscale MagicDNS gives each device a machine name plus tailnet DNS name, and enabled search domains allow short machine-name access.
- `tailscale serve` can privately share a local service inside a tailnet. It is optional here and must not be confused with Tailscale Funnel or public exposure.
- Docker Compose v2 uses the current Compose Specification for services, networks, volumes, and related service definitions.

## Target Paths

Media folders:

```text
/mnt/spirit-8tb/media/movies
/mnt/spirit-8tb/media/tv
/mnt/spirit-8tb/media/music
/mnt/spirit-8tb/media/anime
/mnt/spirit-8tb/media/other
```

Jellyfin service state:

```text
/mnt/spirit-8tb/services/jellyfin/config
/mnt/spirit-8tb/services/jellyfin/cache
/mnt/spirit-8tb/services/jellyfin/transcodes
```

Recommended compose lane:

```text
services/jellyfin/docker-compose.yml
```

If the repo owner wants service folders under another existing convention, Phase 2 must stop before writing compose and ask for approval.

## Phase 0: Baseline And Safety Inventory

Goal: prove the Dell host, mount, Docker, Tailscale, port, and repo boundaries before any writes.

### Increment 0.1: Repo Boundary Baseline

Purpose: Record current repo state and prove forbidden app paths are not part of this media-server lane.

Allowed files:

- `docs/evidence/media-server/phase-0/increment-0.1-repo-boundary.md`

Forbidden files:

- `src/app/media/**`
- `src/components/media/**`
- `apps/ytmclone-android/**`
- `backend/docker-compose.yml`
- `.env*`

Exact commands:

```bash
cd /home/source/SpiritOS
git status --short -- docs/media-server docs/evidence/media-server src/app/media src/components/media apps/ytmclone-android backend/docker-compose.yml .env .env.local || true
find docs/media-server -maxdepth 2 -type f -print | sort || true
test -f src/app/media/page.tsx && echo MEDIA_ROUTE_PRESENT
test -f src/components/media/MediaExperience.tsx && echo MEDIA_COMPONENT_PRESENT
```

Expected result:

- Existing media route/component are present.
- No Phase 0 command changes source files.
- Any pre-existing dirty files are recorded by path only.

Rollback note:

- Documentation-only. Delete the new `docs/evidence/media-server/phase-0/increment-0.1-repo-boundary.md` if it is incorrect.

Manual check:

- Confirm the output includes no modified forbidden files caused by this lane.

### Increment 0.2: Dell Host And 8 TB Mount Baseline

Purpose: Confirm the executor is on the Dell SpiritOS host and `/mnt/spirit-8tb` is mounted before planning writes.

Allowed files:

- `docs/evidence/media-server/phase-0/increment-0.2-host-and-mount.md`

Forbidden files:

- `/mnt/spirit-8tb/**` writes
- backup repos
- service files

Exact commands:

```bash
hostname
whoami
pwd
findmnt /mnt/spirit-8tb
df -h /mnt/spirit-8tb
ls -ld /mnt/spirit-8tb
```

Expected result:

- Hostname matches the Dell/source server expected by the user.
- `/mnt/spirit-8tb` is mounted and has sufficient free space.

Rollback note:

- Documentation-only. If the host or mount is wrong, stop before Phase 1.

Manual check:

- Confirm `/mnt/spirit-8tb` exists and is the intended 8 TB drive.

### Increment 0.3: Docker And Jellyfin Conflict Baseline

Purpose: Confirm Docker exists and port/container names are available without starting or stopping anything.

Allowed files:

- `docs/evidence/media-server/phase-0/increment-0.3-docker-conflict-baseline.md`

Forbidden files:

- Docker service changes
- Compose edits
- Container start/stop/restart

Exact commands:

```bash
docker --version
docker compose version
docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' | grep -Ei 'jellyfin|8096|spirit-jellyfin' || true
ss -tlnp | grep -E '(:8096)\b' || true
```

Expected result:

- Docker and Docker Compose are installed.
- No existing Jellyfin container is using `spirit-jellyfin`.
- Port `8096` is free, or a conflict is recorded for Phase 2 to resolve.

Rollback note:

- Read-only. If Docker is missing, stop and ask for explicit approval before any install.

Manual check:

- Confirm no unexpected Jellyfin service already exists.

### Increment 0.4: Tailscale Baseline

Purpose: Confirm private Tailscale access is available or identify the blocker.

Allowed files:

- `docs/evidence/media-server/phase-0/increment-0.4-tailscale-baseline.md`

Forbidden files:

- Tailscale login, logout, up, serve, funnel, ACL, or DNS changes
- Firewall changes

Exact commands:

```bash
tailscale version
tailscale status --self
tailscale ip -4
tailscale status | head -40
```

Expected result:

- Tailscale is installed and the Dell is logged into the expected tailnet.
- The Dell has a Tailscale IPv4 address and a MagicDNS machine name.

Rollback note:

- Read-only. If Tailscale is missing or logged out, mark Phase 4 as blocked until the user approves Tailscale setup.

Manual check:

- Confirm the machine name is the one the user wants to type from other devices.

### Phase 0 Closeout Check

GO only when:

- `/mnt/spirit-8tb` is mounted.
- Docker and Compose are available.
- No Jellyfin container/port conflict is present, or the conflict is documented.
- Tailscale is installed/logged in, or Phase 4 blocker is documented.
- No SpiritOS `/media` route files were edited.

Closeout file:

- `docs/evidence/media-server/phase-0/phase-0-closeout.md`

## Phase 1: Media Storage Layout

Goal: create obvious media and service folders on the 8 TB drive with a simple permission strategy.

### Increment 1.1: Dry-Run Storage Layout

Purpose: Preview the exact directories to create before writing to `/mnt/spirit-8tb`.

Allowed files:

- `docs/evidence/media-server/phase-1/increment-1.1-storage-layout-dry-run.md`

Forbidden files:

- Existing media files under `/mnt/spirit-8tb`
- Backup repositories
- Docker compose files

Exact commands:

```bash
cd /home/source/SpiritOS
for path in \
  /mnt/spirit-8tb/media/movies \
  /mnt/spirit-8tb/media/tv \
  /mnt/spirit-8tb/media/music \
  /mnt/spirit-8tb/media/anime \
  /mnt/spirit-8tb/media/other \
  /mnt/spirit-8tb/services/jellyfin/config \
  /mnt/spirit-8tb/services/jellyfin/cache \
  /mnt/spirit-8tb/services/jellyfin/transcodes
do
  printf 'WOULD_CREATE %s\n' "$path"
done
findmnt /mnt/spirit-8tb
df -h /mnt/spirit-8tb
```

Expected result:

- The intended directory list is printed.
- No directories are created in this dry-run increment.

Rollback note:

- No filesystem rollback needed.

Manual check:

- Confirm folder names match the desired simple categories: Movies, TV Shows, Music, Anime or Animation, Other.

### Increment 1.2: Create Media And Jellyfin State Directories

Purpose: Create the minimum persistent directory structure after user approval to execute Phase 1.

Allowed files:

- `docs/evidence/media-server/phase-1/increment-1.2-create-storage-layout.md`
- New directories listed in Target Paths

Forbidden files:

- Existing media contents
- Backup repositories
- SpiritOS source files

Exact commands:

```bash
sudo mkdir -p \
  /mnt/spirit-8tb/media/movies \
  /mnt/spirit-8tb/media/tv \
  /mnt/spirit-8tb/media/music \
  /mnt/spirit-8tb/media/anime \
  /mnt/spirit-8tb/media/other \
  /mnt/spirit-8tb/services/jellyfin/config \
  /mnt/spirit-8tb/services/jellyfin/cache \
  /mnt/spirit-8tb/services/jellyfin/transcodes

sudo chown -R source:source /mnt/spirit-8tb/media /mnt/spirit-8tb/services/jellyfin
sudo chmod 775 /mnt/spirit-8tb/media /mnt/spirit-8tb/services /mnt/spirit-8tb/services/jellyfin
sudo find /mnt/spirit-8tb/media -maxdepth 1 -type d -exec chmod 775 {} \;
sudo find /mnt/spirit-8tb/services/jellyfin -maxdepth 1 -type d -exec chmod 775 {} \;

find /mnt/spirit-8tb/media -maxdepth 2 -type d -printf '%M %u %g %p\n' | sort
find /mnt/spirit-8tb/services/jellyfin -maxdepth 2 -type d -printf '%M %u %g %p\n' | sort
```

Expected result:

- The media category folders and Jellyfin state folders exist.
- The `source` user can place media files in category folders.
- Permissions are not world-writable.

Rollback note:

- Only if these newly created folders are empty:

```bash
sudo rmdir /mnt/spirit-8tb/media/movies /mnt/spirit-8tb/media/tv /mnt/spirit-8tb/media/music /mnt/spirit-8tb/media/anime /mnt/spirit-8tb/media/other
sudo rmdir /mnt/spirit-8tb/services/jellyfin/config /mnt/spirit-8tb/services/jellyfin/cache /mnt/spirit-8tb/services/jellyfin/transcodes /mnt/spirit-8tb/services/jellyfin
```

Manual check:

- Put nothing in the folders yet unless the user explicitly chooses a small test media file later.

### Increment 1.3: Folder Usage Notes

Purpose: Write a short local usage note so category placement is obvious.

Allowed files:

- `docs/media-server/jellyfin-folder-map.md`
- `docs/evidence/media-server/phase-1/increment-1.3-folder-map.md`

Forbidden files:

- Source app files
- Existing production compose

Exact commands:

```bash
cat > docs/media-server/jellyfin-folder-map.md <<'EOF'
# Jellyfin Folder Map

Movies: /mnt/spirit-8tb/media/movies
TV Shows: /mnt/spirit-8tb/media/tv
Music: /mnt/spirit-8tb/media/music
Anime or Animation: /mnt/spirit-8tb/media/anime
Other: /mnt/spirit-8tb/media/other

Jellyfin config: /mnt/spirit-8tb/services/jellyfin/config
Jellyfin cache: /mnt/spirit-8tb/services/jellyfin/cache
Jellyfin transcodes: /mnt/spirit-8tb/services/jellyfin/transcodes
EOF

sed -n '1,80p' docs/media-server/jellyfin-folder-map.md
```

Expected result:

- Folder map exists and matches Phase 1 paths.

Rollback note:

- Delete `docs/media-server/jellyfin-folder-map.md` if wrong.

Manual check:

- Confirm the names are simple enough to use without remembering Jellyfin internals.

### Phase 1 Closeout Check

GO only when:

- All target folders exist.
- Ownership and permissions are documented.
- No existing media files were moved, renamed, deleted, or scanned deeply.
- `docs/media-server/jellyfin-folder-map.md` exists.

Closeout file:

- `docs/evidence/media-server/phase-1/phase-1-closeout.md`

## Phase 2: Jellyfin Docker Compose Service

Goal: create and start a basic Jellyfin container with persistent config/cache/transcodes/media mounts and no public exposure.

### Increment 2.1: Compose Location Decision

Purpose: Choose a compose lane without touching existing production compose files.

Allowed files:

- `docs/evidence/media-server/phase-2/increment-2.1-compose-location.md`

Forbidden files:

- `backend/docker-compose.yml`
- `scout/docker-compose.scout.yml`
- `.env*`

Exact commands:

```bash
cd /home/source/SpiritOS
test -d services && echo SERVICES_DIR_EXISTS || echo SERVICES_DIR_MISSING
find . -maxdepth 3 \( -name 'docker-compose.yml' -o -name 'docker-compose.*.yml' -o -name 'compose.yml' \) -print | sort
```

Expected result:

- Preferred location is `services/jellyfin/docker-compose.yml`.
- If `services/` does not exist, create only `services/jellyfin/` in Increment 2.2 or stop and ask whether to use `ops/jellyfin/`.

Rollback note:

- Decision-only.

Manual check:

- User accepts repo-tracked standalone compose lane.

### Increment 2.2: Write Jellyfin Compose File

Purpose: Add a standalone compose file for Jellyfin.

Allowed files:

- `services/jellyfin/docker-compose.yml`
- `docs/evidence/media-server/phase-2/increment-2.2-compose-file.md`

Forbidden files:

- Existing production compose files
- `.env*`
- Source app files

Exact commands:

```bash
cd /home/source/SpiritOS
mkdir -p services/jellyfin
cat > services/jellyfin/docker-compose.yml <<'EOF'
services:
  jellyfin:
    image: jellyfin/jellyfin:latest
    container_name: spirit-jellyfin
    restart: unless-stopped
    ports:
      - "8096:8096"
    volumes:
      - /mnt/spirit-8tb/services/jellyfin/config:/config
      - /mnt/spirit-8tb/services/jellyfin/cache:/cache
      - /mnt/spirit-8tb/services/jellyfin/transcodes:/transcodes
      - /mnt/spirit-8tb/media/movies:/media/movies:ro
      - /mnt/spirit-8tb/media/tv:/media/tv:ro
      - /mnt/spirit-8tb/media/music:/media/music:ro
      - /mnt/spirit-8tb/media/anime:/media/anime:ro
      - /mnt/spirit-8tb/media/other:/media/other:ro
    environment:
      - JELLYFIN_PublishedServerUrl=http://127.0.0.1:8096
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8096/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
EOF

docker compose -f services/jellyfin/docker-compose.yml config
```

Expected result:

- Compose config validates.
- Media folders are mounted read-only into Jellyfin.
- Config/cache/transcodes are persistent on the 8 TB drive.

Rollback note:

```bash
rm -f services/jellyfin/docker-compose.yml
rmdir services/jellyfin 2>/dev/null || true
```

Manual check:

- Confirm port `8096` remains the intended port and media mounts are read-only.

### Increment 2.3: Start Jellyfin Container

Purpose: Start Jellyfin after compose validation.

Allowed files:

- `docs/evidence/media-server/phase-2/increment-2.3-start-container.md`
- Docker state for `spirit-jellyfin`

Forbidden files:

- Existing SpiritOS containers unless Docker needs to inspect state
- Firewall or public exposure changes

Exact commands:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml up -d
docker compose -f services/jellyfin/docker-compose.yml ps
docker inspect spirit-jellyfin --format '{{.State.Status}} {{.State.Health.Status}}' || docker inspect spirit-jellyfin --format '{{.State.Status}}'
docker logs --tail 80 spirit-jellyfin
curl -I http://127.0.0.1:8096 || true
```

Expected result:

- `spirit-jellyfin` is running.
- `http://127.0.0.1:8096` responds.
- No public internet route is configured.

Rollback note:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml down
```

Manual check:

- Open `http://127.0.0.1:8096` on the Dell or an SSH-forwarded browser.

### Increment 2.4: Local/LAN Status Commands

Purpose: Record repeatable commands for status, logs, restart, and health.

Allowed files:

- `docs/media-server/jellyfin-operations.md`
- `docs/evidence/media-server/phase-2/increment-2.4-status-commands.md`

Forbidden files:

- Backup automation
- Existing service scripts

Exact commands:

```bash
cat > docs/media-server/jellyfin-operations.md <<'EOF'
# Jellyfin Operations

Compose file:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml ps
docker compose -f services/jellyfin/docker-compose.yml logs --tail 120 jellyfin
docker compose -f services/jellyfin/docker-compose.yml restart jellyfin
docker compose -f services/jellyfin/docker-compose.yml pull jellyfin
docker compose -f services/jellyfin/docker-compose.yml up -d
docker compose -f services/jellyfin/docker-compose.yml down
```

Local health:

```bash
curl -I http://127.0.0.1:8096
docker inspect spirit-jellyfin --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
```

Rollback:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml down
```

Do not delete `/mnt/spirit-8tb/services/jellyfin/config` unless the user explicitly approves losing Jellyfin setup state.
EOF

sed -n '1,160p' docs/media-server/jellyfin-operations.md
```

Expected result:

- Operator doc exists and does not add automation.

Rollback note:

- Delete `docs/media-server/jellyfin-operations.md` if wrong.

Manual check:

- Confirm no command exposes Jellyfin publicly.

### Phase 2 Closeout Check

GO only when:

- Compose file exists and validates.
- `spirit-jellyfin` runs.
- Local HTTP `8096` responds.
- Media mounts are read-only.
- Config/cache/transcode paths persist under `/mnt/spirit-8tb/services/jellyfin`.

Closeout file:

- `docs/evidence/media-server/phase-2/phase-2-closeout.md`

## Phase 3: First Jellyfin Web Setup

Goal: complete first-run setup, create basic libraries, and prove one owned media file appears and plays.

### Increment 3.1: First-Run Admin Setup

Purpose: Complete Jellyfin wizard with a local admin user.

Allowed files:

- `docs/evidence/media-server/phase-3/increment-3.1-first-run-admin.md`

Forbidden files:

- Secrets in docs
- Screenshots containing passwords

Exact commands:

```bash
xdg-open http://127.0.0.1:8096 2>/dev/null || echo "Open http://127.0.0.1:8096 in a browser"
```

Expected result:

- Jellyfin first-run wizard opens.
- Admin account is created.
- Password is stored by the user, not committed to repo.

Rollback note:

- If setup must be restarted, stop Jellyfin and move the config directory aside only after explicit approval:

```bash
docker compose -f services/jellyfin/docker-compose.yml down
sudo mv /mnt/spirit-8tb/services/jellyfin/config /mnt/spirit-8tb/services/jellyfin/config.bad-$(date +%Y%m%dT%H%M%S)
sudo mkdir -p /mnt/spirit-8tb/services/jellyfin/config
sudo chown -R source:source /mnt/spirit-8tb/services/jellyfin/config
docker compose -f services/jellyfin/docker-compose.yml up -d
```

Manual check:

- Confirm login succeeds locally.

### Increment 3.2: Create Basic Libraries

Purpose: Add the initial categories with obvious folders.

Allowed files:

- `docs/evidence/media-server/phase-3/increment-3.2-libraries.md`

Forbidden files:

- SpiritOS `/media` UI
- Media moves/renames

Exact setup in Jellyfin UI:

```text
Library: Movies
Type: Movies
Folder: /media/movies

Library: TV Shows
Type: Shows
Folder: /media/tv

Library: Music
Type: Music
Folder: /media/music

Library: Anime
Type: Shows unless the files are movie-like, then Movies
Folder: /media/anime

Library: Other
Type: Other
Folder: /media/other
```

Expected result:

- Five libraries exist with simple names.
- Jellyfin points at container paths `/media/...`, not host paths.

Rollback note:

- Remove incorrectly created libraries in Jellyfin dashboard and recreate them.

Manual check:

- Dashboard -> Libraries shows all five folders.

### Increment 3.3: Minimal Metadata And Scanning

Purpose: Keep metadata simple for the first working server.

Allowed files:

- `docs/evidence/media-server/phase-3/increment-3.3-metadata-and-scan.md`

Forbidden files:

- Plugin installs unless user explicitly approves
- Fancy dashboard/CasaOS setup

Exact UI settings:

```text
Keep default metadata providers.
Prefer English metadata unless the user wants another language.
Do not enable advanced plugins in Phase 3.
Run "Scan All Libraries" after library creation.
```

Expected result:

- Library scan completes or reports understandable per-file issues.

Rollback note:

- Correct library folder/type and rescan.

Manual check:

- At least one library is visible on the Jellyfin home page.

### Increment 3.4: Owned Media Drop And Playback Test

Purpose: Prove playback using the user's own media.

Allowed files:

- `docs/evidence/media-server/phase-3/increment-3.4-playback-test.md`
- One user-approved test media file copied into the correct media folder

Forbidden files:

- Downloading copyrighted media
- Moving existing user media without approval

Exact commands, after choosing an owned test file:

```bash
TEST_FILE="/path/to/owned-test-file.mp4"
DEST_DIR="/mnt/spirit-8tb/media/other"
install -m 664 "$TEST_FILE" "$DEST_DIR/"
find "$DEST_DIR" -maxdepth 1 -type f -printf '%M %u %g %s %p\n' | sort | tail -20
```

Expected result:

- Test file appears in Jellyfin after a library scan.
- Playback starts in the browser.

Rollback note:

```bash
rm -i "/mnt/spirit-8tb/media/other/$(basename "$TEST_FILE")"
```

Manual check:

- Press play and confirm video/audio starts.

### Phase 3 Closeout Check

GO only when:

- Admin setup is complete.
- Libraries exist for Movies, TV Shows, Music, Anime, Other.
- At least one owned test file is visible.
- Playback starts locally.
- No SpiritOS app UI was touched.

Closeout file:

- `docs/evidence/media-server/phase-3/phase-3-closeout.md`

## Phase 4: Tailscale Access And Pretty Private Name

Goal: access Jellyfin from another device on the tailnet using a private name, not public internet exposure.

### Increment 4.1: MagicDNS Route Verification

Purpose: Use Tailscale MagicDNS and port `8096` first.

Allowed files:

- `docs/evidence/media-server/phase-4/increment-4.1-magicdns-route.md`

Forbidden files:

- Tailscale Serve/Funnel changes
- Public DNS
- Router port forwarding

Exact commands on Dell:

```bash
tailscale status --self
tailscale ip -4
tailscale status | head -40
hostname
curl -I http://127.0.0.1:8096
```

Exact commands on another Tailscale device:

```bash
tailscale status
tailscale ping <dell-tailscale-name>
curl -I http://<dell-tailscale-name>:8096
```

Expected result:

- `http://<dell-tailscale-name>:8096` opens from another tailnet device.
- If short name fails, try the full MagicDNS name: `http://<dell-tailscale-name>.<tailnet>.ts.net:8096`.

Rollback note:

- No Jellyfin rollback. If access fails, document whether DNS, ACL, firewall, or Jellyfin bind is the blocker.

Manual check:

- Open Jellyfin from a phone/laptop connected to Tailscale.

### Increment 4.2: Local Firewall Check If Needed

Purpose: Diagnose local firewall only if MagicDNS resolves but port `8096` fails.

Allowed files:

- `docs/evidence/media-server/phase-4/increment-4.2-firewall-diagnosis.md`

Forbidden files:

- Firewall changes unless user approves after diagnosis
- Public exposure

Exact read-only commands:

```bash
ss -tlnp | grep -E '(:8096)\b' || true
sudo ufw status verbose || true
tailscale ping <client-device-name> || true
```

If user approves a private-access firewall rule:

```bash
sudo ufw allow in on tailscale0 to any port 8096 proto tcp comment 'Jellyfin over Tailscale only'
sudo ufw status verbose
```

Expected result:

- Firewall allows tailnet-only access to `8096`, or the blocker is documented.

Rollback note:

```bash
sudo ufw delete allow in on tailscale0 to any port 8096 proto tcp
```

Manual check:

- Remote Tailscale device can load `http://<dell-tailscale-name>:8096`.

### Increment 4.3: Optional Tailscale Serve Private HTTPS

Purpose: Add a cleaner private HTTPS route only after plain MagicDNS works.

Allowed files:

- `docs/evidence/media-server/phase-4/increment-4.3-optional-tailscale-serve.md`

Forbidden files:

- Tailscale Funnel
- Public DNS
- Router port forwarding

Exact commands:

```bash
tailscale serve status || true
sudo tailscale serve --https=443 http://127.0.0.1:8096
tailscale serve status
```

Expected result:

- Tailscale reports a private HTTPS route like `https://<dell-tailscale-name>.<tailnet>.ts.net`.
- Access remains inside the tailnet and subject to Tailscale ACLs.

Rollback note:

```bash
sudo tailscale serve --https=443 off
tailscale serve status || true
```

Manual check:

- From another Tailscale device, open the HTTPS route and log in.

### Increment 4.4: Record Final Private Route

Purpose: Write the final working access route.

Allowed files:

- `docs/media-server/jellyfin-access.md`
- `docs/evidence/media-server/phase-4/increment-4.4-final-route.md`

Forbidden files:

- Secrets
- Public DNS records

Exact commands:

```bash
cat > docs/media-server/jellyfin-access.md <<'EOF'
# Jellyfin Access

Primary private route:

```text
http://<dell-tailscale-name>:8096
```

Optional private HTTPS route, if Tailscale Serve is enabled:

```text
https://<dell-tailscale-name>.<tailnet>.ts.net
```

This service is private Tailscale access only. Do not configure public router forwarding, Tailscale Funnel, or public DNS for Phase 1.
EOF
```

Expected result:

- Final route doc exists and identifies private-only access.

Rollback note:

- Edit or delete the doc if the route changes.

Manual check:

- Confirm the route works from another Tailscale device.

### Phase 4 Closeout Check

GO only when:

- Jellyfin opens from another Tailscale device.
- The working private route is written in `docs/media-server/jellyfin-access.md`.
- No public internet exposure was configured.

Closeout file:

- `docs/evidence/media-server/phase-4/phase-4-closeout.md`

## Phase 5: Operational Docs And Backup Awareness

Goal: document day-2 operation and backup decisions without adding automation.

### Increment 5.1: Backup Classification

Purpose: Classify Jellyfin state and media for future backup decisions.

Allowed files:

- `docs/media-server/jellyfin-backup-notes.md`
- `docs/evidence/media-server/phase-5/increment-5.1-backup-classification.md`

Forbidden files:

- Backup scripts
- Restic config
- Backup repositories

Exact commands:

```bash
cat > docs/media-server/jellyfin-backup-notes.md <<'EOF'
# Jellyfin Backup Notes

Back up after user approval:

- `/mnt/spirit-8tb/services/jellyfin/config`: critical Jellyfin server config, users, libraries, metadata database, and settings.
- `/mnt/spirit-8tb/services/jellyfin/cache`: useful but may be rebuildable depending on future cache policy.
- `/mnt/spirit-8tb/services/jellyfin/transcodes`: temporary/rebuildable, normally not backed up.
- `/mnt/spirit-8tb/media/**`: large user media. Treat as a separate backup decision from app/server config.

Do not add backup automation in Phase 5. Use the existing SpiritOS backup approval rules before any real backup, Docker volume export, prune, delete, or restore.
EOF

sed -n '1,120p' docs/media-server/jellyfin-backup-notes.md
```

Expected result:

- Backup doc distinguishes config from large media.

Rollback note:

- Delete or edit the doc if classification changes.

Manual check:

- Confirm no backup command was run.

### Increment 5.2: Reboot And Recovery Notes

Purpose: Document what to do after Dell reboots.

Allowed files:

- `docs/media-server/jellyfin-reboot-recovery.md`
- `docs/evidence/media-server/phase-5/increment-5.2-reboot-recovery.md`

Forbidden files:

- Systemd edits
- Timer installs
- Service manager changes

Exact commands:

```bash
cat > docs/media-server/jellyfin-reboot-recovery.md <<'EOF'
# Jellyfin Reboot Recovery

After Dell reboot:

```bash
findmnt /mnt/spirit-8tb
docker ps --filter name=spirit-jellyfin
docker compose -f /home/source/SpiritOS/services/jellyfin/docker-compose.yml ps
curl -I http://127.0.0.1:8096
tailscale status --self
```

If Jellyfin did not restart:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml up -d
docker logs --tail 120 spirit-jellyfin
```

If the 8 TB mount is missing, do not start Jellyfin until the mount is restored.
EOF
```

Expected result:

- Reboot procedure exists.

Rollback note:

- Delete or edit the doc if wrong.

Manual check:

- Confirm no service manager change was made.

### Increment 5.3: Update And Rollback Notes

Purpose: Document controlled update and rollback commands.

Allowed files:

- `docs/media-server/jellyfin-update-rollback.md`
- `docs/evidence/media-server/phase-5/increment-5.3-update-rollback.md`

Forbidden files:

- Automatic update tools
- Unapproved image pulls in planning run

Exact commands to document:

```bash
cat > docs/media-server/jellyfin-update-rollback.md <<'EOF'
# Jellyfin Update And Rollback

Update after user approval:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml pull jellyfin
docker compose -f services/jellyfin/docker-compose.yml up -d
docker logs --tail 120 spirit-jellyfin
curl -I http://127.0.0.1:8096
```

Rollback options:

1. If the old image is still local, pin the previous image tag in `services/jellyfin/docker-compose.yml` and run `docker compose up -d`.
2. Restore `/mnt/spirit-8tb/services/jellyfin/config` from an approved backup only if configuration corruption is confirmed.
3. Stop the service without deleting state:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml down
```

Never delete media folders as part of a Jellyfin app rollback.
EOF
```

Expected result:

- Update/rollback doc exists and avoids destructive media actions.

Rollback note:

- Delete or edit the doc if wrong.

Manual check:

- Confirm no image pull or update was actually run during doc creation.

### Phase 5 Closeout Check

GO only when:

- Operations, backup, reboot, update, and rollback docs exist.
- No backup automation was added.
- No backups, restores, prunes, deletes, or service-manager changes were run.

Closeout file:

- `docs/evidence/media-server/phase-5/phase-5-closeout.md`

## Phase 6: Final Acceptance

Goal: prove the full basic media server end state.

### Increment 6.1: Final Service Verification

Purpose: Verify local service health and persistent paths.

Allowed files:

- `docs/evidence/media-server/phase-6/increment-6.1-final-service-verification.md`

Forbidden files:

- Service changes unless fixing a documented blocker in an earlier phase

Exact commands:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml ps
docker inspect spirit-jellyfin --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
curl -I http://127.0.0.1:8096
find /mnt/spirit-8tb/services/jellyfin -maxdepth 2 -type d -printf '%M %u %g %p\n' | sort
find /mnt/spirit-8tb/media -maxdepth 2 -type d -printf '%M %u %g %p\n' | sort
```

Expected result:

- Jellyfin is running and local HTTP responds.

Rollback note:

- Stop service with `docker compose -f services/jellyfin/docker-compose.yml down` if final verification reveals a severe misconfiguration.

Manual check:

- Open Jellyfin locally.

### Increment 6.2: Final Tailscale Playback Verification

Purpose: Prove playback from another Tailscale device.

Allowed files:

- `docs/evidence/media-server/phase-6/increment-6.2-final-tailscale-playback.md`

Forbidden files:

- Public exposure

Exact checks:

```text
1. From another Tailscale device, open the final route documented in docs/media-server/jellyfin-access.md.
2. Log in.
3. Open the library containing the test media file.
4. Start playback.
5. Record final route, client device type, and result in the evidence file.
```

Expected result:

- Playback starts from another device over Tailscale.

Rollback note:

- Disable optional Tailscale Serve with `sudo tailscale serve --https=443 off` if HTTPS route is wrong.
- Keep plain `http://<dell-tailscale-name>:8096` as the fallback private route.

Manual check:

- User confirms playback starts.

### Increment 6.3: Final Docs And Verification Block

Purpose: Close the lane with one copy-paste verification block.

Allowed files:

- `docs/evidence/media-server/phase-6/phase-6-closeout.md`
- `docs/media-server/jellyfin-final-status.md`

Forbidden files:

- Source UI
- Existing production compose files unless already approved in Phase 2

Exact commands:

```bash
cat > docs/media-server/jellyfin-final-status.md <<'EOF'
# Jellyfin Final Status

Status: GO when all Phase 6 acceptance checks pass.

Final private route:

```text
TODO: write working route here.
```

Acceptance:

- Jellyfin container running on Dell.
- Jellyfin opens locally on Dell/LAN.
- Jellyfin opens over Tailscale.
- At least one library exists.
- At least one test media file is visible.
- Playback starts from another Tailscale device.
- No public internet exposure configured.
- SpiritOS `/media` UI untouched.
EOF
```

Expected result:

- Final status doc records the route and acceptance.

Rollback note:

- Edit the final status doc if route or acceptance changes.

Manual check:

- User runs final verification block and confirms GO.

### Phase 6 Closeout Check

Implementation is complete only when all are true:

- Jellyfin container is running on Dell.
- Jellyfin opens locally on Dell/LAN.
- Jellyfin opens over Tailscale.
- At least one library is created.
- At least one test media file is visible in Jellyfin.
- Playback starts from another device.
- The final route/domain/name is written in docs.
- A final single copy-paste terminal verification block has been provided.

Closeout file:

- `docs/evidence/media-server/phase-6/phase-6-closeout.md`

## Current Planning-Run Self-Check

Run from the Windows checkout after this planning run:

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

Expected result:

- Both required docs exist.
- `git diff --name-only -- <forbidden>` prints nothing for forbidden tracked files.
- `git status --short -- docs/media-server` shows only the new docs created by this planning run.

## Handoff Summary

The next Codex/chat should begin at Phase 0, not Phase 1, because live host/mount/Docker/Tailscale state must be revalidated immediately before any writes. After Phase 0 is GO, proceed increment by increment. Do not install Jellyfin, start containers, touch firewall, or write `/mnt/spirit-8tb` until the relevant phase explicitly allows it and the user has approved execution.
