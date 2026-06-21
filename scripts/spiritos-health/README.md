# SpiritOS read-only health watchers

Installed watcher scripts for safe runtime snapshots. These scripts write logs
under `/mnt/spirit-8tb/spiritos-health/`, use lock files, do not restart
services or terminate processes, and do not dump shell variables.
