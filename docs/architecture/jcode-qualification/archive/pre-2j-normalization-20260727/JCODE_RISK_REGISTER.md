# JCode Risk Register

| ID | Risk | Severity | Current treatment | Status |
| --- | --- | --- | --- | --- |
| R-01 | normal JCode tool path bypasses safety classifier | critical | external capability/filesystem boundary | OPEN_BLOCKER |
| R-02 | shell/destructive command exposure | critical | deny Bash/batch; future sandbox | OPEN_BLOCKER |
| R-03 | path/symlink/worktree escape | critical | Proxy path preflight is not enough; OS write root required | OPEN_BLOCKER |
| R-04 | unauthorized network/provider access | critical | loopback config plus OS egress deny | OPEN_BLOCKER |
| R-05 | event truncation/malformed tool arguments | high | raw framed capture, sequence and terminal checks | OPEN_BLOCKER |
| R-06 | false success from executor claim | critical | existing independent gates only | CONTROLLED_BY_DESIGN |
| R-07 | session/memory cross-task contamination | high | fresh HOME/JCODE_HOME; memory/resume off | CONTROLLED_IN_PREVIEW |
| R-08 | project/global prompt injection | high | bind project instructions; reject overlays/global state | PARTIAL_OPEN |
| R-09 | MCP/skills expansion | high | MCP forced off; no skills in baseline | CONTROLLED_IN_PREVIEW |
| R-10 | provider/model substitution | high | fixed profile/model; runtime identity receipt still needed | OPEN_BLOCKER |
| R-11 | auto-update/selfdev drift | high | pinned SHA and no-update/no-selfdev | CONTROLLED_IN_PREVIEW |
| R-12 | cancellation descendants/post-stop writes | high | future process-group supervisor | OPEN_BLOCKER |
| R-13 | sidecar state/permission ambiguity | high | reject sidecar option | AVOIDED |
| R-14 | large dependency/resource burden | medium | locked no-default build; constrained resources | MONITOR |
| R-15 | campaign drift/unpausing Campaign 4 | critical | non-advancing 2-J annex; exact next action only | CONTROLLED_BY_PROCESS |
| R-16 | frozen benchmark leakage | critical | separate manifest, no run, no JCode exposure | CONTROLLED_BY_PROCESS |
| R-17 | Terra High bypasses Proxy | critical | product-neutral Proxy executor contract only | OPEN_GOVERNANCE |
| R-18 | dirty main/remote divergence contaminates evidence | high | isolated worktree, local-only commit | CONTROLLED_BY_PROCESS |

Machine-readable ownership, triggers, and evidence are in
`jcode_risk_register.json`.
