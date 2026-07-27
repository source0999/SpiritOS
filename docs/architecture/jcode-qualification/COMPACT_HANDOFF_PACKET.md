# Compact Handoff Packet

## Current state

Campaign 2 benchmark authority is accepted at `17f3ce87`. Campaign 2-J is at
Gate 2-J.0 only. JCode remains a disabled, non-executing Layer 4 candidate;
the frozen benchmark and daily runtime are untouched.

## Next gate

Gate 2-J.1 must record the exact Python interpreter and venv, reproduce the
registered coding pack, characterize the known order-dependent baseline defect,
and prove JCode introduces no new regression. It must not call the result green
unless the registered pack is actually green.

## Prohibited next actions

Do not execute JCode, seal or run the diagnostic fixture, import JCode into a
production path, start Campaign 3, alter the benchmark, or use the daily
runtime. Those actions require later gates and explicit work packets.

## Evidence roots

Canonical packet: this directory. Raw pre-normalization evidence:
`archive/pre-2j-normalization-20260727/`. Disabled seam:
`source_proxy/jcode/adapter.py`. Focused boundary test:
`source_proxy/tests/test_jcode_qualification_adapter.py`.
