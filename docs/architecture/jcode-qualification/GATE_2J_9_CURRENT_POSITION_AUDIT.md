# Gate 2-J.9 Current Position Audit

status: `INDEPENDENTLY_AUDITED_DISPATCHER_ABSENT_AMENDMENT_REQUIRED`

schema: `source-proxy.gate-2j-9-current-position-audit/v1`
auditor: GLM (independent systems auditor)
audit_date_utc: 2026-07-29T19:30:00Z
audit_mode: read-only evidence audit against Git, campaign docs, source, and receipts.
  No JCode process was launched, no model request was sent, no fixture was executed,
  no benchmark was touched, and the daily runtime was not modified.

## 1. Canonical repository, branch, and HEAD

| Field | Verified value |
|---|---|
| Repository root | `/home/source/SpiritOS-source-proxy-jcode-qualification-20260726` |
| gitdir / common-dir | `/home/source/SpiritOS/.git/worktrees/SpiritOS-source-proxy-jcode-qualification-20260726` / `/home/source/SpiritOS/.git` |
| Branch | `codex/source-proxy-jcode-qualification-20260726` |
| Full HEAD | `cbba33aa6f617bbb6c83438079541035155a9207` |
| Upstream | `origin/codex/source-proxy-jcode-qualification-20260726` |
| Ahead / behind upstream | `0 / 0` (pushed) |
| Working tree | clean (index clean, no tracked changes, no untracked files) |
| Merge-base with master | `85dee8b59cce39afe1fbe7d674c066ccca1e6f13` |
| Commits unique vs master | 530 (long-lived campaign branch subsuming Campaigns 0-3) |
| Commits since qualification base | 112 |

The reported clean pushed HEAD `cbba33aa6` is correct and exact.

## 2. Commit relationship among reported campaign commits

Linear ancestry, all on this branch, newest last:

```
794b238ce156b9b2f92e7dab4521cfb2171e11ba  docs(c2j): record failed reproducibility retry     (2026-07-27 21:35 -0400)
        -> ae8bbc4085e58600a7f6701b94d95c0c0f2ae0da  docs(c2j): attest reproducible Dell binary and reseal packet  (2026-07-27 23:04 -0400)
                -> cbba33aa6f617bbb6c83438079541035155a9207  docs(c2j): record sealed execution contract authority gap  (2026-07-27 23:11 -0400) = HEAD
```

Independently proven: `ae8bbc408` IS an ancestor of `cbba33aa6`; `794b238ce` IS an ancestor of
`cbba33aa6`. The build-repair commit and the reported clean pushed HEAD are on one line.

## 3. Current Campaign 2-J gate

Gate 2-J.9 (Controlled comparison) is **not started**. Gate 2-J.10 (Adoption) is **not reached**.
The campaign is blocked before any Gate 2-J.9 task because no canonical contained dispatcher exists.

## 4. Verified build and binary status

The Dell two-build reproducibility attestation is independently confirmed against the provisioned artifact:

| Field | Verified value | Source |
|---|---|---|
| Approved binary path | `/home/source/.codex-audits/jcode-dell-remediation-20260727/approved-binary/jcode` | on disk |
| SHA-256 | `2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6` | matches report + receipt + preparation.py constant |
| Size | 233,979,416 bytes | matches |
| Mode | 755 | matches |
| Format | ELF 64-bit LSB pie, x86-64, dynamically linked, not stripped | matches |
| Version | `jcode v0.58.51-dev (2444e7b6)` | matches |
| Pinned source commit | `2444e7b6bc80d421ae3ee404081bdb41150a1830` | matches |
| Resealed packet SHA-256 | `4fee8fc9d0ffa8711cd300cab473adb5606ebacfdfd444ce9bcfb33b02f3f615` | recomputed, matches sidecar |

Binary prerequisite is green. The stale field in `FINAL_STRUCTURED_RECEIPT.json`
`binary_provider_model_truth.binary_sha256` previously recorded the historical
`d7598ca48...`; this audit's receipt update corrects it to the new canonical hash and preserves
the historical value under `historical_binary_sha256`.

## 5. Packet digest

Current packet: `GATE_2J_8_5_EXECUTABLE_RUN_PACKET.json`, SHA-256
`4fee8fc9d0ffa8711cd300cab473adb5606ebacfdfd444ce9bcfb33b02f3f615`.
Previous packet digest (pre-reseal): `a8c7c35353b0512f35d4d677e1ca560f1ad285d2210d60de0db87a83abc3aa27`.

## 6. Benchmark and daily-runtime isolation

- Benchmark: From qualification base `1641ddb1c` to HEAD, 112 files changed; **zero are
  benchmark paths**. The frozen `benchmarks/coder-backend-100/**` and
  `benchmarks/source-proxy-basic-backend-10/**` trees are untouched during Campaign 2-J.
  (They appear in a master-vs-branch diff only because the branch subsumes earlier campaigns;
  that is not a Campaign 2-J change.)
