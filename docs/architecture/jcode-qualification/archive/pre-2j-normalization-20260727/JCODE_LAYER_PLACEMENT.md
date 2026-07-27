# JCode Layer Placement

Primary placement: **Layer 4, Cognitive Execution Runtime**.

`INFERENCE`: JCode's bounded model/tool loop is replaceable execution machinery.
It is not a task authority, approval service, router, independent verifier, or
campaign oracle.

| JCode subsystem | Layer | May do | Must not own |
| --- | --- | --- | --- |
| `jcode run --ndjson` agent loop | 4 | within-task planning, model turns, permitted tool requests | canonical task state or final outcome |
| provider profile/runtime | 5 edge | call exact designated loopback model route | choose provider/model, hold cloud credentials, fallback silently |
| read/glob/grep/list | 2/6 extension | discover files allowed by executor packet | canonical context selection or hidden data access |
| write/edit/patch tools | 6 extension | propose changes inside externally enforced paths | authorization, protected-path policy, commit/push/deploy |
| event/transcript/session machinery | 8 extension | emit complete per-task raw evidence | canonical evidence store, cross-task memory, benchmark retention |
| tests/review concepts | 6/7 input only | invoke allowed test command and return results | independent reviewer/verifier/anti-cheat verdict |
| safety/permission concepts | 7 input only | supply additional denials | Proxy approval or policy authority |
| MCP/browser/web/memory/swarm/selfdev | none in baseline | nothing | any campaign baseline capability |

## Belongs here / must not own

| Belongs in JCode boundary | Must remain outside JCode |
| --- | --- |
| bounded coding loop | human intent and rejection rights |
| permitted file discovery | canonical task/acceptance packet |
| selected model interaction | task database and terminal state |
| permitted edit proposals | model router and provider authorization |
| allowed tool invocation | worktree/base/protected-path policy |
| bounded retry within Proxy budget | approvals and mutation authorization |
| complete raw event stream | cancellation authority and independent diff |
| claimed executor outcome | reviewer, verifier, oracle, anti-cheat |
| per-task transient state | commit, push, deployment, benchmark oracle |

Terra High may later submit canonical Source Proxy tasks that select this
executor after qualification. Terra High must not embed or call JCode as an
independent authority path.
