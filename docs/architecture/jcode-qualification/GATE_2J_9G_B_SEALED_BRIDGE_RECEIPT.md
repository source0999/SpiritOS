# Gate 2-J.9G-B Sealed-Bridge Receipt

## Verdict

BLOCKED_BEFORE_COMPLIANT_FAKE_BACKEND_ROUTE

## Scope

- Worktree: /home/source/SpiritOS-source-proxy-jcode-qualification-20260726
- Branch: codex/source-proxy-jcode-qualification-20260726
- Authorization: TERRA_HIGH_AUTHORIZED__GATE_2J_9G_B
- Authorization digest: 8213ccdd0058fe25c7a027c4c2e7efe48ae770b0fd049d8e1d8309add6e1fbdb
- Implementation start: bffead34de12302a1ac8389153ff376178af8e83
- Pinned source: 2444e7b6bc80d421ae3ee404081bdb41150a1830
- Pinned binary SHA-256: 2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6

## Routing Audit

Classification: SUPPORTED_CUSTOM_PROVIDER_NOT_WIRED.

The pinned source exposes openai-compatible, accepts
JCODE_OPENAI_COMPAT_API_BASE, permits a local loopback base URL, and
constructs the OpenAI-compatible endpoint by appending
/chat/completions. Relevant evidence is in
crates/jcode-base/src/provider_catalog.rs,
crates/jcode-provider-openrouter-runtime/src/openrouter_sse_stream.rs, and
tests/provider_matrix.rs in the pinned source checkout. The observed
http://localhost:11434/v1 route is a saved/default profile value, not a
hard-coded mandatory endpoint.

## Evaluated Design

A static in-root loopback shim was evaluated with an inherited Unix socketpair
to a Proxy-owned host bridge. A focused containment audit proved that Bubblewrap
preserves an explicitly passed socket FD into the preassembled root. The
in-root endpoint would have been 127.0.0.1:43123/v1; the root remained
network-unshared and no host port 11434 was exposed.

## Execution Evidence

Three exact-binary jcode run launches were made under the new root during the
authorized fake-backend proof. Each used the OpenAI-compatible environment,
the task-scoped capability, and the inherited channel. The exact binary started,
but did not connect to the in-sandbox listener before the 45-second supervised
timeout. The host bridge observed zero HTTP requests.

- JCode launches in this gate: 3
- Fake model requests: 0
- Real model requests: 0
- Direct Ollama requests: 0
- Repository writes by JCode: 0
- Frozen benchmark changes: 0
- Daily-runtime changes: 0

## Stop Condition

The required proof that JCode reaches the configured compatibility endpoint is
absent. Advancing would replace the requested integration with an easier
non-JCode bridge test, so Gate 2-J.9G, 2-J.9H, and 2-J.9I are not started.

The unaccepted prototype relay and its test were removed before recording this
receipt. A future authorization must diagnose the pinned binary's pre-request
startup stall with independently supervised process, syscall, and configuration
evidence before it can resume the route proof.
