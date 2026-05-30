# Backup System v0.1 Scheduler Install Checklist

Date/time: 2026-05-29T16:13:37-04:00

## Current Stop Point

Stop here before real install.

This checklist does not install timers, launchd jobs, Windows scheduled tasks, cloud sync, prune jobs, forget jobs, or destructive cleanup.

## Pre-install Checks

- Confirm scheduler scope: all-node install is NO-GO until Windows is proven or explicitly excluded.
- Confirm latest master status doc is reviewed.
- Confirm restic repository path is reachable: `/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server`
- Confirm restic password file path exists without printing contents: `/home/source/.config/spiritos-backup/restic-source-server.pass`
- Confirm staging, restore-drills, and logs directories exist and are writable by the scheduler user.
- Confirm each backup lane has a manual command that has already passed.
- Confirm no prune, forget, delete, cloud sync, or destructive cleanup is included.

## Exact Files/Templates To Use

- Dell systemd service example: `docs/backup-system/templates/spiritos-backup-dell.service.example`
- Dell systemd timer example: `docs/backup-system/templates/spiritos-backup-dell.timer.example`
- Mac launchd example: `docs/backup-system/templates/spiritos-backup-mac-launchd.plist.example`
- Windows Task Scheduler example: `docs/backup-system/templates/spiritos-backup-windows-task.xml.example`
- Scheduler readiness doc: `docs/backup-system/backup-system-v0.1-scheduler-readiness.md`
- Master status doc: `docs/backup-system/backup-system-v0.1-master-status.md`

## Required Env/Password Files

- Restic password files must stay outside the repo.
- Required env files must stay outside committed evidence if they contain secrets.
- Logs must record paths and non-secret summaries only.
- Do not print `.env`, `.env.local`, restic password files, SSH keys, tokens, certs, private keys, or passwords.

## User/Permissions Assumptions

- Dell scheduler jobs should run as the approved user that can read the restic password file and write to backup paths.
- Mac jobs must run as an approved Mac user with access to the selected checkout and approved backup command.
- Windows jobs must run as an approved Windows user with access to the selected path scope.
- Any service account must have the least privileges needed for its lane.

## How To Test Timers Manually

- Run each service command manually in dry-run or safe preflight mode first.
- Run only the exact lane under review.
- Confirm exit code and non-secret log output.
- Confirm restic snapshot metadata only after a real approved backup gate.
- For restore drills, restore only into isolated restore-drill directories.

## How To Disable Timers

- systemd: disable and stop the approved timer name, then verify it is inactive.
- launchd: unload/bootout the approved plist, then verify it is not scheduled.
- Windows Task Scheduler: disable the approved task, then verify next run time is absent or disabled.
- Record disable proof in evidence after any install gate.

## How To Read Logs

- Read only non-secret logs.
- Prefer timestamps, lane names, exit codes, snapshot IDs, and path-only summaries.
- Do not paste secret-bearing command lines or env values into evidence.
- Treat unexpected secret output as NO-GO and rotate affected credentials if needed.

## How To Verify A Backup Happened

- Run `restic snapshots` against the approved repository.
- Verify expected hostname, tags, and timestamp.
- Verify lane-specific staging files by names, sizes, and counts only.
- Run lightweight `restic check` on the approved cadence.
- Run isolated restore proof according to the restore drill checklist.

## Rollback Plan

- Disable the installed timer/task.
- Confirm no future run is scheduled.
- Preserve logs and evidence.
- Do not delete snapshots as part of rollback.
- Revert only scheduler install files outside repo docs/templates if explicitly approved.
- Re-run lightweight `restic check` after rollback if repository health is in question.

## Stop Point Before Real Install

Stop before copying templates into system scheduler locations or enabling any timer/task.

Required approval text for the next gate should identify:

- Lanes to schedule.
- Lanes excluded.
- Exact scheduler user.
- Exact templates to install.
- Manual commands already proven.
- Rollback command plan.
- Confirmation that prune, forget, cloud sync, and destructive cleanup are excluded.
