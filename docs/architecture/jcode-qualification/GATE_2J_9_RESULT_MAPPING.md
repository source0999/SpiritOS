# Gate 2-J.9 Result and Terminal-State Mapping

status: `TERMINAL_MAPPING_SPECIFIED_PROXY_ONLY_AUTHORITY`

schema: `source-proxy.gate-2j-9-result-mapping/v1`

The only production terminal classes remain Proxy-owned:

- `COMPLETED_VERIFIED`
- `ESCALATION_CONTEXT_PACK_READY`
- `BLOCKED_OR_DEGRADED_TRUTHFULLY`

JCode cannot emit any authoritative terminal class. JCode's claimed outcome is evidence only.

## 1. Mapping table

| Dispatcher outcome | Default terminal class | Notes |
|---|---|---|
| Clean executor exit, valid independent diff, all independent checks pass | `COMPLETED_VERIFIED` (only after review+verify+anti-cheat+evidence-complete) | requires all four pass |
| Clean executor exit, no changes | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | no work produced |
| Executor-declared success but evidence incomplete / checks fail | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | claim not trusted |
| Executor-declared failure | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | honest failure |
| Malformed output / missing required events | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=mangled_output |
| Incomplete evidence | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=evidence_incomplete |
| Timeout | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=timeout |
| Cancellation | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=cancelled |
| Model unavailable (bridge cannot reach/prove model) | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=model_unavailable |
| Model identity mismatch | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=model_mismatch (anti-cheat) |
| Provider mismatch / unauthorized endpoint | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=provider_mismatch |
| Unauthorized tool attempt | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=unauthorized_tool |
| Unauthorized filesystem attempt | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=unauthorized_fs |
| Protected-path attempt | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=protected_path |
| Network violation (forbidden flow reached) | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=network_violation |
| Budget exhaustion | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=budget_exhausted |
| Failed tests (Proxy verifier) | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=tests_failed |
| Reviewer rejection | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=reviewer_reject |
| Verifier rejection | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=verifier_reject |
| Anti-cheat rejection | `BLOCKED_OR_DEGRADED_TRUTHFULLY` | reason=anti_cheat_reject |
| Infrastructure failure (bridge/worktree/evidence-dir unavailable) | `ESCALATION_CONTEXT_PACK_READY` | may need operator triage |
| Escalation/ambiguity task resolved by executor within scope | `ESCALATION_CONTEXT_PACK_READY` | per manifest category |

## 2. `COMPLETED_VERIFIED` gate

`COMPLETED_VERIFIED` may occur only after ALL of the following pass:

1. Clean executor exit with a valid independent diff.
2. Evidence completeness (all required events present, NDJSON chain intact, ledgers hashed).
3. Proxy reviewer acceptance.
4. Proxy verifier acceptance (tests pass for the task).
5. Proxy anti-cheat acceptance (model/provider identity proven, no forbidden flow, no
   protected-path violation, no benchmark-solution leakage).

Any failure above forces `BLOCKED_OR_DEGRADED_TRUTHFULLY` or `ESCALATION_CONTEXT_PACK_READY`.

## 3. Determinism

The map is a pure function of (dispatcher outcome, evidence completeness, independent-check
results). It contains no path that lets JCode's claim produce `COMPLETED_VERIFIED`. The mapper
is implemented in `source_proxy/jcode/terminal_mapping.py` and is itself unit-tested with the
controlled failure matrix (Gate 2-J.9J).
