# Compact Handoff Packet

## Current state

## Superseding binary status

The historical binary-mismatch summary below is superseded for the binary
prerequisite only. Two fresh Dell builds now match at
2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6 and the
packet was resealed as
4fee8fc9d0ffa8711cd300cab473adb5606ebacfdfd444ce9bcfb33b02f3f615. The
remaining Gate 2-J.9 blocker is the absence of a contained runner that applies
the sealed budgets and emits the complete required evidence.

Campaign 2 benchmark authority is accepted at `17f3ce87`. Gate 2-J.8.5 is
sealed without execution: fixture commit `12706316e72494144846f59a2130e2dd2bd83086`,
fixture-tree SHA-256 `69c138d6835b02bed4e67fc6ddd0f168015d3bf8d81cb8b46c7ab8bd63870de5`,
and run-packet SHA-256 `a8c7c35353b0512f35d4d677e1ca560f1ad285d2210d60de0db87a83abc3aa27`.
The packet attests both canonical local Qwen coder models, fixed budgets, and
an 80-run A/B-first then C/D order. JCode remains disabled and non-executing;
the frozen benchmark and daily runtime are untouched.

## Next gate

Before any Gate 2-J.9 task, reconstitute the pinned JCode binary with the
recorded offline serial profile and verify SHA-256
`d7598ca48bb4fc8ff9c37d122fde5dd47314cd36fc2516ce6156795b71a545cc`.
The authorized local recovery sweep found no candidate binary. Gate 2-J.8.6
then ran two fresh pinned Docker builds. Build 1 produced
`c490cf35737564ad0a45e2b3e8f15d6cf9289feaee32e53597c29fede2316cfc`, which
does not equal the approved hash; build 2 failed in `rust-lld` with `SIGSEGV`.
No replacement hash or packet change was accepted. See
`GATE_2J_8_6_PINNED_BINARY_PROVISIONING.md`. No task may start until an
approved binary, containment, evidence, and actual-model checks pass from fresh
state.

## Prohibited next actions

Do not execute JCode or a diagnostic task during this preparation stage, change
the sealed fixture/packet, import JCode into a production path, start Campaign
3, alter the benchmark, or use the daily runtime.

## Evidence roots

Canonical packet: this directory. Raw pre-normalization evidence:
`archive/pre-2j-normalization-20260727/`. Disabled seam:
`source_proxy/jcode/adapter.py`. Focused boundary test:
`source_proxy/tests/test_jcode_qualification_adapter.py`. Preflight receipt:
`GATE_2J_9_PREFLIGHT_BLOCKER.md`. Gate 2-J.8.5 receipt:
`GATE_2J_8_5_PREPARATION_AND_RUN_PACKET.md`.
