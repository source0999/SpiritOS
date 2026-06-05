# SpiritFlix Force OSD Hide Patch

Status: server-side patch applied after user proved the previous overlay existed but the native Jellyfin controls were still visible.

Live files changed on the Dell host:

```text
/mnt/spirit-8tb/services/jellyfin/web-overrides/index.html
/mnt/spirit-8tb/services/jellyfin/web-overrides/spirit-player-enhancer.css
/mnt/spirit-8tb/services/jellyfin/web-overrides/spirit-player-enhancer.js
```

Backups created:

```text
/mnt/spirit-8tb/services/jellyfin/web-overrides/backups/index.html.before-20260605T0105Z-spiritflix-force-osd.bak
/mnt/spirit-8tb/services/jellyfin/web-overrides/backups/spirit-player-enhancer.css.before-20260605T0105Z-spiritflix-force-osd.bak
/mnt/spirit-8tb/services/jellyfin/web-overrides/backups/spirit-player-enhancer.js.before-20260605T0105Z-spiritflix-force-osd.bak
```

What changed:

```text
VERSION = 20260605T0105Z-spiritflix-force-osd
Added JS-side native Jellyfin OSD/control hiding via data-spiritflix-native-hidden.
Kept the SpiritFlix overlay awake instead of letting it auto-sleep.
Raised .spiritflix-player z-index to 2147483647.
Recreated the Jellyfin container so read-only file bind mounts serve the new file contents.
```

Server-side verification:

```text
node --check /mnt/spirit-8tb/services/jellyfin/web-overrides/spirit-player-enhancer.js
PASS

curl http://127.0.0.1:8096/web/spirit-player-enhancer.js?spiritos=20260605T0105Z-spiritflix-force-osd
served marker: VERSION = 20260605T0105Z-spiritflix-force-osd

curl http://127.0.0.1:8096/web/spirit-player-enhancer.css?spiritos=20260605T0105Z-spiritflix-force-osd
served marker: z-index: 2147483647

docker ps --filter name=spirit-jellyfin
spirit-jellyfin Up healthy on 8096
```
