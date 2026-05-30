# Increment 2.2.1 Overlay Decision

Date: 2026-05-28

## Scope

Allowed work for this increment:

- Inspect Linux repo `scripts/mac-worker/`.
- Inspect Mac repo `scripts/mac-worker/`.
- Compare files.
- Determine whether these files should be tracked repo content or an explicitly documented overlay.

No files were deleted. No commits were made. No worker implementation files were changed.

## Required command results

### Linux worker directory

Command:

```bash
cd /home/source/SpiritOS
ls -la scripts/mac-worker || true
```

Result:

```text
total 36
drwx------ 3 source source 4096 May 28 19:05 .
drwxr-xr-x 5 source source 4096 May 28 18:11 ..
drwx------ 2 source source 4096 May 28 19:18 __pycache__
-rwx------ 1 source source 8443 May 28 19:05 spirit-mac-worker.mjs
-rwx------ 1 source source 9437 May 28 19:05 spirit_mac_worker.py
```

### Linux worker file headers

Command:

```bash
cd /home/source/SpiritOS
find scripts/mac-worker -maxdepth 1 -type f -print -exec sed -n '1,40p' {} \;
```

Result summary:

- `scripts/mac-worker/spirit-mac-worker.mjs` starts with `#!/usr/bin/env node`, imports Node built-ins, defines supported job types, and defines a safe check command allowlist.
- `scripts/mac-worker/spirit_mac_worker.py` starts with `#!/usr/bin/env python3`, imports Python standard library modules, defines supported job types, and defines a safe check command allowlist.
- The first 40 lines shown by the command contained no secrets, keys, tokens, `.env.local` values, private host credentials, or production data.

### Mac worker directory

Command:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && ls -la scripts/mac-worker || true'
```

Result:

```text
total 48
drwx------   4 spiritmac  staff   128 May 28 15:01 .
drwxr-xr-x  16 spiritmac  staff   512 May 28 15:01 ..
-rwx------   1 spiritmac  staff  8443 May 28 15:05 spirit-mac-worker.mjs
-rwx------   1 spiritmac  staff  9437 May 28 15:05 spirit_mac_worker.py
```

### Mac worker files

Command:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && find scripts/mac-worker -maxdepth 1 -type f -print 2>/dev/null || true'
```

Result:

```text
scripts/mac-worker/spirit-mac-worker.mjs
scripts/mac-worker/spirit_mac_worker.py
```

## Comparison

Tracked state command:

```bash
cd /home/source/SpiritOS
git ls-files scripts/mac-worker
```

Result:

```text
```

Interpretation: `scripts/mac-worker/` is currently untracked in the Linux repo.

Linux checksum command:

```bash
sha256sum scripts/mac-worker/spirit-mac-worker.mjs scripts/mac-worker/spirit_mac_worker.py
```

Linux result:

```text
979862fc69483c92da37e0da7589bb1f50c5e61303c4f2908a38fb5596a4c187  scripts/mac-worker/spirit-mac-worker.mjs
8870323b132425285fd4ec0ee5621c92d9b6b37f2292e0a5107c072ae41f9087  scripts/mac-worker/spirit_mac_worker.py
```

Mac checksum command:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && shasum -a 256 scripts/mac-worker/spirit-mac-worker.mjs scripts/mac-worker/spirit_mac_worker.py'
```

Mac result:

```text
979862fc69483c92da37e0da7589bb1f50c5e61303c4f2908a38fb5596a4c187  scripts/mac-worker/spirit-mac-worker.mjs
8870323b132425285fd4ec0ee5621c92d9b6b37f2292e0a5107c072ae41f9087  scripts/mac-worker/spirit_mac_worker.py
```

Linux and Mac worker files match by SHA-256.

## Decision

Decision: `scripts/mac-worker/` should become normal tracked repo content.

Reasoning:

- The Mac API and worker path depend on these files for the currently proven Plan 1 jobs.
- Linux and Mac have matching non-secret worker files.
- Keeping the files untracked makes production-preflight support brittle because a clean checkout would not contain the worker entrypoints.
- An undocumented or purely manual overlay would weaken job status truth and repeatability.
- Tracking the two worker entry files preserves Source Proxy as the approval/write authority while making the advisory/check support node reproducible.

Exclusions:

- Do not track `scripts/mac-worker/__pycache__/`.
- Do not track secrets, keys, `.env.local`, local caches, generated evidence outside approved docs, or machine-specific private files.

## Safety confirmation

- No Mac write authority was changed.
- No hidden worker, daemon, launch agent, or persistent process was started.
- No Scout production data was mutated.
- No Cartographer, provider routing, secrets, or protected files were changed.
- No worker files were changed in this increment.

## GO / NO-GO

GO for Increment 2.2.1 complete.

Next authorized increment: Increment 2.2.2, formalize the worker files safely.
