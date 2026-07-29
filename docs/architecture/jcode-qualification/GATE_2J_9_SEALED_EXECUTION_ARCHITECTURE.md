# Gate 2-J.9 Sealed Execution Architecture

status: `AMENDMENT_ARCHITECTURE_SEALED_PENDING_OPERATOR_DECISIONS`

schema: `source-proxy.gate-2j-9-sealed-execution-architecture/v1`
amendment to: `CAMPAIGN_2J_AMENDMENT.md`
companion specs: containment, inference bridge, NDJSON event contract, process supervision,
  writable overlay and diff contract, result mapping.

This document defines the canonical sealed JCode dispatcher architecture. It is sufficiently
exact that Terra High can implement it without making new architectural decisions. Mechanism
selections are based on independently audited host capability (see
`GATE_2J_9_CONTAINMENT_SPECIFICATION.md` "Host capability evidence") and on the existing
proven Bubblewrap containment already in the repository.

## 1. Authority model preserved

`CodingOrchestrator` (the Source Proxy) remains the sole authority over task creation,
task/correlation IDs, immutable prompts, approvals, provider/model selection, budgets,
allowed/protected paths, tool policy, timeout/cancellation, raw-output capture, evidence
hashes, independent Git diff, review, verification, anti-cheat, final terminal outcome, and
commit/push/merge/deploy/release authorization.

JCode may own only: a bounded per-task cognitive loop; permitted repository discovery;
permitted model requests through the sealed provider bridge; permitted tool calls; observation
of tool results; bounded retries; and emission of complete raw events and output.

JCode must never own any of the Proxy-reserved authorities, must never hold direct production
credentials, unrestricted filesystem/network access, persistent cross-task memory, or
auto-update. These invariants are already encoded in `adapter.py` forced-env and denied-tool
lists; the dispatcher enforces them at the OS level, not by trusting JCode.

## 2. Required control path

```text
Canonical Proxy Task
        |
Sealed Execution Envelope            (proxy-built, hash-bound, see section 4)
        |
Envelope Validation and Attestation  (identity.py reconciliation + envelope validation)
        |
Disposable Worktree + Writable Overlay (read-only base at sealed commit + isolated writable layer)
        |
Contained Per-Task JCode Process     (one fresh external CLI process; fresh JCODE_HOME)
        |
Sealed Inference Bridge              (attesting proxy-controlled local bridge)
        |
Exact Authorized Local Model         (qwen2.5-coder:7b primary / :14b challenger, no substitution)
        |
Strict Event and Output Capture      (NDJSON contract; stdout/stderr ledgers)
        |
Independent Workspace/Diff Inspection (proxy-owned git diff, untracked/deleted/renamed)
        |
Proxy Reviewer / Verifier / Anti-Cheat
        |
Canonical Proxy Terminal Outcome     (one of three terminal classes; JCode claim is evidence only)
```

JCode runs as exactly one fresh external CLI process per task. Each task receives:
one fresh disposable worktree; one fresh writable overlay; one fresh `JCODE_HOME`;
no previous session; no previous memory; no shared prompt cache containing campaign content;
no hidden expectations; no frozen benchmark solutions; no direct production mutation authority.

## 3. Sealed dispatcher component map

The dispatcher is a new Proxy-owned module (proposed: `source_proxy/jcode/dispatcher.py`) that
composes the existing proven components with the new ones defined in the companion specs. It does
not extend JCode's authority.

| Stage | Component | State |
|---|---|---|
| Envelope build | `adapter.JCodeExecutionEnvelope` + new `sealed_envelope.py` builder | reuse envelope; add sealed envelope builder |
| Identity attestation | `identity.verify_jcode_binary_identity` + `reconcile_jcode_model_identity` | reuse; wire to live bridge receipt |
| Worktree + overlay | new `source_proxy/jcode/workspace.py` | NEW (Gate 2-J.9E) |
| Containment args | `containment.build_jcode_containment_args` + cgroup scope wrapper | extend proven bwrap path |
| Process supervision | `supervision.run_supervised_jcode_command` + cgroup/tree-cleanup extension | extend proven path |
| Sealed inference bridge | new `source_proxy/jcode/sealed_inference_bridge.py` | NEW (Gate 2-J.9F) |
| Event capture + NDJSON | `evidence.map_jcode_ndjson_evidence` + strict schema | extend proven mapper |
| Independent diff | new `source_proxy/jcode/diff_collector.py` | NEW (Gate 2-J.9E) |
| Terminal mapping | new `source_proxy/jcode/terminal_mapping.py` | NEW (Gate 2-J.9 result mapping) |

## 4. Sealed execution envelope (canonical)

The envelope is Proxy-built and hash-bound before any JCode process exists. It is the single
authority the dispatcher consumes. Serialization is deterministic UTF-8 JSON using the existing
`preparation._canonical_json` rule (`sort_keys=True`, `separators=(",",":")`, `ensure_ascii=True`)
with a trailing newline; every hashable artifact is SHA-256 over that canonical encoding.

The envelope MUST carry, at minimum:

- **Identity:** schema version; campaign ID `campaign-2-j`; gate ID; run ID; task ID;
  correlation ID; harness ID `SpiritOS-Source-Proxy/CodingOrchestrator`; harness version;
  adapter version `jcode-qualification-adapter/v1`; JCode source commit
  `2444e7b6bc80d421ae3ee404081bdb41150a1830`; JCode binary SHA-256
  `2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6`; proxy source commit
  (branch HEAD); base repository commit (sealed base).
