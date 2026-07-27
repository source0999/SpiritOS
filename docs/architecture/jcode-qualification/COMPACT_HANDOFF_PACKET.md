# Compact Handoff Packet

## Current state

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
The current audit checkout has no binary and its non-interactive environment
does not expose Cargo. Then perform the packet's independent no-model runner
preflight; no task may start until the binary, containment, evidence, and
actual-model checks pass from fresh state.

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