- Daily runtime: `/home/source/SpiritOS` is on branch `master` @ `85dee8b59` with its
  pre-existing 4,842-file dirty state. It is a different worktree, different branch, and
  different HEAD from the 2-J worktree. Campaign 2-J did not touch it.

## 7. Independent component classification

Per Gate 2-J.9 audit requirement, each JCode component classified
(PROVEN / PARTIAL / DECLARED_ONLY / MISSING / UNSAFE / BLOCKED_BY_UNSEALED_CONSTANT).
Passing unit tests are NOT treated as proof of live integration.

| Component | File | Classification | Basis |
|---|---|---|---|
| Envelope schema + fail-closed validation | `adapter.py` | DECLARED_ONLY | schema + validator exist; `live_ready` hardcoded False, `would_run_task` always False |
| CLI capability probe | `adapter.py build_jcode_cli_status` | PROVEN | version/source probe exercised; binary_and_source_match derivable |
| CLI argv policy | `adapter.py validate_jcode_cli_argv` | PROVEN | static denylist enforced, tested |
| Subprocess env builder | `adapter.py jcode_subprocess_env` | PARTIAL | builds env but never spawned; JCODE_HOME isolated by construction |
| Provider config renderer | `adapter.py render_jcode_provider_config` | PARTIAL | renders TOML preview; never written to a real JCODE_HOME, never enforced |
| Binary identity check | `identity.py verify_jcode_binary_identity` | PROVEN | hash+commit+version reconciliation, tested |
| Model identity reconciliation | `identity.py reconcile_jcode_model_identity` | PARTIAL | schema exists; requires a live provider receipt no component produces |
| Filesystem containment (read-only negative) | `containment.py` + `sandbox/bubblewrap.py` | PROVEN (negative only) | bwrap `--unshare-net` + ro-binds + empty workspace proven; no writable overlay |
| Writable overlay / disposable worktree | none | MISSING | no per-run worktree creation, no overlay mount, no post-run diff |
| Network bridge (byte-forwarding) | `network_bridge.py` + `loopback_bridge_runner.py` | PARTIAL | one loopback Unix relay proven; explicitly byte-forwarding, no model/param attestation |
| Sealed inference bridge (attesting) | none | MISSING | no request-enforcement proxy, no provider/model attestation, no budget enforcement |
| Process supervision | `supervision.py` | PARTIAL | process-group SIGTERM/SIGKILL + reap proven for generic commands; not bound to a contained JCode tree, no cgroup resource limits, no descendant discovery beyond pgrp |
| Strict NDJSON evidence mapper | `evidence.py map_jcode_ndjson_evidence` | PARTIAL | enforces sequence + terminal sentinel + result fields; no per-event schema, no prev-hash chain, no unknown-event quarantine, no stdout-contamination handling |
| Run-packet preparation (no exec) | `preparation.py` | PROVEN | seals manifest+fixture+registry into packet; never executes; resealed hash verified |
| Dispatcher / runner (launch JCode per task) | none | MISSING | no component launches the attested JCode binary in containment for a task |
| Independent Git diff collector | none | MISSING | no post-run `git diff`/untracked/deleted/renamed accounting |
| Terminal-state mapping to Proxy truth | none | MISSING | no map from dispatcher outcomes to COMPLETED_VERIFIED / ESCALATION / BLOCKED |
| Qualification fixture runner | `qualification_fixture/runner.py` | DECLARED_ONLY | `return TaskState()` stub; no dispatch |

## 8. Blocker summary (independent confirmation)

The campaign's own authority-gap audit is **corroborated**. Six sealed execution constants
are genuinely absent from the implementation:

1. lane-to-executor binding for the existing canonical harness (lanes A/C have no harness command/config/commit);
2. per-run context packet contents and SHA-256;
3. pinned provider-profile configuration binding `spiritos-qualification` to the local bridge + no-auth policy;
4. generation-request enforcement and actual-model attestation (the bridge is byte-forwarding by design);
5. JCode-to-Proxy strict NDJSON result mapping with raw-output location and independent-checker contract;
6. writable allowed-path overlay and post-run diff contract.

All other §3.3 authority constants (harness ID, adapter ID, schemas, binary, source, registry
model digests, gross budgets, tool allow/deny, endpoint) are present and sealed; they are
reproduced in `GATE_2J_9_AUTHORITY_CONSTANTS_MATRIX.md`.

## 9. Stop-condition check (per §17)

None of the stop conditions require halting the amendment: repository state is unambiguous,
the campaign base is proven, no operator choice is needed to *write* the amendment (operator
choices are flagged explicitly where they gate execution), and writing the amendment touches
only this doc directory. No benchmark or daily-runtime mutation occurs.

## 10. Explicit confirmation

No JCode task executed. No model request occurred. No fixture was run. No benchmark or
daily-runtime mutation occurred. This audit produced only documentation artifacts.
