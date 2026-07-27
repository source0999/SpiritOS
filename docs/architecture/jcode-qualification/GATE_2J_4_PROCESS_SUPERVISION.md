# Gate 2-J.4 Process Supervision

status: `GREEN`

`source_proxy/jcode/supervision.py` creates one new process session for each
future qualification command and returns a terminal receipt only after the
entire process group has been reaped. Timeout and cancellation send `SIGTERM`,
wait a bounded grace period, then send `SIGKILL` when any group member remains.

The focused suite covers normal completion, cancellation, a timeout-resistant
process, and a descendant that ignores `SIGTERM`. The descendant case proves
that a parent exit cannot be mistaken for cleanup of the group.

The pinned-source audit recorded the earlier `SIGSEGV` precisely: it was a
`rustc` crash while compiling JCode's large default-feature embedding/AWS graph,
not a JCode model or task execution crash. The locked no-default-feature build
was the controlled mitigation. This gate does not rerun that resource-heavy
default build and does not claim it is green.

| Check | Result |
|---|---|
| Focused command | `python -m pytest -q source_proxy/tests/test_jcode_supervision.py` |
| Result | `4 passed in 0.54s` |
| SIGSEGV source | archived `JCODE_SOURCE_AUDIT.md`, reproduced default-feature `rustc` crash |
| Live JCode/model/provider/task | not invoked |

Gate 2-J.4 is complete. The next ordered gate is exact binary, provider, and
model truth. The default executor and JCode feature flag remain unchanged.
