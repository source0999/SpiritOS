# Manual Run Results

Manual watcher run is `BLOCKED`.

The installed scripts passed the local forbidden-string safety scan, but `/mnt/spirit-8tb/spiritos-health/` does not exist and cannot be created without sudo from this session. Passwordless sudo is not available:

```text
sudo: a password is required
sudo_not_available
```

Because watchers must write logs under `/mnt/spirit-8tb/spiritos-health/`, I did not run the watcher scripts as a substitute against another path. No unapproved output path was used.

Raw evidence:

- `raw/30-permission-blocker.txt`
- `raw/31-health-dir-status.txt`
