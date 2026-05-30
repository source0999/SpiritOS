# Increment 1.3 Restic Availability

Date: 2026-05-29

Checks run:

- `command -v restic && restic version || true`: PASS command execution, restic missing

Approved install command printed before execution:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends restic
```

Install attempt result:

```text
sudo: a terminal is required to read the password; either use the -S option to read from standard input or configure an askpass helper
sudo: a password is required
```

Follow-up check:

```text
id -u: 1000
whoami: source
restic: still unavailable
```

Result: NO-GO. Restic is not available, and this Codex session cannot install it because `sudo` requires an interactive password.

No other packages were installed.
