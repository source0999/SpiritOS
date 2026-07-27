# Gate 2-J.3 Critical Blocker: Network and Credential Containment

status: `BLOCKED_CRITICAL_HOST_NETWORK_ENFORCEMENT_MISSING`

## Required claim

This gate requires an OS-enforced default-deny egress policy with exactly one
permitted, inference-only loopback endpoint. Application URL validation is not
enough: the JCode process must be unable to reach every other host, port, or
credential-bearing service.

## Executed evidence

| Check | Result |
|---|---|
| Bubblewrap default-deny mode | Available; it uses `--unshare-net` and prevents all network access. It cannot reach the host loopback inference service from that new network namespace. |
| Privileged host firewall inspection | `nft list ruleset` failed: `Operation not permitted (you must be root)`; `iptables -S` failed: `Permission denied (you must be root)`. |
| Unprivileged isolated network namespace | `unshare --user --map-root-user --net ...` failed before execution: `unshare: write failed /proc/self/uid_map: Operation not permitted`. |
| Candidate alternatives | `nft`, `iptables`, `ip`, `slirp4netns`, and `systemd-run` are installed, but no non-root path can install and verify a single-endpoint egress rule. |
| Pinned binary reproducibility | The pinned audit checkout remained clean; a disposable, worktree-local locked build with `--no-default-features --features linux-compat-vendored-openssl --bin jcode` produced SHA-256 `d80950beb50a3abefec48448a9feec51c935fb03dd5ab0b20d7f5cf9ff320713` and `jcode v0.58.51-dev (2444e7b6)`. No model, provider, or task was invoked. |

## Why this blocks the campaign

The existing adapter accepts only loopback URLs, but it deliberately reports
`inference_only_egress_guard_not_implemented`. Its current Bubblewrap policy
proves total egress denial; relaxing that policy would expose the host network
without an exact OS firewall rule. Treating a URL allowlist or a trusted-command
mode as equivalent would be an authority and containment regression.

## Required external resolution

An operator or host administrator must provide a verifiable, per-process or
per-network-namespace egress policy that:

1. permits only the designated local inference route and port;
2. denies all other IPv4, IPv6, DNS, Unix-socket, proxy, and credential routes;
3. can be applied and inspected by the qualification worker without changing
   the daily runtime; and
4. supplies a testable endpoint identity independent of the coding API.

Until that exists, Gate 2-J.3 remains blocked. Gates 2-J.4 through 2-J.10 must
not begin, the default executor remains unchanged, and no JCode execution is
authorized.
