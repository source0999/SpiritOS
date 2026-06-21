# F10 Codex Review Report

F10 has not started. There is no implementation evidence to review yet.

## Review stance
- F10 is the terminal requalification gate, not final acceptance.
- F10 may produce `READY_FOR_SECONDARY_REVIEW` only after all F01-F09 stages are
  GO, committed, and requalified by the frozen battery.
- Final acceptance remains separate: independent Codex review, Britton approval,
  and merge authority.

## Pre-run findings
- No source implementation has begun at planning-packet time.
- Prior focused source-proxy audit XML checksum caveat is recorded as
  `known_preexisting_prior_audit_xml_integrity_caveat`.
- Full-repo audit checksums pass after `a01abb13`.
- Set A/B/C are forbidden during cleanup.
- Plan 4 is forbidden.

## F10 review checklist
- Contract hashes match all frozen F-stage acceptance and holdout artifacts.
- All battery items have exact commands, exit codes, raw evidence, and
  conclusions.
- No fallback is counted as primary success.
- No route/status-only proof is counted as behavior proof.
- No benchmark-specific runtime branch exists.
- No unapproved API/cloud provider call occurred.
- No protected path was modified.
- Dirty tree is clean after the final F10 commit.
