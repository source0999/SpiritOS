# JCode Source and Security Audit

status: `PINNED_DESIGN_QUALIFICATION_LIVE_EXECUTION_BLOCKED`

## Source pin

| Field | Value |
|---|---|
| Upstream | `https://github.com/1jehuang/jcode.git` |
| Commit | `2444e7b6bc80d421ae3ee404081bdb41150a1830` |
| Nearest release ancestor | `v0.58.0-51-g2444e7b6` |
| License | MIT |
| Audit checkout | `/home/source/.codex-audits/jcode-20260727T0145Z` |

The pin is authoritative; later tags are not inferred to be ancestors or
equivalent. The raw source receipt and audit findings remain archived.

## Security conclusion

JCode is not safe to execute in this repository without external controls.
Its normal tool, process, network, state, and provider surfaces remain outside
the Proxy authority boundary. The current seam therefore defaults every live
capability to false, allows only a Proxy-issued loopback model endpoint in a
future runtime, and denies shell, browser, memory, MCP, swarm, and web fetch.

## Live-execution blockers

1. OS-enforced filesystem containment is absent.
2. Default-deny network and credential containment is absent.
3. Process-group supervision, limits, cancellation, and recovery are absent.
4. Exact binary, provider, requested model, and actual model reconciliation is absent.
5. Complete NDJSON/raw-stream/result evidence mapping is absent.
6. Fresh-state and second-run reproduction are absent.
7. The diagnostic fixture is sealed but uncommitted and unexecuted.
8. No paired comparison evidence exists.
9. Challenger lanes require later model authority.
10. No adoption threshold has been met.

Every blocker must be independently cleared; none may be collapsed into a
design-only conclusion.
