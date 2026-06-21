# F10 Evidence Summary

No F10 evidence has been generated. F10 is NOT_STARTED.

When F10 runs, every battery item must record:

- exact command
- start time
- exit code
- decisive output excerpt
- raw evidence path
- SHA-256 of retained raw evidence
- conclusion derived from the command

Required battery coverage is frozen in `acceptance-contract.json` and includes
all taxonomy tests, all 19 failure classes, anti-cheat negative corpus, parity,
brain-switch dry-run tests, proof no unapproved provider call occurred, generic
packet decomposition holdouts, benchmark-tailoring scan, receipt compatibility,
trace/consumer compatibility, apply/recovery tests, focused and bounded Python
tests, lint, typecheck, build, canonical `/coding` tests, bounded smoke if
available, Plan 2 and Plan 3 operators, Headroom/fallback checks, protected-path
checks, dirty-tree checks, and `git diff --check`.

Skipped, timed-out, unavailable, fallback-relied, or partial commands may not be
reported as PASS.
