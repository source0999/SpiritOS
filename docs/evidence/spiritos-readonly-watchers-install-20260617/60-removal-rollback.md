# Removal / Rollback Instructions Not Executed

These commands are documentation only and were not run.

## If systemd units are later installed

```bash
sudo systemctl disable --now spiritos-health-snapshot.timer
sudo rm -f /etc/systemd/system/spiritos-health-snapshot.service
sudo rm -f /etc/systemd/system/spiritos-health-snapshot.timer
sudo rm -f /etc/systemd/system/spiritos-boot-postmortem.service
sudo systemctl daemon-reload
```

## Repo watcher scripts

If Britton approves removal of the approved repo watcher scripts later:

```bash
rm -rf scripts/spiritos-health
```

Do not run that as part of this install task. Health logs under `/mnt/spirit-8tb/spiritos-health/` should be preserved unless Britton separately approves deletion.