- **Task binding:** immutable prompt; prompt SHA-256; acceptance-criteria hash;
  diagnostic-manifest hash; task category; hidden-material exclusion proof.
- **Context binding:** context packet ID; context schema version; context packet SHA-256;
  ordered context-file manifest; per-file SHA-256; total context bytes; truncation status;
  excluded-path list; generation process and version.
- **Model/provider binding:** provider-profile ID `spiritos-qualification`; inference bridge
  ID `sealed-loopback-inference-bridge/v1`; permitted base URL `http://127.0.0.1:4000/v1`;
  permitted endpoint; model registry ID (`qwen2.5-coder:7b` or `:14b` by lane); expected
  provider model ID; expected model digest; quantization `Q4_K_M`; generation parameters
  (max_tokens 4096, seed 7, temperature 0); context-window limit; output-token limit;
  request-count limit; fallback policy `none`; explicit prohibition on silent substitution.
- **Capability binding:** allowed paths; protected paths; allowed tools (the 9 sealed);
  denied tools (the 11 sealed); permitted command classes (none); denied command classes
  (all shell); environment allowlist (LANG, LC_ALL, PATH, TZ); network policy; writable
  paths (overlay only); read-only paths (base + inputs); commit/push/deploy prohibition.
- **Budget binding:** wall-clock timeout 300 s; inactivity timeout (to be sealed);
  model-request maximum (to be sealed); token maximum 32768; tool-call maximum (to be sealed);
  retry maximum (to be sealed); process-count maximum (cgroup pids, to be sealed);
  file-write maximum (to be sealed); output-byte maximum 2,000,000; event-count maximum (to be sealed).
- **Evidence binding:** evidence directory; transcript path; raw-event path; stdout path;
  stderr path; tool-call ledger; model-request ledger; filesystem ledger; diff receipt path;
  final result path; required hashes.

Canonical hashing rule: each ledger and envelope section is hashed independently over its
canonical-JSON bytes, and the envelope root hash is the SHA-256 of the canonical JSON of the
ordered list of section hashes. The root hash is recorded in `evidence_hashes`.

## 5. Mechanism selections (sealed design)

These are the selected canonical designs based on audited host capability. Where a value is
marked `OPERATOR_REQUIRED`, the architecture defines the slot but the exact numeric/identity
value must be sealed by operator decision before the gate that consumes it may run.

- **Containment:** Bubblewrap 0.9.0 namespace sandbox (unshare user/pid/ipc/uts/cgroup/net),
  read-only base binds, empty `/workspace` with an isolated writable overlay bind, read-only
  `/jcode-home`, no `/proc`/`/sys` beyond bwrap defaults, wrapped in a **systemd v255 transient
  scope** with **cgroup v2** resource limits. See containment spec. (NOT a container image;
  NOT Docker; NOT a new mechanism.)
- **Process supervision:** `systemd-run --scope --user` (or equivalent `--scope`) creates the
  cgroup; `supervision.py` process-group SIGTERM->SIGKILL escalation is retained and extended
  with cgroup membership check for complete descendant cleanup. See supervision spec.
- **Inference bridge:** a Proxy-controlled attesting local bridge on loopback that inspects
  every request, binds to task/correlation IDs, verifies provider+model, enforces generation
  parameters and request/token budgets, and emits raw request/response metadata. The current
  byte-forwarding Unix bridge is reused as the *transport*; an attestation layer is added.
  See inference bridge spec.
- **Event protocol:** strict NDJSON, one JSON object per line, with the per-event schema and
  terminal sentinel defined in the NDJSON contract. See event contract spec.
- **Writable overlay:** lower layer = read-only bind of the disposable worktree at the sealed
  base commit; upper layer = a fresh empty tmpdir bind-mounted writable at `/workspace`;
  post-run diff collected by Proxy-owned `git` against the base commit, plus untracked-file
  enumeration. See writable-overlay-and-diff contract.

## 6. Open operator decisions (required before the consuming gate)

These are the genuine operator-sealing decisions. The amendment defines the slot and a safe
default where one exists; an operator must seal the final value. No gate that *executes* a
model task may start until all are sealed.

1. Lane-to-executor binding: which existing canonical-harness command, configuration, and
   implementation commit backs lanes A (primary) and C (challenger). The run packet labels
   lanes but binds no harness. `OPERATOR_REQUIRED`.
2. Per-run context packet: the construction rule (which repository files, in what order,
   truncated how) and the context schema version. `OPERATOR_REQUIRED`.
3. Pinned provider-profile configuration artifact on disk binding `spiritos-qualification` to
   the local OpenAI-compatible bridge with no-auth. `OPERATOR_REQUIRED`.
4. Inactivity timeout, per-run model-request maximum, tool-call maximum, retry maximum,
   cgroup pids maximum, file-write maximum, event-count maximum, NDJSON max line length.
   `OPERATOR_REQUIRED` (safe defaults proposed in each spec).
5. Whether the attesting inference bridge may perform a single no-op real-model identity
   probe at Gate 2-J.9F, or must remain fixture-only until Gate 2-J.9H.
   `OPERATOR_REQUIRED` (default: fixture-only at 9F; real probe only at 9H under separate auth).

## 7. Non-goals reaffirmed

This amendment does not execute JCode, does not call a model, does not begin the 80-run
comparison, does not touch the frozen benchmark, does not modify the daily runtime, and does
not advance another campaign. It only specifies the sealed dispatcher for Terra High to
implement gate-by-gate after operator approval.
