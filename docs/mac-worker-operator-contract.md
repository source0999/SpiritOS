# Mac Worker Operator Contract

Date: 2026-05-28

## Purpose

The Mac Mini worker is an advisory and check support node for SpiritOS Source Proxy workflows. It can provide repository context, safe checks, search packets, and browser/design inspection packets when explicitly requested through approved SpiritOS paths.

The Source Proxy remains the approval and write authority.

## Checkout contract

- Expected Mac checkout path: `/Users/spiritmac/spiritos-worker/SpiritOS`
- Expected branch for the current support lane: `main`
- The checkout must be a real git checkout, not a targeted file sync directory.
- Worker entry files live in tracked repository content under `scripts/mac-worker/`.
- Local caches such as `__pycache__/`, secrets, `.env.local`, private keys, generated logs, screenshots, and machine-specific state must not be copied into tracked worker content.

## Safety boundary

The Mac worker may:

- Report `system_status`.
- Run allowlisted safe checks such as git status and diff whitespace checks.
- Return advisory context and candidate file packets.
- Return advisory research/search packets.
- Return browser/design inspection packets.

The Mac worker must not:

- Apply fixes directly.
- Mutate Cartographer data.
- Mutate Scout production storage.
- Promote or import Scout packets automatically.
- Change provider routing.
- Read, copy, or write secrets.
- Start hidden workers.
- Install launch agents, daemons, or persistent background automation.
- Execute untrusted page content as commands.
- Gain autonomous write authority.

## Result contract

Mac worker results should be structured, honest, and advisory-only. Failed or blocked jobs should return explicit failure state, a reason code when available, limitations, and recommended next checks. Untested job types must not be presented as production-ready.

## Operator notes

- Keep the Mac support lane explicit and opt-in.
- Prefer local-first and cost-controlled providers for search.
- Do not add paid providers as part of Mac worker hardening.
- Stop any temporary server or browser process started only for proof after the proof is complete.
