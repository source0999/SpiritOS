# Increment 1.2 Mac Restic Install Attempt

Date: 2026-05-29

Scope:

- Mac node only.
- Approval granted by Britton: install `restic`.

Checks run:

- SSH to `spirit-mac-mini`: PASS
- macOS version check: PASS
- `command -v restic && restic version || true`: PASS command execution, restic not found
- `command -v brew || true`: PASS command execution, Homebrew not found in PATH
- `command -v port || true`: PASS command execution, MacPorts not found in PATH
- common binary location check for `/opt/homebrew/bin/brew`, `/usr/local/bin/brew`, `/opt/local/bin/port`, and common `restic` paths: PASS command execution, none found
- `git diff --check`: PASS

Observed:

```text
spirit-mac-mini.local
spiritmac
ProductName: macOS
ProductVersion: 15.7.7
BuildVersion: 24G720
```

Result: NO-GO.

Reason:

`restic` is not installed on the Mac, and no approved package manager path was available. Approval to install `restic` does not imply approval to install Homebrew/MacPorts or download and install a standalone binary from the internet.

No install command was run.

Safety:

- No Mac backup ran.
- No Mac data was copied.
- No Mac restic repo was initialized.
- No package manager was installed.
- No DB dumps ran.
- No Docker volume exports ran.
- No Windows backup ran.
- No containers were stopped or restarted.
- No timers were installed.
- No cloud sync ran.
- No pruning/deletion ran.
- No commit/push ran.
- No secrets were printed.
