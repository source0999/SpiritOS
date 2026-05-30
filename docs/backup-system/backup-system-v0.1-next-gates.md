# Backup System v0.1 Next Gates

Date/time: 2026-05-29T16:13:37-04:00

## 1. Scheduler install gate

Purpose: Install approved recurring jobs after manual preflight.

What it can change: It may install approved systemd timers, launchd jobs, or Windows scheduled tasks only for approved lanes.

What it must not change: It must not run prune, forget, cloud sync, destructive cleanup, or container restarts. It must not silently include Windows until Windows backup is GO or explicitly excluded.

Manual checks: Verify scheduler templates, users, permissions, repo path, password file path, logs path, dry-runs, and disable steps.

GO/NO-GO criteria: GO only if every scheduled lane has a proven manual command and rollback path. NO-GO if Windows is claimed without proof or if prune/cloud sync is bundled.

## 2. Backup dashboard/status UI gate

Purpose: Add a visible status surface for last backup time, lane freshness, restore proof, and NO-GO/deferred items.

What it can change: It may add read-only status parsing and UI docs/components.

What it must not change: It must not trigger backups, read secrets, install schedulers, or mutate restic repositories.

Manual checks: Verify status data source, stale thresholds, no secret exposure, and UI rendering.

GO/NO-GO criteria: GO only if dashboard is read-only and reflects Windows NO-GO honestly. NO-GO if it overclaims protected lanes.

## 3. Offsite encrypted mirror planning gate

Purpose: Design an offsite encrypted mirror strategy without syncing yet.

What it can change: It may create planning docs, threat model, cost model, and candidate provider notes.

What it must not change: It must not run cloud sync, rclone, remote writes, deletes, or credential installation.

Manual checks: Verify target provider, encryption model, bandwidth/cost expectations, secrets storage, and dry-run plan.

GO/NO-GO criteria: GO only for a written plan. NO-GO for any attempted sync or credential leakage.

## 4. Retention/prune simulation gate

Purpose: Model retention rules before any destructive action.

What it can change: It may run non-destructive policy simulations and create docs/evidence.

What it must not change: It must not run `restic forget`, `restic prune`, delete snapshots, or delete staging/restore files.

Manual checks: Verify policy, expected kept snapshots, expected removal candidates, and restore implications.

GO/NO-GO criteria: GO only if simulation is non-destructive and reviewed. NO-GO if real prune/delete is included.

## 5. Retention/prune real gate

Purpose: Execute approved retention after simulation and operator approval.

What it can change: It may run the exact approved real retention command.

What it must not change: It must not be bundled with scheduler install, cloud sync, unrelated cleanup, or unreviewed retention rules.

Manual checks: Re-run snapshot inventory, confirm simulation evidence, confirm backup freshness, confirm restore proof, and record exact command.

GO/NO-GO criteria: GO only with explicit approval after simulation. NO-GO if repository health or restore proof is stale.

## 6. Full disaster recovery drill gate

Purpose: Prove recovery beyond single-file restore drills.

What it can change: It may restore selected snapshots into isolated disaster-recovery drill directories and document recovery steps.

What it must not change: It must not restore over live `/home/source/SpiritOS`, restart containers, overwrite live data, or expose secrets.

Manual checks: Verify isolated target, selected snapshots, included paths, restored counts, integrity checks, and cleanup policy.

GO/NO-GO criteria: GO only if isolated restore validates expected files without touching live services. NO-GO if live data would be overwritten.

## 7. Ollama model backup/export decision gate

Purpose: Decide whether and how to protect Ollama model data.

What it can change: It may inventory sizes by metadata, assess rebuildability, and design a backup/export lane.

What it must not change: It must not export or copy Ollama data until explicitly approved.

Manual checks: Verify volume/path size, rebuild cost, privacy concerns, storage impact, and restore expectations.

GO/NO-GO criteria: GO only for an approved design or explicit defer decision. NO-GO if large model data is copied without approval.
