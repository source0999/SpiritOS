# Gate 2-J.8.5 Binary Recovery Attempt

status: `NO_APPROVED_BINARY_RECOVERED_OR_REBUILT`

## Expected artifact

| Field | Value |
|---|---|
| Source commit | `2444e7b6bc80d421ae3ee404081bdb41150a1830` |
| Required binary SHA-256 | `d7598ca48bb4fc8ff9c37d122fde5dd47314cd36fc2516ce6156795b71a545cc` |
| Required version | `jcode v0.58.51-dev (2444e7b6)` |
| Locked build | `CARGO_BUILD_JOBS=1 cargo build --locked --no-default-features --features linux-compat-vendored-openssl --bin jcode` |

## Recovery search

The authorized read-only sweep checked every executable regular file named
`jcode` under `/home/source`, `/tmp`, `/var/tmp`, and
`/var/lib/docker/volumes`. Every candidate would have been compared by full
SHA-256 before copying. Result: `0` executable candidates and `0` exact
matches. No candidate was copied or executed.

## Isolated rebuild

| Field | Value |
|---|---|
| Source mount | `/home/source/.codex-audits/jcode-20260727T0145Z` read-only |
| Source / lockfile | pinned commit above / `9b48f643ae298e655db7bbe68a548feb8414a634de5cf55d2b1994426e3bac19` |
| Builder image | `rust@sha256:77fac8b98f9f46062bb680b6d25d5bcaabfc400143952ebc572e924bcbedc3fa` |
| Rust / Cargo | `1.97.1` / `1.97.1` |
| Target | `x86_64-unknown-linux-gnu` |
| Linker / flags | image defaults; no custom linker or `RUSTFLAGS` recorded |
| Resources observed | 8 CPUs, 16.7 GB Docker memory |
| Mutable output only | `/home/source/.codex-audits/jcode-binary-rebuild/` |
| Result | `rustc` exited with signal 11 (`SIGSEGV`) while compiling; no `target/debug/jcode` exists |

No binary hash comparison, `file`, or `ldd` could run because no binary was
produced. No expected hash, source, packet, fixture, or product behavior was
changed. The source audit checkout remains clean.

## Disposition

Gate 2-J.9 remains blocked before task execution. A later authorized attempt
must either recover an exact original binary or diagnose the compiler crash
under a documented build environment. A new binary hash may be proposed only
after reproducible fresh builds and a separate explicit packet reseal
authorization; it has not been proposed here.
