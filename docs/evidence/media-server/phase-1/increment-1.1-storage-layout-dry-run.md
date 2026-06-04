# Increment 1.1 Storage Layout Dry Run

Purpose:

- Preview the exact directories to create before writing to `/mnt/spirit-8tb`.

Command:

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

Result:

```text
WOULD_CREATE /mnt/spirit-8tb/media/movies
WOULD_CREATE /mnt/spirit-8tb/media/tv
WOULD_CREATE /mnt/spirit-8tb/media/music
WOULD_CREATE /mnt/spirit-8tb/media/anime
WOULD_CREATE /mnt/spirit-8tb/media/other
WOULD_CREATE /mnt/spirit-8tb/services/jellyfin/config
WOULD_CREATE /mnt/spirit-8tb/services/jellyfin/cache
WOULD_CREATE /mnt/spirit-8tb/services/jellyfin/transcodes
TARGET          SOURCE    FSTYPE OPTIONS
/mnt/spirit-8tb /dev/sda1 ext4   rw,relatime
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       7.3T   60G  6.8T   1% /mnt/spirit-8tb
```

Manual check:

- Folder names match the desired simple categories: Movies, TV Shows, Music, Anime, Other.
- No directories were created by this dry-run increment.

Rollback:

- No filesystem rollback needed.

Status: GO
