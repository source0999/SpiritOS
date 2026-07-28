# Gate 2-J.8.6 Pinned JCode Binary Provisioning

status: `JCODE_BINARY_REBUILD_HASH_MISMATCH_REQUIRES_RESEAL`

## Authority boundary

This gate searched for and rebuilt the pinned binary only. It did not invoke
JCode against a task, send a model request, start the diagnostic comparison,
touch the frozen benchmark or daily runtime, install global host tooling, or
enable production wiring.

## Required artifact and recovery

| Field | Value |
|---|---|
| Expected SHA-256 | `d7598ca48bb4fc8ff9c37d122fde5dd47314cd36fc2516ce6156795b71a545cc` |
| Pinned source | `2444e7b6bc80d421ae3ee404081bdb41150a1830` |
| Cargo.lock SHA-256 | `9b48f643ae298e655db7bbe68a548feb8414a634de5cf55d2b1994426e3bac19` |
| Builder image | `rust@sha256:77fac8b98f9f46062bb680b6d25d5bcaabfc400143952ebc572e924bcbedc3fa` |
| Rust / Cargo / target | `1.97.1` / `1.97.1` / `x86_64-unknown-linux-gnu` |
| Build command | `CARGO_BUILD_JOBS=1 cargo build --locked --no-default-features --features linux-compat-vendored-openssl --bin jcode` |

The authorized archive/cache/Docker-volume search had already found zero
executable candidates and zero exact hash matches. No candidate was copied or
executed.

## Fresh build results

| Build | Isolation | Result |
|---|---|---|
| 1 | Fresh `/cargo-home` and `/build-target`, source mounted read-only | exit `0`; SHA-256 `c490cf35737564ad0a45e2b3e8f15d6cf9289feaee32e53597c29fede2316cfc` |
| 2 | Separate fresh `/cargo-home` and `/build-target`, same pinned image/source/command | exit `101`; `rust-lld` `SIGSEGV` linking `tokio-macros`; no binary |
| 3 | Separate fresh `/cargo-home` and `/build-target`, same pinned image/source/command | exit `101`; `rustc` `SIGSEGV` compiling `ring`; no binary |

Build 1 reports `jcode v0.58.51-dev (2444e7b6)`, an ELF x86-64 PIE executable,
mode `755`, dynamic `libgcc_s`, `libm`, and `libc` dependencies, and build ID
`faddc3d2298401e71305a24f321696cb57564a40`. It is not provisioned because
its hash does not match the required hash. Build 2 produced no executable, so
there is no second hash, `file`, or `ldd` result.

The later authorized retry is Build 3. It confirms that the container compiler
is unstable under otherwise identical fresh conditions: there is one successful
alternate artifact and two independent `SIGSEGV` failures. That is not two
successful identical builds and cannot establish a reproducible replacement.

## Environmental comparison

The Rust/Cargo versions and target triple are identical. The recorded
successful environment was Ubuntu 24.04.4 with GCC 13.3.0 and GNU ld 2.42; the
pinned Rust builder is Debian 12 with GCC 12.2.0 and GNU ld 2.40. These linker
and libc-adjacent differences plausibly explain a non-identical binary, but
they do not excuse accepting a different hash. The second build's linker crash
also means a reproducible alternate binary has not been established.

## Disposition

The sealed Gate 2-J.9 packet is unchanged. No binary was copied into a runner,
no new packet hash is proposed, and Gate 2-J.9 remains blocked. A future packet
amendment may be prepared only after two independent clean builds produce the
same alternate binary, followed by separate explicit authorization to reseal.

## Superseding Dell remediation record

This historical mismatch record remains intact. The later Dell remediation
authorization established a new canonical binary through two matching clean
builds and authorized the packet reseal. See
GATE_2J_8_7_DELL_BUILD_HEALTH_AND_REPRODUCIBILITY.md. The historical d759
receipt remains historical evidence.
