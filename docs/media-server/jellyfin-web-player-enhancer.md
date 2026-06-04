# Jellyfin Web Player Enhancer

SpiritOS uses the existing Jellyfin Web UI on port `8096` for this player lane. It does not use a separate SpiritOS `/media` frontend.

Live private route:

```text
http://spirit.tailb69ea6.ts.net:8096/web/#/home
```

Override location on the Dell:

```text
/mnt/spirit-8tb/services/jellyfin/web-overrides/
```

Installed override files:

- `index.html`
- `spirit-player-enhancer.js`
- `spirit-player-enhancer.css`
- `README.md`

The enhancer is injected into Jellyfin Web through read-only bind mounts in `services/jellyfin/docker-compose.yml`. It observes the DOM for the active Jellyfin `<video>` element and adds one scoped overlay with `data-spirit-player-enhancer`.

Preferences are stored in browser localStorage under:

```text
spiritJellyfinPlayerEnhancer:v1
```

Rollback:

1. Remove the `web-overrides` bind mounts from `services/jellyfin/docker-compose.yml`.
2. Run `docker compose -f /home/source/SpiritOS/services/jellyfin/docker-compose.yml up -d`.
3. Confirm `curl -I http://127.0.0.1:8096/web/` returns OK.

Do not expose this Jellyfin service publicly, use Tailscale Funnel, or move playback into a new SpiritOS `/media` app.
