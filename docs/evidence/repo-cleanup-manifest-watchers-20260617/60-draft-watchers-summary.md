# Draft Watchers Summary

Draft watcher scripts and systemd examples were written under `drafts/` only. They use lock files, write to `/mnt/spirit-8tb/spiritos-health/` if installed later, degrade with `|| true`, avoid env dumps, and mark service health without restarting anything.
