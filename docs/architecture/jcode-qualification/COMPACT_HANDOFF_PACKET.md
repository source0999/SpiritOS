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

The Gate 2-J.9 sealed-execution amendment is written and awaits operator review
(`GATE_2J_9_SEALED_EXECUTION_ARCHITECTURE.md` and its companion specs). The first authorized
workflow gate is **Gate 2-J.9A - Authority Constants and Canonical Schemas**, blocked until
the five operator decisions in the architecture spec are sealed (or explicitly blocked).

Current verified position: branch clean, pushed 0/0, HEAD
`cbba33aa6f617bbb6c83438079541035155a9207`; binary prerequisite green
(`2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6`); resealed packet
`4fee8fc9d0ffa8711cd300cab473adb5606ebacfdfd444ce9bcfb33b02f3f615`; benchmark unchanged;
daily runtime untouched; JCode disabled and non-executing; no model request occurred.
See `GATE_2J_9_CURRENT_POSITION_AUDIT.md` for the independent audit.
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
