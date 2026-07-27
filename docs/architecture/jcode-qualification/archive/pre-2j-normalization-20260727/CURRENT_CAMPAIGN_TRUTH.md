# Current Campaign Truth

## Authoritative sequence

The current Gate B plan is the controlling sequence for new work:

| Campaign | Purpose | Evidence state |
| --- | --- | --- |
| 0 | Repository/runtime truth | accepted at `bbe195111e202afe8610cd02adf528f0e92857c7` |
| 1 | Terminal truth | accepted at `4e5772182cdf879ab2a05243e916f7760f22b41c` |
| 2 | Full-pipeline benchmark authority | implementation complete at `1641ddb1c71e6b364e98aa9aeff4b4719627d926`; operator acceptance pending |
| 3 | Repository search/index/context | not started |
| 4 | Scout/Obsidian causal integration | not started; does not unpause the historical `/coding` UI campaign |
| 5 | Diagnostics/adaptive recovery | not started |
| 6 | Model roles and authorized escalation | not started |

Exact Gate B order is immutable for this qualification. Campaign 2-J is a
non-advancing candidate annex, not a new number in the success chain.

## Current gate

`VERIFIED FACT`: C0 -> C1 -> C2 is linear. C0 and C1 have acceptance receipts.
C2's canonical acceptance matrix and operator packet say operator acceptance is
pending. Therefore C3 through C6 cannot start from this work.

`BLOCKER`: no full campaign green or operator acceptance token exists for C2.
The only authorized campaign action is explicit operator accept/reject review of
the existing C2 packet.

## Campaign 4

`VERIFIED FACT`: `docs/architecture/campaign-4-state.json` and
`docs/architecture/campaign-4-stub.md` preserve the historical `/coding` UI
campaign as paused. A future Gate B stage also uses the label Campaign 4 for
causal Scout/Obsidian integration. This naming collision does not authorize
either stage and this annex changes neither file.

## Terra High

`VERIFIED FACT`: no tracked `Terra High` or `Terrha High` component was found in
the selected current/planning source. It is treated as the requested downstream
product intent, not as an existing authority or repository identity. Any later
Terra High use must enter through Source Proxy's canonical task and executor
contracts; it must not call JCode directly.

## Historical context

Earlier Campaign 3/3.5/4 receipts remain historical evidence for extended lanes,
backend governance, and a paused UI. They are not rewritten, renumbered, or used
to bypass the newer C0-C6 acceptance chain. The planning-only commit
`f45a7851ec688bcc99045f4c05ad80c4903ce094` is not an ancestor of the current C0
implementation line, so its prose is context rather than executable authority.
