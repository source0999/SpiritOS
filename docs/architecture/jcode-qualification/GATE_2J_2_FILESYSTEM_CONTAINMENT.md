# Gate 2-J.2 Filesystem Containment

status: `GREEN_NEGATIVE_CONTAINMENT_ONLY`

## Scope

This gate qualifies only an OS-enforced negative filesystem boundary for a
future JCode runner. It does not create a JCode dispatcher, authorize live
execution, or claim that a writable execution workspace exists.

`source_proxy/jcode/containment.py` starts Bubblewrap with an empty
`/workspace` root, exposes only an explicitly validated regular-file input
set, mounts those inputs read-only, creates a fresh isolated `/jcode-home`,
and unshares the network. Workspace escapes, percent-encoded paths, secret
shaped paths, symlinks, duplicate entries, and protected-path overlap fail
closed before Bubblewrap is invoked.

The host's Bubblewrap/AppArmor behavior also rejects writes to the sandbox
workspace. That is recorded as containment, not silently treated as a writable
JCode execution capability.

## Executed evidence

| Check | Result |
|---|---|
| Host Bubblewrap | `/usr/bin/bwrap`, version `0.9.0` |
| Focused command | `/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python -m pytest -q source_proxy/tests/test_jcode_containment.py source_proxy/tests/test_jcode_qualification_adapter.py source_proxy/tests/test_bubblewrap_sandbox.py` |
| Focused result | `50 passed in 0.24s` |
| Real negative probe | Declared input was readable; `/home/source` was absent; protected-file creation returned nonzero with `Permission denied`; host files were unchanged. |

## Gate disposition

Gate 2-J.2 is complete for filesystem containment. The next gate is 2-J.3
network and credential containment, including the separately required proof of
the only permitted loopback endpoint. The default executor remains unchanged
and `JCODE_EXECUTOR_ENABLED` remains disabled.
