# Human Brain to AI System Brain Layer Map

Status: `PROPOSED FALLBACK MAP`.

`VERIFIED FACT`: the repository has canonical component and campaign documents,
but the minimal Source Proxy context did not reveal one accepted document using
a complete numbered human-to-system layer map. The requested fallback labels
are therefore used without replacing existing names such as canonical context
broker, CodingOrchestrator, CampaignApprovalAuthority, reviewer, verifier, and
anti-cheat.

| Layer | Established concern | Current Source Proxy components |
| --- | --- | --- |
| 0 Human intent and sovereignty | goals, values, approvals, rejection, final authority | human operator; operator assertion ceremony |
| 1 Executive translation | canonical task, scope, acceptance, risk | long-running task request/store; plan and campaign packets |
| 2 Perception and context | repository search, maps, context packets | canonical context broker, Cartographer, Scout, Obsidian, Mac Search |
| 3 Executive control/system orchestration | state, routes, budgets, cancellation, exact outcome | CodingOrchestrator, task store, model router, approval authority |
| 4 Cognitive execution runtimes | bounded coding/model/tool loop | current custom executor; candidate JCode CLI process |
| 5 Model substrate | coder/advisory/verifier models and inference | Qwen 7B primary; Qwen14B/Ornith challengers; Gemma/Hermes advisory; Ollama |
| 6 Motor and tool system | file, shell, tests, worktrees, VCS, network | Proxy tool action executor, target plugins, sandbox/worktree helpers |
| 7 Metacognition and immune system | review, verification, policy, anti-cheat | independent reviewer, verifier, oracle, anti-cheat, path/mutation guards |
| 8 Episodic memory, learning, evidence | traces, receipts, benchmark history | task/evidence stores, participant records, campaign receipts, sealed benchmark |
| 9 Human/system interface | status, approvals, explanations | `/coding` APIs and paused UI projection |

## Data flow

```mermaid
flowchart LR
    H["Human Intent Packet"] --> C["Canonical Task and Acceptance Packet"]
    C --> P["Proxy Control Packet"]
    P --> X["Context and Perception Packet"]
    X --> E["Executor Packet"]
    E --> B{"Authorized executor"}
    B -->|"baseline"| O["Existing harness"]
    B -->|"candidate, later"| J["One fresh JCode CLI process"]
    O --> M["Selected local model and allowed tools"]
    J --> M
    M --> R["Execution Evidence Packet"]
    R --> V["Reviewer, Verifier, Anti-Cheat Packet"]
    V --> T["Canonical Outcome Packet"]
    T --> U["Human-readable status"]
```

JCode receives only the Executor Packet and permitted context. Hidden verifier
expectations, benchmark solutions, approval internals, unrelated history,
credentials, and previous-task state do not cross the boundary.

## Control flow

```mermaid
flowchart TD
    A["Authenticated operator approval"] --> S["Proxy validates task, base, scope, route, budget"]
    S --> Q{"Executor selection authorized?"}
    Q -->|"no"| Z["BLOCKED_SAFE"]
    Q -->|"existing"| E["Run existing executor"]
    Q -->|"JCode gate not yet eligible"| Z
    Q -. "future Campaign 2-J only" .-> J["Spawn isolated JCode"]
    E --> D["Proxy independently captures diff and tests"]
    J --> D
    D --> R["Reviewer"] --> V["Verifier"] --> C["Anti-cheat"] --> F["Proxy finalizer"]
    F --> O{"Canonical outcome"}
```

The inference path may be `JCode -> loopback inference-only endpoint -> selected
model`. It may never be `JCode -> /coding`, preventing recursive orchestration.

## Trust boundaries

```mermaid
flowchart LR
    subgraph Human["Human authority"]
        A["Approve or reject"]
    end
    subgraph Proxy["Trusted Source Proxy control plane"]
        T["Task/state/router/budget"]
        G["Approval and mutation policy"]
        V["Review/verify/anti-cheat/final truth"]
    end
    subgraph Sandbox["Untrusted disposable executor boundary"]
        J["JCode process"]
        W["Disposable worktree and fresh JCODE_HOME"]
    end
    subgraph Model["Bound local inference"]
        M["Exact selected model"]
    end
    A --> G
    T --> J
    G --> J
    J --> W
    J --> M
    J -->|"raw events and claimed result"| V
    W -->|"independent Git diff"| V
    V --> A
```

JCode and model output are untrusted proposals. Source Proxy and the human
retain all authority.

## Failure containment

```mermaid
flowchart TD
    J["JCode task process"] --> F{"Failure class"}
    F -->|"timeout/cancel/crash"| K["Proxy kills process group and seals raw bytes"]
    F -->|"tool/path/network denial"| B["Proxy blocks capability and records attempt"]
    F -->|"stream gap/malformed event"| E["Evidence incomplete"]
    F -->|"claimed success"| D["Independent diff/tests/review/verify/anti-cheat"]
    K --> N["Non-success canonical outcome"]
    B --> N
    E --> N
    D -->|"any failure"| N
    D -->|"all gates pass"| P["Eligible verified outcome"]
    N --> C["Discard worktree and JCODE_HOME after receipt retention"]
    P --> C
```

No JCode exception, retry, or self-reported success can bypass the finalizer.
