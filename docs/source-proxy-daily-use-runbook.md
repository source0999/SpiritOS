# Source Proxy Daily Use Runbook

Status date: 2026-05-18
Status: active daily-use operator runbook

## Purpose

This runbook explains which surface to use for normal Source Proxy work from desktop, Codex mobile, SSH, and RustDesk.

Source Proxy remains the system of record. Codex mobile and SSH are review/control surfaces only; they do not bypass approval, apply, commit, or push gates.

## Quick Start

Use this default flow for most increments:

1. Ask Codex to state the active increment, scoped files, and manual check.
2. Let Codex run read-only checks when you are on mobile.
3. Review the expected output and blockers.
4. Approve the next increment only when the check is understandable.
5. Keep apply, commit, and push behind separate Source Proxy approvals.

## Local Desktop Flow

Use desktop when you need the full UI, a code editor, or a wide diff.

Best for:

- reviewing multi-file diffs
- inspecting `/coding`, dashboard, Scout, or Cartographer UI state
- comparing long test logs
- checking visual layout
- resolving merge or branch questions

Normal desktop loop:

```bash
cd /home/source/SpiritOS
git status --short
git diff --check
```

Then open:

```text
https://10.0.0.186:3000/coding
```

Source Proxy approval is still final. A desktop review does not imply apply, commit, or push approval.

## Codex Mobile Review Flow

Use Codex mobile when you want Codex to run the check and summarize the result while you are away from the desktop.

Best for:

- "run manual check for me"
- approving read-only diagnostic commands
- reviewing compact test summaries
- deciding whether to continue to the next increment
- catching blockers without juggling terminal apps

Mobile prompt pattern:

```text
Can you run the manual check for me and, if all good, go next? I am mobile.
```

Codex should respond with:

- what command it ran
- actual pass/fail output
- expected output
- any dirty files or evidence files created
- the next increment
- one copy-paste manual-check block for later verification

Codex mobile may approve scoped docs edits when the current increment explicitly names those docs. It must not approve apply, commit, push, provider promotion, or broad cleanup.

## SSH Fallback Flow

Use SSH or Termius when you need raw host access and copyable terminal output.

Best for:

- restarting the local HTTPS LAN servers
- checking ports
- tailing logs
- running long commands directly
- collecting output that Codex mobile should review

Common checks:

```bash
cd /home/source/SpiritOS
tmux ls 2>/dev/null || true
ss -ltnp | grep -E ':3000|:8787|:22|:11434' || true
git diff --check
```

SSH does not change authority. Do not use SSH to apply, commit, push, delete, clean, or edit secrets unless the active Source Proxy gate explicitly authorizes that action.

## RustDesk Use

Use RustDesk only when GUI access is actually required.

Use RustDesk for:

- browser-only visual inspection
- UI behavior that cannot be verified from logs
- copying from an app that is not available over SSH

Avoid RustDesk for routine manual checks. SSH or Codex mobile is usually simpler and less disruptive.

## What To Paste Back

When you run checks yourself, paste the smallest useful block:

```text
COMMAND:
RESULT:
EXPECTED:
DIFF CHECK:
STATUS:
BLOCKERS:
```

For long logs, paste only:

- final test summary
- failed test names
- route response JSON
- `git diff --check` result
- `git status --short`

## Stop And Ask For Help

Stop the increment and ask for review if any of these happen:

- a check fails
- `git diff --check` reports whitespace errors
- a command wants approval to apply, commit, push, delete, or clean
- a protected path appears, such as `.env`, certificates, keys, tokens, or credentials
- a route returns unexpected write authority
- HEAD changes unexpectedly
- the dirty-file list changes in a way the increment did not predict
- the output is too large or confusing to review on mobile

## Never Approve Remotely

Do not approve these from mobile or SSH without a separate explicit Source Proxy gate:

- apply
- commit
- push
- merge
- broad cleanup
- deleting files
- editing secrets or certificates
- provider-layer implementation
- AionUi bridge work
- Spirit Cowork Console work
- autonomous multi-agent writes
- scheduled provider tasks
- promoting Codex to default coding worker

## Daily Closeout

Before stopping for the day, collect:

```bash
cd /home/source/SpiritOS
git status --short
git diff --check
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Expected result:

- `git diff --check` has no output
- closeout reports `Closeout status: PASS` or names exact blockers
- no apply, commit, or push action runs by default
- expected evidence snapshots are separated from unsafe dirty files

## Related Docs

- `docs/source-proxy-remote-manual-checks.md`
- `docs/source-proxy-production-hardening-plan.md`
- `docs/source-proxy-regression-matrix.md`
