# SpiritOS Backup System v0.1 Contract

Date: 2026-05-29

## Purpose

SpiritOS Backup System v0.1 defines a dry-run-first backup lane for the Dell/source-server 8TB drive and connected Mac and Windows nodes. It protects runtime state that GitHub and Repomix do not capture, while refusing real writes until Britton explicitly approves the relevant gate.

## Backup Classes

- Class A: source and docs. Repo source, scripts, docs, runbooks, evidence, config examples, compose files, receipts, and logs that are safe to copy.
- Class B: runtime data. `.spirit-backups`, `source_proxy/.spirit-backups`, `source_proxy/data`, Scout data, backend runtime data, evidence, receipts, and logs.
- Class C: Docker/database state. Docker named volumes such as `source_postgres_data`, `ollama_data`, `whisper_cache`, `openedai_voices`, and `searxng_data`, plus database logical dumps planned through approved commands.
- Class D: node-specific state. Mac worker checkout and overlay paths under `/Users/spiritmac/spiritos-worker/SpiritOS`, plus Windows project scope centered around `C:\Projects`.
- Class E: rebuildable caches. `node_modules`, `.next`, `dist`, package manager caches, Repomix outputs, temporary caches, and generated artifacts.
- Class F: secrets and credentials. `.env`, `.env.local`, private keys, tokens, certificates, credential stores, password files, and any secret-shaped path.

## Default Safety

- Default behavior is `dry-run` and read-only.
- Scripts may print planned commands and path names.
- Scripts must not print secret contents.
- Scripts must not copy data to `/mnt/spirit-8tb` unless `SPIRIT_BACKUP_MODE=real` and `SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES=true` are deliberately provided after Britton approval.

## Critical Action Gates

Critical action approval is required before installing packages, initializing a restic repo, creating real backup directories on `/mnt/spirit-8tb`, reading or copying secret contents, dumping live databases, exporting Docker volumes, stopping or modifying containers, running a real backup, running a real restore, scheduling timers, pruning, deleting, syncing offsite, committing, pushing, merging, stashing, or cleaning the repo.

## No-Delete Policy

v0.1 is no-delete and no-prune. Retention policy examples may be documented, but prune, forget, expire, clean, and delete commands are blocked until a later explicit approval gate.

## Restore Drill Requirement

Every first real backup must be paired with a restore drill into an isolated restore-drill path. The restore drill must refuse overwrite and must never restore over `/home/source/SpiritOS`.
