# Jellyfin Backup Notes

Back up after user approval:

- `/mnt/spirit-8tb/services/jellyfin/config`: critical Jellyfin server config, users, libraries, metadata database, and settings.
- `/mnt/spirit-8tb/services/jellyfin/cache`: useful but may be rebuildable depending on future cache policy.
- `/mnt/spirit-8tb/services/jellyfin/transcodes`: temporary/rebuildable, normally not backed up.
- `/mnt/spirit-8tb/media/**`: large user media. Treat as a separate backup decision from app/server config.

Do not add backup automation in Phase 5. Use the existing SpiritOS backup approval rules before any real backup, Docker volume export, prune, delete, or restore.
