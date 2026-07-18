# SpiritOS Foundation Remediation R1 Ledger

Schema: `spiritos-foundation-remediation-r1-ledger/v1`

Remediation: `spiritos-foundation-remediation-r1`

## Authoritative checkpoint

- Worktree: `/home/source/SpiritOS-foundation-remediation-r1-20260717`
- Branch: `codex/spiritos-foundation-remediation-r1-20260717`
- Base: `2b8ead66578d7f7053c01cb987e011b763c1c03d`
- Recorded source head: `32905e349d62a9bde101e8e6168567404faad679`
- Current phase/gate: Phase 1 / `r1_1_portable_authority`
- GO eligibility: `false`
- Terminal verdict: not available
- Campaign 3 started: `false`; Campaign 4 started: `false`; push: `false`

## Verified repository baseline

On Dell host `source-server`, `git fsck --full --strict --no-progress --no-dangling`
completed successfully. The six protected commit identities match the Goal. The new
linked worktree was created directly from `2b8ead665…`; no historical branch or
worktree was moved.

The Campaign 2 branch had already advanced to
`39de31bb73cb4a910281705259b35a6d42a0726c` before R1 began. R1 protects that exact
observed ref tip from further movement while separately protecting the engineering
terminal object `2b8ead66578d7f7053c01cb987e011b763c1c03d` and requiring it to remain in
the branch ancestry. The other five observed ref tips equal their listed protected
heads.

## Independently confirmed defects

- `source_proxy/cartographer/proposal_reviews.py` accepts caller actor/snapshot data,
  creates directories, writes JSON, and unlinks the prior file. The Source Proxy and
  Next routes provide no canonical approval or server-owned actor.
- Python and TypeScript authority adapters hard-code Campaign 1/2 worktree roots.
- `source_proxy/tasks/long_running.py` finalizes coding approval as succeeded directly
  after apply, then leaves the task in `applied_needs_verification`.
- The same module copies approval/plugin identity into reviewer, verifier, and evidence
  acknowledgement dictionaries instead of recording independent invocations.
- `source_proxy/coding/orchestrator.py` is not imported by the production long-running
  API; the live execute route enters approval gate then the executor directly.
- The lane catalog validates static metadata but the live chain does not enforce
  producer/consumer version, output, or consumption boundaries.
- `source_proxy/target_plugins/adapter.py` recognizes prompts 1-10 but defines commands
  and task specifications only for prompts 1-3.
- The inherited Campaign 2 authority validator reports valid despite the production
  bypass. Its completion regression suite fails because checked-in state is terminal
  while the test asserts it must be nonterminal.
- Historical terminal receipts are not source/build-bound immutable Git evidence.

These are defect confirmations, not accepted completion evidence.

## Pre-remediation validator baseline

| Command | Result | Meaning |
| --- | --- | --- |
| `validate-campaign-1-authority.py` | fail | inherited branch/root mismatch and stale assumptions |
| `validate-campaign-1-continuity.py` | fail | branch/head mismatch |
| `validate-campaign-1-evidence.py` | fail | receipt absent |
| `validate-campaign-1-test-profiles.py` | pass | registry shape only |
| `validate-campaign-2-authority.py` | pass | false reassurance; no production importer check |
| `validate-campaign-2-continuity.py` | fail | branch mismatch |
| `validate-campaign-2-test-profiles.py` | pass | trusts self-declared accepted receipts |
| `test-campaign1-autoloop-completion.py` | 7 pass | does not prove current production graph |
| `test-campaign2-autoloop-completion.py` | 6 pass, 1 fail | checked-in terminal claim contradicts stale regression |

## Gate log

| Gate | Status | Evidence / next truth |
| --- | --- | --- |
| R1.0 control plane | complete | seven control documents, four validators, strict evaluator, and 6/6 fail-closed regression tests are present; authority/evidence remain deliberately nonterminal |
| R1.1 portable authority | in progress | remove configured-root hard-coding and validate registered roots |
| R1.2 Cartographer authority | pending | replace direct writer path |
| R1.3 SpiritFlix authority | pending | complete bindings and transactional helper |
| R1.4 Design security | pending | preservation-only authority correction |
| R1.5 coding lifecycle | pending | late finalization and independent consumers |
| R1.6 target adapters 1-10 | pending | executable target-owned behavior |
| R1.7 production orchestrator | pending | live importer and persisted owner |
| R1.8 runtime contracts/transfer | partial | immutable version/schema/output/acknowledgement/consumption boundary is tested; live orchestrator integration and Cartographer lineage remain pending |
| R1.9 backend state/recovery | pending | Source Proxy truth and one-run recovery |
| R1.10 immutable evidence | pending | implement source-bound schema/generator and profile evidence model; terminal receipt waits for proof |
| R1.11 clean proving task | pending | real HTTP/model/approval/apply/participants/recovery/undo/rerun |
| R1.12 closeout | pending | full matrix, terminal receipt/manifest, tag, bundle, sidecar, restoration instructions |

## Scope ledger

```text
USER_OBJECTIVE: Foundation Remediation R1
PROJECT_SCOPE: Source Proxy, SpiritFlix, Cartographer, Design security preservation, shared authority/evidence
ACTIVE_WORKTREE: /home/source/SpiritOS-foundation-remediation-r1-20260717
ACTIVE_BRANCH: codex/spiritos-foundation-remediation-r1-20260717
ALLOWED_PATHS: source_proxy/, src/app/api/spiritflix/, src/app/v1/cartographer/, src/lib/coding/, packages/contracts/, scripts/, docs/architecture/
FORBIDDEN_DETOURS: Campaign 3 implementation, Campaign 4, Scout/Mac/Obsidian/retained agents, Designer expansion, push
CURRENT_PHASE: R1.1
COMPLETED_GATES: R1.0
NEXT_GATE: validate and checkpoint portable registered-root authority
SERVICES: no R1 service started
TESTS_REQUIRED: registered R1 profiles
OPEN_BLOCKERS: none; expected validator failures are repair gates
LAST_VERIFIED_HEAD: 32905e349d62a9bde101e8e6168567404faad679
```

## R1.0 checkpoint evidence

- `python3 scripts/test-foundation-remediation-r1-completion.py`: 6/6 pass.
- `python3 scripts/validate-foundation-remediation-r1-test-profiles.py`: pass at
  registry-coherence claim ceiling.
- The continuity validator is intentionally run after the atomic checkpoint because
  it rejects untracked, staged, or dirty control-plane files.
- The authority validator still rejects the inherited live call graph. The evidence
  validator still rejects nonterminal state and missing terminal evidence. These are
  required fail-closed results, not waived gates.

## Runtime-contract boundary checkpoint

- Added an immutable runtime lane boundary that compiles the canonical embedded
  schemas and rejects missing/incompatible versions, malformed output, same-invocation
  acknowledgements, unknown output, mismatched acknowledgement, replayed consumption,
  and required-but-unconsumed output.
- `25 passed` across the new boundary suite plus canonical contracts, orchestrator,
  Cartographer handoff, and observability regression tests.
- Claim ceiling: library boundary only. Production integration remains an explicit
  R1.8 partial gate and cannot satisfy the authority validator yet.

## Closeout rule

Markdown is never parsed to infer success. The completion evaluator must execute the
four strict validators and reconcile machine state, tracked receipt, immutable
manifest, tag, bundle, SHA sidecar, and protected heads. A normal failing gate remains
work to repair; it is not a stop condition.
