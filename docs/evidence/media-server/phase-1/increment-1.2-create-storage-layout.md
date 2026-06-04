# Increment 1.2 Create Storage Layout

Purpose:

- Create the minimum persistent directory structure after user approval to execute Phase 1.

Original non-interactive command attempted:

```bash
sudo -n mkdir -p \
  /mnt/spirit-8tb/media/movies \
  /mnt/spirit-8tb/media/tv \
  /mnt/spirit-8tb/media/music \
  /mnt/spirit-8tb/media/anime \
  /mnt/spirit-8tb/media/other \
  /mnt/spirit-8tb/services/jellyfin/config \
  /mnt/spirit-8tb/services/jellyfin/cache \
  /mnt/spirit-8tb/services/jellyfin/transcodes
```

Original result:

```text
sudo: a password is required
```

Follow-up verification after user ran the sudo directory creation commands manually:

```bash
hostname
pwd
findmnt /mnt/spirit-8tb
find /mnt/spirit-8tb/media -maxdepth 2 -type d -printf '%M %u %g %p\n' | sort
find /mnt/spirit-8tb/services/jellyfin -maxdepth 2 -type d -printf '%M %u %g %p\n' | sort
```

Follow-up verification output:

```text
source-server
/home/source
TARGET          SOURCE    FSTYPE OPTIONS
/mnt/spirit-8tb /dev/sda1 ext4   rw,relatime
drwxrwxr-x source source /mnt/spirit-8tb/media
drwxrwxr-x source source /mnt/spirit-8tb/media/anime
drwxrwxr-x source source /mnt/spirit-8tb/media/movies
drwxrwxr-x source source /mnt/spirit-8tb/media/music
drwxrwxr-x source source /mnt/spirit-8tb/media/other
drwxrwxr-x source source /mnt/spirit-8tb/media/tv
drwxrwxr-x source source /mnt/spirit-8tb/services/jellyfin
drwxrwxr-x source source /mnt/spirit-8tb/services/jellyfin/cache
drwxrwxr-x source source /mnt/spirit-8tb/services/jellyfin/config
drwxrwxr-x source source /mnt/spirit-8tb/services/jellyfin/transcodes
```

Manual check:

- The user ran the approved sudo commands on the Dell/source server.
- All target media and Jellyfin service directories now exist.
- Ownership is `source:source`.
- Permissions are `775` and are not world-writable.
- No existing media contents were moved, renamed, deleted, or scanned deeply.

Rollback:

- Only remove the newly created directories if they are empty and the user explicitly approves rollback.

Status: GO
