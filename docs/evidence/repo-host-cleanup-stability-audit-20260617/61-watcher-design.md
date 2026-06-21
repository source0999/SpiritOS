# Watcher Design

No watchers were installed. This is an approval-gated design only.

## host-health-recorder
- Purpose: records uptime, boot id, disk, memory, load, thermal if available, and journal tails
- Exact files it would create: `/mnt/spirit-8tb/spiritos-health/host/YYYYMMDD-HHMMSS.jsonl`
- Proposed systemd unit/timer or cron entry: `spiritos-host-health.service + spiritos-host-health.timer`
- Exact install command later: `sudo cp docs/ops/systemd/spiritos-host-health.* /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now spiritos-host-health.timer`
- Exact disable/remove command later: `sudo systemctl disable --now spiritos-host-health.timer && sudo rm /etc/systemd/system/spiritos-host-health.*`
- Risk: low
- Can run manually first: yes: run the recorder script once manually
- Approval needed: approval to add script/config and install timer

## service-health-checker
- Purpose: checks Source Proxy, Next, Ollama, Docker, SearXNG, and Jellyfin when applicable
- Exact files it would create: `/mnt/spirit-8tb/spiritos-health/services/YYYYMMDD-HHMMSS.json`
- Proposed systemd unit/timer or cron entry: `spiritos-service-health.service + timer`
- Exact install command later: `sudo cp docs/ops/systemd/spiritos-service-health.* /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now spiritos-service-health.timer`
- Exact disable/remove command later: `sudo systemctl disable --now spiritos-service-health.timer && sudo rm /etc/systemd/system/spiritos-service-health.*`
- Risk: medium
- Can run manually first: yes: run curl/process checks once manually
- Approval needed: approval to define service list and alert behavior

## crash-reboot-postmortem
- Purpose: on boot captures previous boot journal warnings and reboot clues
- Exact files it would create: `/mnt/spirit-8tb/spiritos-health/boots/BOOTID-postmortem.md`
- Proposed systemd unit/timer or cron entry: `spiritos-boot-postmortem.service WantedBy=multi-user.target`
- Exact install command later: `sudo cp docs/ops/systemd/spiritos-boot-postmortem.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable spiritos-boot-postmortem.service`
- Exact disable/remove command later: `sudo systemctl disable spiritos-boot-postmortem.service && sudo rm /etc/systemd/system/spiritos-boot-postmortem.service`
- Risk: low
- Can run manually first: yes: run collector manually against -b -1
- Approval needed: approval to install boot-time unit

## model-storage-guard
- Purpose: verifies Ollama paths resolve under /mnt/spirit-8tb and alerts on OS-disk model storage
- Exact files it would create: `/mnt/spirit-8tb/spiritos-health/model-storage/YYYYMMDD-HHMMSS.json`
- Proposed systemd unit/timer or cron entry: `spiritos-model-storage-guard.service + timer`
- Exact install command later: `sudo cp docs/ops/systemd/spiritos-model-storage-guard.* /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now spiritos-model-storage-guard.timer`
- Exact disable/remove command later: `sudo systemctl disable --now spiritos-model-storage-guard.timer && sudo rm /etc/systemd/system/spiritos-model-storage-guard.*`
- Risk: low
- Can run manually first: yes: run readlink/df checks once manually
- Approval needed: approval to install timer and choose alert channel

## repo-bloat-guard
- Purpose: reports new generated artifact growth and suggests ignores/archive moves without deleting
- Exact files it would create: `/mnt/spirit-8tb/spiritos-health/repo-bloat/YYYYMMDD-HHMMSS.json`
- Proposed systemd unit/timer or cron entry: `spiritos-repo-bloat-guard.service + timer`
- Exact install command later: `sudo cp docs/ops/systemd/spiritos-repo-bloat-guard.* /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now spiritos-repo-bloat-guard.timer`
- Exact disable/remove command later: `sudo systemctl disable --now spiritos-repo-bloat-guard.timer && sudo rm /etc/systemd/system/spiritos-repo-bloat-guard.*`
- Risk: low
- Can run manually first: yes: run inventory once manually
- Approval needed: approval to add repo script/config and timer
