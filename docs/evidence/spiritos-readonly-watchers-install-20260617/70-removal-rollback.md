# Removal / Rollback

No systemd watcher units or timers were installed by this run, so there is no systemd rollback currently required.

If a later sudo install is performed, rollback commands are:

```bash
sudo systemctl disable --now spiritos-health-snapshot.timer
sudo systemctl disable spiritos-boot-postmortem.service
sudo rm -f /etc/systemd/system/spiritos-health-snapshot.service
sudo rm -f /etc/systemd/system/spiritos-health-snapshot.timer
sudo rm -f /etc/systemd/system/spiritos-boot-postmortem.service
sudo systemctl daemon-reload
```

Repo watcher scripts should be removed only with separate approval:

```bash
rm -rf scripts/spiritos-health
```

Health logs under `/mnt/spirit-8tb/spiritos-health/` should be preserved by default. Remove them only with separate explicit approval.
