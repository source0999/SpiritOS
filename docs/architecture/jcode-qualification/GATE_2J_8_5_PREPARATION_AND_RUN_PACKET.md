# Gate 2-J.8.5 Preparation and Executable Run Packet

status: `SEALED_PRE_EXECUTION_NO_TASKS_RUN`

## Scope

This bounded preparation gate creates the immutable diagnostic fixture and
seals the exact Gate 2-J.9 inputs. It does not start JCode, make a generation
request, execute a diagnostic task, enable the executor, or touch the frozen
benchmark or daily runtime.

## Sealed inputs

| Field | Value |
|---|---|
| Frozen diagnostic manifest | `archive/pre-2j-normalization-20260727/jcode_qualification_manifest.json` |
| Manifest SHA-256 | `149e2cdc7407f19cb4b0a431edb246affaaaeebabaa0694a22af57dcb6cadbb6` |
| Fixture commit | `12706316e72494144846f59a2130e2dd2bd83086` |
| Fixture roots | `qualification_fixture/`, `fixture_proxy/` |
| Fixture files / tree SHA-256 | `42` / `69c138d6835b02bed4e67fc6ddd0f168015d3bf8d81cb8b46c7ab8bd63870de5` |
| Local registry receipt | `GATE_2J_8_5_LOCAL_MODEL_REGISTRY_20260727.json` |
| Sealed packet | `GATE_2J_8_5_EXECUTABLE_RUN_PACKET.json` |
| Packet SHA-256 | `a8c7c35353b0512f35d4d677e1ca560f1ad285d2210d60de0db87a83abc3aa27` |

The fixture source and protected tests are deliberately committed in an initial
state suitable for the exact 20 manifest tasks. No task test command was run
in this gate; only Python compilation and the packet-builder tests ran.

## Model and route binding

The read-only local Ollama registry at `http://127.0.0.1:11434/api/tags`
attests both required models: `qwen2.5-coder:7b` digest
`dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364` and
`qwen2.5-coder:14b` digest
`9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849`.
Both report `Q4_K_M`. The packet fixes local loopback routing, no credentials,
no fallback, JCode profile `spiritos-qualification`, and the sandbox bridge
endpoint `http://127.0.0.1:4000/v1` forwarding only to host loopback port
`11434`.

Generation values are drawn from the existing adapter contract: temperature
`0`, seed `7`, max tokens `4096`, turn budget `4`, aggregate token budget
`32768`, timeout `300` seconds, and maximum raw output `2000000` bytes.

## Deterministic comparison plan

The packet fixes 80 prospective runs: each of the 20 tasks first in paired
primary lanes A then B, followed by the same 20 tasks in paired challenger
lanes C then D. Every future run requires a fresh disposable worktree and
executor home; JCode lanes additionally require a fresh `JCODE_HOME`. The
packet fixes the allowlist, denied tools, no-session/no-memory policy, fixed
bridge, strict NDJSON requirements, and Proxy-owned independent final checks.

## Required Gate 2-J.9 preflight

The pinned audit checkout remains at
`2444e7b6bc80d421ae3ee404081bdb41150a1830` and currently contains no JCode
binary. Its preserved scoped Rust toolchain is available through its recorded
`CARGO_HOME` and `RUSTUP_HOME`, but no substitute binary was selected. Before
any task, locate or rebuild the approved binary with the recorded offline serial
profile and prove exact SHA-256
`d7598ca48bb4fc8ff9c37d122fde5dd47314cd36fc2516ce6156795b71a545cc`.

After binary proof, run only the packet's no-model containment, supervision,
evidence, and actual-model-binding preflight from fresh state. Registry
presence is availability evidence, not an observed actual-model result. Gate
2-J.9 may then begin only if every preflight check passes.

## Binary recovery attempt

On 2026-07-27, the authorized recovery sweep checked executable files named
`jcode` in `/home/source`, `/tmp`, `/var/tmp`, and `/var/lib/docker/volumes`
against the full approved SHA-256. It found zero executable candidates and zero
matches. A fresh isolated build then used source commit `2444e7b6`, lockfile
SHA-256 `9b48f643ae298e655db7bbe68a548feb8414a634de5cf55d2b1994426e3bac19`,
Rust/Cargo `1.97.1`, the exact serial no-default-feature command, and image
`rust@sha256:77fac8b98f9f46062bb680b6d25d5bcaabfc400143952ebc572e924bcbedc3fa`.
The compiler terminated with `SIGSEGV` before producing `target/debug/jcode`.
No binary was provisioned, no hash was replaced, and the packet remains sealed
against the original approved binary. See `GATE_2J_8_5_BINARY_RECOVERY_ATTEMPT.md`.

## No-execution receipt

## Dell binary reseal addendum

The original packet digest a8c7c35353b0512f35d4d677e1ca560f1ad285d2210d60de0db87a83abc3aa27
is historical. The Dell remediation produced two matching fresh offline builds
of pinned source 2444e7b6bc80d421ae3ee404081bdb41150a1830 with new canonical
binary SHA-256 2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6.
The packet was resealed at 2026-07-28T02:58:43Z with digest
4fee8fc9d0ffa8711cd300cab473adb5606ebacfdfd444ce9bcfb33b02f3f615.
The provisioned controlled audit artifact is
/home/source/.codex-audits/jcode-dell-remediation-20260727/approved-binary/jcode.
The full provenance and Dell health receipt is
GATE_2J_8_7_DELL_BUILD_HEALTH_AND_REPRODUCIBILITY.md.

This removes only the binary-incomplete condition. It does not enable JCode,
execute a task, or relax the contained-runner and evidence preflight.

| Item | Result |
|---|---|
| JCode processes | `0` |
| Model generation requests | `0` |
| Diagnostic tasks attempted/completed | `0 / 0` |
| Frozen benchmark executions | `0` |
| Daily-runtime use | `0` |
| Production wiring enabled | `false` |
| Gate 2-J.10 reached | `false` |
