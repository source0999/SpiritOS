# JCode Source Audit

All findings are pinned to
`2444e7b6bc80d421ae3ee404081bdb41150a1830`. Upstream README or website claims
were treated as hypotheses; source and test behavior take precedence.

## Build and test record

| Classification | Command/result |
| --- | --- |
| REPRODUCED BEHAVIOR | Initial locked source check failed because the host lacks `libssl-dev`; no system package was installed. |
| REPRODUCED BEHAVIOR | `cargo check --locked --no-default-features --features linux-compat-vendored-openssl --bin jcode` passed in 1m55s with one Bedrock dead-code warning. |
| REPRODUCED BEHAVIOR | `cargo test --locked -p jcode-provider-openrouter -p jcode-harness-api -p jcode-harness-api-server` passed 34 tests (6 + 8 + 20), zero failures. |
| REPRODUCED BEHAVIOR | `cargo test --locked --no-default-features -p jcode-base safety -- --nocapture` passed 9 safety tests; 1124 tests filtered. |
| REPRODUCED BEHAVIOR | A first default-feature safety-test build crashed `rustc` with `SIGSEGV` while compiling the large embedding/AWS graph. The constrained no-default-feature run passed. |
| REPRODUCED BEHAVIOR | The deterministic `jcode-harness` binary built/runs with constrained jobs/stack and directly read, wrote, edited, multi-edited, patched, applied a patch, and ran `bash pwd` in an isolated fixture. |

The successful source build used Rust `1.97.1`, jobs constrained for this host,
the locked dependency graph, no default features, and vendored OpenSSL. The
workspace includes about 79 crate directories and an 11,294-line `Cargo.lock`,
which is a meaningful build/update surface.

## Capability evidence

