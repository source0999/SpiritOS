# Increment 6.1 Final Service Verification

Purpose:

- Verify local service health and persistent paths.

Commands:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml ps
docker inspect spirit-jellyfin --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
curl -I http://127.0.0.1:8096
find /mnt/spirit-8tb/services/jellyfin -maxdepth 2 -type d -printf '%M %u %g %p\n' | sort
find /mnt/spirit-8tb/media -maxdepth 2 -type d -printf '%M %u %g %p\n' | sort
find /mnt/spirit-8tb/media -maxdepth 2 -type f -printf '%M %u %g %s %p\n' | sort
```

Output summary:

```text
spirit-jellyfin   jellyfin/jellyfin:latest   Up 39 minutes (healthy)   0.0.0.0:8096->8096/tcp, [::]:8096->8096/tcp
running healthy
HTTP/1.1 302 Found
Location: web/
drwxrwxr-x source source /mnt/spirit-8tb/services/jellyfin/config
drwxrwxr-x source source /mnt/spirit-8tb/services/jellyfin/cache
drwxrwxr-x source source /mnt/spirit-8tb/services/jellyfin/transcodes
drwxrwxr-x source source /mnt/spirit-8tb/media/movies
drwxrwxr-x source source /mnt/spirit-8tb/media/tv
drwxrwxr-x source source /mnt/spirit-8tb/media/music
drwxrwxr-x source source /mnt/spirit-8tb/media/anime
drwxrwxr-x source source /mnt/spirit-8tb/media/other
-rw-rw-r-- source source 392858929 /mnt/spirit-8tb/media/other/2024-07-23 01-17-41.mp4
-rw-rw-r-- source source 701222377 /mnt/spirit-8tb/media/other/2024-07-23 01-27-43.mp4
```

Manual check:

- Jellyfin opens locally.
- Browser playback remains `USER_MANUAL_CHECK_PENDING`.

Status: GO_TERMINAL_SAFE
