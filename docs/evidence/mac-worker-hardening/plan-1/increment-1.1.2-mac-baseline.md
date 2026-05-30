# Increment 1.1.2 Mac Baseline

Date: 2026-05-28

## Required commands run

```bash
ssh -o BatchMode=yes spirit-mac-mini 'hostname; whoami; sw_vers; python3 --version'
ssh -o BatchMode=yes spirit-mac-mini 'ls -la /Users/spiritmac/spiritos-worker || true'
ssh -o BatchMode=yes spirit-mac-mini 'ls -la /Users/spiritmac/spiritos-worker/SpiritOS || true'
ssh -o BatchMode=yes spirit-mac-mini 'test -d /Users/spiritmac/spiritos-worker/SpiritOS/.git && echo GIT_PRESENT || echo GIT_MISSING'
ssh -o BatchMode=yes spirit-mac-mini 'test -f /Users/spiritmac/spiritos-worker/SpiritOS/scripts/mac-worker/spirit_mac_worker.py && echo WORKER_SCRIPT_PRESENT || echo WORKER_SCRIPT_MISSING'
```

## Evidence

### Host, user, macOS, Python

```text
spirit-mac-mini.local
spiritmac
ProductName:		macOS
ProductVersion:		15.7.7
BuildVersion:		24G720
Python 3.9.6
```

### Worker parent path

```text
total 0
drwxr-xr-x   3 spiritmac  staff   96 May 28 14:20 .
drwxr-xr-x+ 21 spiritmac  staff  672 May 28 14:18 ..
drwxr-xr-x  10 spiritmac  staff  320 May 28 14:20 SpiritOS
```

### Worker path contents

```text
total 24
drwxr-xr-x  10 spiritmac  staff   320 May 28 14:20 .
drwxr-xr-x   3 spiritmac  staff    96 May 28 14:20 ..
-rwx------   1 spiritmac  staff  1212 May 25 07:50 next.config.ts
-rwx------   1 spiritmac  staff  3516 May 27 21:24 package.json
drwxrwxr-x  18 spiritmac  staff   576 May 25 08:08 scout
drwxr-xr-x  17 spiritmac  staff   544 May 28 14:11 scripts
drwxrwxr-x  27 spiritmac  staff   864 May 25 08:08 source_proxy
drwxr-xr-x  10 spiritmac  staff   320 May  8 20:15 src
drwx------   4 spiritmac  staff   128 May 27 21:22 tests
-rwxrwxr-x   1 spiritmac  staff   846 May 16 19:58 tsconfig.json
```

### Git and worker script presence

```text
GIT_MISSING
WORKER_SCRIPT_PRESENT
```

## Result

Increment 1.1.2 is complete.

Required checks were run directly.

Evidence was written to this file.

GO to the next authorized step: Phase 1.1 closeout.
