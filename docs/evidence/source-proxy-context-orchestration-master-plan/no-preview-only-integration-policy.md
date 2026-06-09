# No Preview-Only Integration Policy

Status: policy for the master plan. This does not authorize runtime changes.

## Policy

SpiritOS Source Proxy coding readiness cannot be accepted because a route exists, a UI renders, a preview completes, a demo responds, or documentation says a system is integrated.

Integration means the real `/coding` hot path uses Source Proxy to assemble a task-specific coder packet from polished systems, passes that packet to the selected coder model, validates the output contract, and writes durable evidence.

## Banned Acceptance Claims

- Route exists, therefore integrated.
- Preview works, therefore production-ready.
- Repomix output exists, therefore full repo context exists.
- A design packet route exists, therefore design is integrated.
- A Cartographer map exists, therefore Cartographer is feeding coder context.
- A Scout/Search route exists, therefore research context is available.
- A helper agent can run, therefore subagent orchestration is ready.
- A screenshot or UI card exists, therefore Source Proxy used the packet.
- Docs describe the intended flow, therefore the flow is accepted.

## Required Diagnostics

Every context source must report one of:

- `used`: packet produced, included, and cited in final coder packet
- `skipped`: intentionally skipped with visible reason
- `blocked`: intended source could not produce a packet and the reason is visible

Silent omission is a failed run.

## Repomix Boundary

Repomix is allowed as one fallback context source. It must not be described as the main repo-context brain, the full-context guarantee, or a substitute for task-specific Source Proxy orchestration.

If a run is fallback-only, Source Proxy must block or warn visibly and record that fallback-only status in the durable receipt.

## Authority Boundary

No preview, advisory packet, helper output, Scout result, Design critique, Cartographer map, or Repomix packet may secretly apply code, commit, push, enqueue continuation, or run background workers.