| Capability | Advertised behavior | Source/test evidence | Reproduced behavior | Limitation/security implication | SpiritOS fit | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| Headless execution | one-shot noninteractive run | `src/cli/args.rs:145-167`; `src/cli/commands.rs:2786` | parser/tests and source build passed | NDJSON still depends on upstream stream integrity | good behind Proxy adapter | high |
| NDJSON events | machine-readable events | `run_single_message_command_ndjson`; `crates/jcode-protocol/src/wire.rs:862` | harness API tests passed | complete transcript/result contract not yet mapped | conditional | high |
| Tool allowlist | explicit `--tools` and disabled tools | `src/cli/args.rs:107-115`; `jcode-app-core/src/tool/mod.rs:321-329,548-569` | source tests/build passed | allowlist is tool-name level, not Proxy path capability | useful but insufficient | high |
| Base-tool disable | start from empty tool surface | `--disable-base-tools`; config selection at `jcode-base/src/config.rs:598-607` | parser/build passed | selected editing tools still need OS/path containment | useful | high |
| File discovery | read/glob/grep/list tools | `crates/jcode-app-core/src/tool` registry | deterministic harness used reads | repository instructions can influence model | bounded fit | high |
| File editing | write/edit/multiedit/patch/apply_patch | tool registry and harness binary | all mutation families changed isolated fixture | normal loop is not universally permission-gated | blocker without external sandbox | high |
| Shell execution | Bash/batch tools | `crates/jcode-app-core/src/tool/bash*`, `batch.rs` | harness ran `bash pwd` | destructive command exposure and env inheritance | deny in baseline | high |
| Safety classifier | classify risky actions/queue permission | `crates/jcode-base/src/safety.rs:187,551-580` | 9 targeted tests passed | production call-site search found `request_permission` in ambient path only | not an authority boundary | high |
| Normal tool execution | execute model tool calls | `agent/turn_execution.rs:459-479`; `agent/turn_loops.rs:1009` | harness mutated directly | registry execution does not invoke the safety classifier | external containment required | high |
| Ambient approval | request permission before ambient mutation | `tool/ambient.rs:640-703`; ambient tests | targeted tests cover safety primitive | tool is unavailable to normal sessions (`tool/tests.rs:622-636`) | cannot replace Proxy approval | high |
| OpenAI-compatible provider | configurable provider/model endpoint | provider config and OpenRouter/OpenAI runtime crates | provider tests passed, no live model call | must prevent direct cloud/credential fallback | loopback inference only | medium-high |
| Provider/model selection | profile and model CLI/config | `src/cli/args.rs`; provider configuration | parser/build passed | issue #380 reports runtime identity divergence class | Proxy must bind and verify actual model | medium |
| MCP | discover/register external tools | `src/cli/commands.rs:2479-2538`; MCP manager | source says run MCP defaults on | project MCP is prompt/network expansion | force off | high |
| Auto-poke | continue unfinished work | `src/cli/commands.rs:2469,2564,2698-2714` | source default is enabled | turn count can expand unless explicitly capped | force off/max 1 | high |
| Auto-update/selfdev | update and self-development workflows | `src/cli/startup.rs:347`; `dispatch.rs:880-883`; selfdev tools | flags parse/build | campaign reproducibility and supply-chain risk | force `--no-update --no-selfdev` | high |
| Project instructions | load project/global `AGENTS.md` | `jcode-base/src/prompt.rs:396-408,815-890` | source tests prove loading | repository and global prompt injection surface | inspect project instructions; fresh HOME | high |
| Prompt overlays | load project/global `.jcode/prompt-overlay.md` | `prompt.rs:407-410,861-890`; prompt tests | tests prove both overlays load | hidden cross-task/control injection | reject overlays | high |
| Sessions/resume | persistent and restorable sessions | `agent/turn_execution.rs` restore methods; server/session crates | unit coverage present | stale-session resurrection/cross-task leakage risk; open resume issues | fresh session only | medium-high |
| Memory | extraction/search/semantic memory | memory/session-search crates | not exercised in this audit | contamination and hidden benchmark retention | force off | medium |
| Swarm/task graphs | multi-agent coordination | swarm/config/tool modules | not exercised | concurrency/race and authority duplication risk | force off | medium |
| Harness API | create/attach/message/events/cancel | `jcode-harness-api` and server bridge | 28 API/server tests within 34-target run passed | permission response unsupported; list sessions partial | reject sidecar now | high |
| Cancellation | API/CLI cancellation surfaces | harness bridge `cancel`; agent interrupts | unit tests only | process-group and post-cancel write containment unproven | Proxy must own | medium |
| Retry/recovery | provider retries and restart/resume | provider/server recovery modules | unit source only | boundedness and full evidence need adapter proof | Proxy budget must dominate | medium |
| Event parsing | streamed tool/content handling | provider runtimes; harness API client | malformed chunks may be skipped by a green test | skipped/truncated events can destroy evidence | independent completeness checks required | high |
| Telemetry | documented telemetry with opt-out | `TELEMETRY.md`; env controls | source inspected | privacy/egress risk if defaults drift | force `DO_NOT_TRACK` and no telemetry | medium-high |
| VCS actions | commit/PR/selfdev workflows exist | VCS/selfdev/ambient source | not exercised | executor must not commit/push | deny tools and external Git checks | high |
| Browser/network | browser/web fetch/search/provider access | computer/browser/web tools/provider crates | not exercised | unauthorized network and credential risk | deny; OS egress guard required | high |
| Cross-platform | Linux/macOS/Windows paths and release code | platform/release modules | Linux source build passed | Windows/release reliability not reproduced | Linux-only qualification initially | medium |

## Issue review

Open issues were read as risk signals, not assumed proof against this SHA:

- `#604` destructive-command guardrail/home deletion: source-relevant because
  normal shell/tool execution is not universally safety-classified; destructive
  behavior was not reproduced.
- `#609` and `#610` streamed/tool-call corruption: not reproduced against a live
  provider; source/tests show malformed chunks can be skipped.
- `#144` stable external orchestration API: directly consistent with the partial
  harness bridge found in source.
- `#64` project MCP trust approval, `#476` serve/connect broken pipe, `#380`
  provider/model identity, `#559` overload retry, `#600` resume after reload,
  `#608` model picker persistence, `#76` swarm behavior, `#354` session saving,
  `#62` safe evaluation profile, and `#471` read-before-edit are unresolved risk
  classes for later targeted reproduction.

Source: `https://github.com/1jehuang/jcode` and its numbered issue pages.

## Conclusion

`INFERENCE`: JCode is a capable coding runtime, not a governance substrate. Its
headless CLI, tool filter, provider profile, and event stream make it plausible
as a Layer 4 challenger. Its normal mutation path, prompt overlays, defaults,
partial sidecar API, and evidence risks make it unsafe for direct production or
as-is live qualification.
