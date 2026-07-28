# Gate 2-J.8.7 Dell Build Health and Reproducible Binary Attestation

status: DELL_REPRODUCIBLE_BINARY_ATTESTED_PACKET_RESEALED

## Scope

This receipt records host diagnostics, compiler/linker smoke tests, two
isolated builds, and non-model binary checks only. It did not invoke JCode
against a task, send a model request, modify the frozen benchmark, touch the
daily runtime, enable production wiring, or start Gate 2-J.9.

## Health receipt

| Field | Observed value |
|---|---|
| Host / kernel | source-server / Linux 6.8.0-134-generic x86_64 |
| CPU | Intel Core i7-6700, 8 logical CPUs |
| RAM / available | 15 GiB / approximately 11 GiB |
| Swap | /swap.img, 4 GiB total, active; no swap change made |
| Build filesystem | ext4 /dev/sdb2, 198 GiB free, 28.4M free inodes |
| Docker | 29.4.0, overlayfs, systemd cgroup v2, 8 CPUs, 15.5 GiB |
| Build cgroup | fresh containers, 1 CPU, 6 GiB memory and memory-swap |
| Limits | open files 1024; process and virtual-memory limits unlimited |
| Overcommit | mode 0, ratio 50, max_map_count 1048576 |
| Thermal | CPU package 42.0 C; below the reported 84.0 C high threshold |
| Rust / Cargo / target | 1.97.1 / 1.97.1 / x86_64-unknown-linux-gnu |
| Compiler / linker | GCC 12.2.0; GNU ld.bfd 2.40 through /usr/bin/gcc -fuse-ld=bfd |
| Source / lockfile | 2444e7b6bc80d421ae3ee404081bdb41150a1830 / 9b48f643ae298e655db7bbe68a548feb8414a634de5cf55d2b1994426e3bac19 |
| Builder image | rust@sha256:77fac8b98f9f46062bb680b6d25d5bcaabfc400143952ebc572e924bcbedc3fa |

The active cgroup reported zero OOM and OOM-kill events. Kernel logs contain
the historical rust-lld and rustc faults plus older ext4 metadata-checksum
errors, but no new OOM, MCE, EDAC, disk-I/O, or filesystem event during the
corrected smoke or proof builds. The ext4 history is a host-maintenance risk,
not evidence that this reproducible artifact is corrupt.

## Stabilized profile

The prior rust-lld crash while linking tokio-macros and rustc diagnostic during
ring compilation supported a focused correction: one job, incremental
compilation disabled, RUST_MIN_STACK=16777216, GNU ld.bfd, a fresh target per
run, fixed container paths, and a sealed read-only Cargo cache. No Dell
package, service, swap, kernel, or persistent system configuration changed.

The cache was seeded once with cargo fetch --locked, then made read-only:
60,141 files and aggregate SHA-256
5decd3a87a17705ddde3c5cd4133e5af386d07a57b4ea09f221f1bc0d3ab96a1.
Proof builds used --offline --locked, CARGO_BUILD_JOBS=1,
CARGO_INCREMENTAL=0, SOURCE_DATE_EPOCH=1785116316, TZ=UTC, LC_ALL=C,
LANG=C, source remapping, and disabled linker build IDs.

## Smoke tests

Two fresh no-network containers compiled and ran a trivial Rust binary through
GNU ld.bfd. Two fresh containers then ran cargo check --offline --locked
--no-default-features --features linux-compat-vendored-openssl --bin jcode -j 1.
Each finished in 7m56s and compiled ring 0.17.14, tokio-macros 2.6.0, and
procedural macro crates including serde_derive and syn without a crash.

## Two-build proof

Both builds used a read-only source mount at /workspace/jcode, a separate fresh
target at fixed internal /workspace/target, the sealed cache, a fresh
container, and no network.

| Field | Build A | Build B |
|---|---|---|
| UTC interval | 2026-07-28T02:33:08Z to 02:44:25Z | 2026-07-28T02:44:40Z to 02:56:27Z |
| Exit code | 0 | 0 |
| SHA-256 | 2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6 | 2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6 |
| Size / mode | 233979416 bytes / 755 | 233979416 bytes / 755 |
| Version | jcode v0.58.51-dev (2444e7b6) | jcode v0.58.51-dev (2444e7b6) |

Both outputs are x86-64 PIE ELF executables dynamically linked only to
libgcc_s, libm, and libc, with no linker build ID. The attested artifact was
copied without transformation to
/home/source/.codex-audits/jcode-dell-remediation-20260727/approved-binary/jcode
and rechecked by SHA-256, cmp, file, ldd, permissions, and --version. It is not
committed to Git.

Historical d7598ca48bb4fc8ff9c37d122fde5dd47314cd36fc2516ce6156795b71a545cc
evidence remains historical. The matching Dell result is the new canonical
qualification binary bound into the resealed packet.
