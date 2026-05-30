# Increment 1.2.2 Real Git Checkout

Date: 2026-05-28

## Work performed

The existing non-git Mac worker tree was preserved as a timestamped backup:

```text
/Users/spiritmac/spiritos-worker/SpiritOS.pre-git-backup-20260528-150109
```

A fresh clone was created at the required final path:

```text
/Users/spiritmac/spiritos-worker/SpiritOS
```

The first clone attempt used the Linux SSH remote shape and failed because GitHub host key verification is not configured on the Mac:

```text
BACKUP_PATH:/Users/spiritmac/spiritos-worker/SpiritOS.pre-git-backup-20260528-150109
Cloning into '/Users/spiritmac/spiritos-worker/SpiritOS'...
Host key verification failed.
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
```

The repository was reachable over HTTPS without secrets:

```text
ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26	HEAD
```

The successful clone used:

```bash
git clone https://github.com/source0999/SpiritOS.git /Users/spiritmac/spiritos-worker/SpiritOS
cd /Users/spiritmac/spiritos-worker/SpiritOS
git checkout main
```

Clone result:

```text
Already on 'main'
Your branch is up to date with 'origin/main'.
```

The fresh checkout did not include `scripts/mac-worker/spirit_mac_worker.py` because `scripts/mac-worker/` is currently untracked in the Linux working tree and not present in `origin/main`. To keep the Mac support node operational without touching secrets, only `/home/source/SpiritOS/scripts/mac-worker` was copied into the Mac checkout as a documented untracked advisory worker overlay.

No `.env.local` or secret-shaped file was read or copied into the new checkout.

## Required validation commands run after the change

```bash
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && git status --branch --short --untracked-files=normal'
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && git rev-parse HEAD'
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && test -f scripts/mac-worker/spirit_mac_worker.py && echo WORKER_SCRIPT_PRESENT'
```

## Evidence

### Mac checkout status

```text
## main...origin/main
?? scripts/mac-worker/
```

### Mac checkout HEAD

```text
ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26
```

### Worker script presence

```text
WORKER_SCRIPT_PRESENT
```

### Mac checkout remote

```text
origin	https://github.com/source0999/SpiritOS.git (fetch)
origin	https://github.com/source0999/SpiritOS.git (push)
```

## Result

Increment 1.2.2 is complete.

Required validation checks were run directly.

Evidence was written to this file.

GO to the next authorized step: Phase 1.2 closeout.
