# Gate 2-J.5 Critical Blocker: Reproducible Binary Identity

status: `BLOCKED_FRESH_LOCKED_BUILD_NOT_REPRODUCIBLE`

The pinned source checkout remains clean at
`2444e7b6bc80d421ae3ee404081bdb41150a1830`. A fresh isolated build used the
pinned Rust toolchain and the documented command:

```text
cargo build --locked --no-default-features --features linux-compat-vendored-openssl --bin jcode
```

It failed while compiling the locked `rustls 0.23.37` source with:

```text
cannot find tuple struct or tuple variant `HandshakeMessagePaiload`
similarly named tuple struct `HandshakeMessagePayload` defined here
```

An earlier disposable build had produced a binary hash, but this fresh build
cannot reproduce it. Treating the earlier artifact as current qualification
evidence would violate the exact-binary identity requirement. No source patch,
crate substitution, lockfile change, provider call, model call, or daily
runtime action was attempted.

The new fail-closed identity module and focused tests are retained, but Gate
2-J.5 cannot be green until an operator supplies an immutable vendored crate
set or another independently verifiable build environment that reproduces the
pinned binary.

Gates 2-J.6 through 2-J.10 must not begin.
