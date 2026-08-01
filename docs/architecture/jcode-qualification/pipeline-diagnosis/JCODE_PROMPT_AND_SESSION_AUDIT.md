# JCode Prompt and Session Audit

## Identity and Isolation

- Binary: `/home/source/.codex-audits/jcode-dell-remediation-20260727/approved-binary/jcode`
- SHA-256: `2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6`
- Version: `jcode v0.58.51-dev (2444e7b6)`
- Every D/F run used a fresh worktree, overlay, runtime root, HOME,
  `JCODE_HOME`, and session. Memory and session reuse were disabled.
- JCode had no direct route to Ollama; all provider traffic crossed the sealed
  socketpair relay and diagnostic bridge.

Fresh-state receipts rule out `JCODE_SESSION_OR_DEFAULT_CONTAMINATION` as a
cross-run cause. The built-in prompt itself remains a current-run contaminant.

## Exact First-Turn Prompt

The corrected capture has roles `system,user,user` with message lengths 2,004,
291, and 504 characters for Task R. The system prompt instructs JCode to be
maximally proactive, modify its own harness, use todo/open tools, and commit by
default. The sealed task simultaneously forbids Git mutation, self-development,
session reuse, memory, and undeclared tools. Several named JCode tools are not
available in the contained run.

Classifications:

- `JCODE_PROJECT_INSTRUCTION_CONTAMINATION`: generic JCode defaults are
  unrelated to the tiny sealed task.
- `PACKET_INSTRUCTION_CONFLICT`: commit/self-development defaults contradict
  the operator-bound no-Git/no-self-modification envelope.
- `CONTEXT_BUDGET_MISALLOCATED`: 2,004 characters are spent before the model
  sees the 504-character pointer message.

The CLI user message tells the model to read
`/workspace/DIAGNOSTIC_TASK.txt` and `/workspace/DIAGNOSTIC_CONTEXT.json` and
verify their hashes. It does not inline either file. Therefore the first model
turn cannot know the task details until a read succeeds. For Task R, legacy D
and F both produce a 2,801-character flattened backend prompt; their substantive
content is identical apart from packet hashes. Full Proxy bloat is mounted but
not model-visible on turn one.

## Tool and Loop Behavior

Capture-only preflight proves that JCode proposes `read` for Task R and
`apply_patch`, `read`, and `write` for Task W. The legacy bridge removes those
schemas before inference. The corrected bridge preserves them, but Qwen returns
text JSON. JCode surfaces that as `text_delta`/final text and records no tool
event, no dispatch, no edit, and no reinjected result.

JCode also has no focused-test capability in this contained profile. Task W
cannot reach complete qualification with only its current three tools.

## Suitability Decision

The pinned binary remains containment- and identity-suitable, but it is not yet
model-profile-suitable for either selected Qwen model. Qualification requires:

1. A sealed project system prompt that removes commit, self-development,
   unavailable-tool, and generic workflow instructions.
2. A first-turn packet that includes the concise task contract or a parser that
   reliably recovers Qwen's text read call.
3. A bounded focused-test tool for write tasks.
4. Text-call parsing and unchanged observation reinjection within the three-turn
   limit.

Until those are proven, JCode decisions are
`JCODE_TOOL_COMPATIBILITY_READY=false` and
`PIPELINE_NOT_READY_FOR_COMPARISON`.
