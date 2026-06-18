# Systemd Install Results

Verdict: `BLOCKED`

Systemd install remains blocked because `sudo -n true` still returns `sudo: a password is required` from this SSH command path. No unit files were copied to `/etc/systemd/system`, no `systemctl daemon-reload` was run, and no timer/service was enabled.

## Safe Unit Names Planned

- `spiritos-health-snapshot.service`
- `spiritos-health-snapshot.timer`
- `spiritos-boot-postmortem.service`

## Recommended Unit Content For Later Sudo Install

`/etc/systemd/system/spiritos-health-snapshot.service`:

```ini
[Unit]
Description=SpiritOS health snapshot (safe read-only)

[Service]
Type=oneshot
WorkingDirectory=/home/source/SpiritOS
ExecStart=/home/source/SpiritOS/scripts/spiritos-health/spiritos-host-health-snapshot.sh
ExecStart=/home/source/SpiritOS/scripts/spiritos-health/spiritos-service-health-snapshot.sh
ExecStart=/home/source/SpiritOS/scripts/spiritos-health/spiritos-model-storage-guard.sh
ExecStart=/home/source/SpiritOS/scripts/spiritos-health/spiritos-repo-bloat-report.sh
```

`/etc/systemd/system/spiritos-health-snapshot.timer`:

```ini
[Unit]
Description=Run SpiritOS health snapshot periodically

[Timer]
OnBootSec=10min
OnUnitActiveSec=30min
Persistent=true

[Install]
WantedBy=timers.target
```

`/etc/systemd/system/spiritos-boot-postmortem.service`:

```ini
[Unit]
Description=SpiritOS boot postmortem snapshot (safe read-only)
After=multi-user.target

[Service]
Type=oneshot
WorkingDirectory=/home/source/SpiritOS
ExecStart=/home/source/SpiritOS/scripts/spiritos-health/spiritos-boot-postmortem.sh

[Install]
WantedBy=multi-user.target
```
