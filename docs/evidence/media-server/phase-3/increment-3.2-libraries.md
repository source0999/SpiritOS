# Increment 3.2 Libraries

Purpose:

- Add the initial categories with obvious folders.

Pre-check commands:

```bash
cd /home/source/SpiritOS
docker inspect spirit-jellyfin --format 'CONTAINER_STATE {{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
curl -fsS http://127.0.0.1:8096/System/Info/Public
find /mnt/spirit-8tb/media -maxdepth 1 -type d -printf '%M %u %g %p\n' | sort
find /mnt/spirit-8tb/services/jellyfin/config -maxdepth 5 -type f | grep -Ei 'library|collection' | wc -l
```

Pre-check output:

```text
CONTAINER_STATE running healthy
StartupWizardCompleted:false
0
drwxrwxr-x source source /mnt/spirit-8tb/media
drwxrwxr-x source source /mnt/spirit-8tb/media/anime
drwxrwxr-x source source /mnt/spirit-8tb/media/movies
drwxrwxr-x source source /mnt/spirit-8tb/media/music
drwxrwxr-x source source /mnt/spirit-8tb/media/other
drwxrwxr-x source source /mnt/spirit-8tb/media/tv
```

Required manual UI steps:

1. Open `http://127.0.0.1:8096` on the Dell, or open the private Tailscale route from another trusted device.
2. Finish any remaining first-run wizard page until Jellyfin no longer reports startup wizard mode.
3. Go to Dashboard.
4. Open Libraries.
5. Add media library:
   - Content type: Movies
   - Display name: Movies
   - Folder: `/media/movies`
6. Add media library:
   - Content type: Shows
   - Display name: TV Shows
   - Folder: `/media/tv`
7. Add media library:
   - Content type: Music
   - Display name: Music
   - Folder: `/media/music`
8. Add media library:
   - Content type: Shows, unless the files are movie-like
   - Display name: Anime
   - Folder: `/media/anime`
9. Add media library:
   - Content type: Other
   - Display name: Other
   - Folder: `/media/other`
10. Save each library.

Manual check:

- Dashboard -> Libraries shows Movies, TV Shows, Music, Anime, and Other.
- Library folder paths are container paths under `/media/...`, not host paths under `/mnt/spirit-8tb/...`.
- No media files are moved, renamed, or deleted.
- No SpiritOS `/media` UI file is edited.

Rollback:

- Remove incorrectly created libraries in the Jellyfin dashboard and recreate them with the container paths above.

Status: BLOCKED_ON_USER_LIBRARY_UI

Follow-up after user completed the wizard:

```bash
find /mnt/spirit-8tb/services/jellyfin/config/root/default -maxdepth 2 -type f | grep -Ei 'mblink|collection|options' | sort
for file in /mnt/spirit-8tb/services/jellyfin/config/root/default/*/*.mblink; do
  printf '%s -> ' "$file"
  sed -n '1p' "$file"
done
```

Follow-up output:

```text
/mnt/spirit-8tb/services/jellyfin/config/root/default/Anime/anime.mblink -> /media/anime
/mnt/spirit-8tb/services/jellyfin/config/root/default/Home Videos and Photos/other.mblink -> /media/other
/mnt/spirit-8tb/services/jellyfin/config/root/default/Movies/movies.mblink -> /media/movies
/mnt/spirit-8tb/services/jellyfin/config/root/default/Music/music.mblink -> /media/music
/mnt/spirit-8tb/services/jellyfin/config/root/default/Shows/tv.mblink -> /media/tv
```

Library verification:

- Movies maps to `/media/movies`: GO
- TV folder maps to `/media/tv`: GO
- Music maps to `/media/music`: GO
- Anime maps to `/media/anime`: GO
- Other folder maps to `/media/other`: GO

Display-name note:

- Jellyfin config uses `Shows` for the TV library rather than the plan-preferred display name `TV Shows`.
- Jellyfin config uses `Home Videos and Photos` for the Other library rather than the plan-preferred display name `Other`.
- The folder mappings are correct and use container paths, not host paths.

Follow-up status: PARTIAL-GO
