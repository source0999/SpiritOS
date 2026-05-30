# Increment 1.3R Restic Installed After Manual Sudo

Date: 2026-05-29

Checks run:

- `command -v restic`: PASS
- `restic version`: PASS
- `git diff --check`: PASS

Observed:

```text
/usr/bin/restic
restic 0.16.4 compiled with go1.22.2 on linux/amd64
```

Result: GO. Restic is now available after Britton's manual install outside Codex. No real backup has run yet in this resumed gate.
