# Gate 2-J.9 Risk Register

status: `RISKS_IDENTIFIED_MITIGATIONS_BOUND_TO_GATES`

schema: `source-proxy.gate-2j-9-risk-register/v1`

| ID | Risk | Likelihood | Impact | Mitigation / bound | Owning gate |
|---|---|---|---|---|---|
| R1 | JCode identity cannot be attested (binary/source/version drift) | Low | High | identity.py reconciliation mandatory before launch; fail closed | 2-J.9G |
| R2 | Containment escape (fs/symlink/net) | Low | Critical | bwrap namespaces + ro base + isolated overlay + net unshare + loopback-only bridge; preflight | 2-J.9B |
| R3 | Model/provider substitution or silent fallback | Medium | Critical | attesting bridge rejects unknown model/endpoint; no fallback policy; identity reconcile | 2-J.9F |
| R4 | Process-tree leak (orphan children) | Medium | High | systemd cgroup scope + cgroup.procs enumeration + SIGKILL + empty check | 2-J.9C |
| R5 | Evidence loss / incomplete | Medium | High | sealed ledgers + hashing + refuse verification when incomplete + seal-on-abnormal-exit | 2-J.9D, 2-J.9J |
| R6 | Executor claim trusted as terminal truth | Medium | Critical | result mapping has no path from claim to COMPLETED_VERIFIED; independent checks mandatory | 2-J.9J |
| R7 | Frozen benchmark leakage to executor | Low | Critical | disposable worktree of base commit; benchmark paths not in context/overlay; anti-cheat check | 2-J.9E, 2-J.9J |
| R8 | Daily runtime contamination | Low | High | separate worktree/branch; daily runtime not in any bind; never run from /home/source/SpiritOS | all |
| R9 | Host resource exhaustion (OOM/CPU) | Medium | Medium | cgroup MemoryMax/TasksMax/CPUQuota; matches proven build profile; single job | 2-J.9B |
| R10 | ext4 checksum history (host maintenance) | Low | Low | historical, not reproduced during build proof; monitored; no action required for the artifact | (monitor) |
| R11 | Operator decisions stall the campaign | Medium | Medium | each decision has a safe default proposed; explicit block documented when unresolved | 2-J.9A |
| R12 | Recursion / bridge-to-/coding/ misuse | Low | Critical | bridge denies /coding route; recursion prevention; no production credentials | 2-J.9F |
| R13 | Concurrent runs interfering | Low | Medium | one run per cgroup scope; unique run_id; isolated run roots | 2-J.9B/C |

## Residual risk note

JCode remains `SPECIFIED_NOT_RUNTIME_PROVEN` until 2-J.9G/H/I pass. No artifact in this
amendment upgrades that status. Adoption (2-J.10) is a separate bounded decision and does not
make JCode a default executor.
