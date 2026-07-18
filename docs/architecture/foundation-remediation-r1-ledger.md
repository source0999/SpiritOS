# SpiritOS Foundation Remediation R1 Ledger

Schema: `spiritos-foundation-remediation-r1-ledger/v1`

Remediation: `spiritos-foundation-remediation-r1`

## Authoritative checkpoint

- Worktree: `/home/source/SpiritOS-foundation-remediation-r1-20260717`
- Branch: `codex/spiritos-foundation-remediation-r1-20260717`
- Base: `2b8ead66578d7f7053c01cb987e011b763c1c03d`
- Recorded source head: `297151eb814512bfa4d37a6306e20a9dfe2af041`
- Current phase/gate: Phase 4 / `r1_11_clean_proving_task`
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
| R1.1 portable authority | complete | registered top-level worktree identity, root namespace isolation, and symlink/subdirectory/stale-root rejection are covered in Python and TypeScript |
| R1.2 Cartographer authority | complete | legacy client authority routes are absent; persisted proposal review uses server-owned identity, exact bindings, consume-before-write, independent checks, and rollback |
| R1.3 SpiritFlix authority | complete | production writers use authenticated, complete mutation bindings and a verify/finalize-or-compensate transaction |
| R1.4 Design security | complete | existing writeback only; exact artifact binding, production issuer/consumer, independent disk verification, late finalization, and rollback |
| R1.5 coding lifecycle | complete | apply is nonterminal; five independently invoked participants bind one immutable artifact and successful authority finalization is hard-gated on proof recomputation |
| R1.6 target adapters 1-10 | complete | every exact LumaCart prompt has target-owned specification, command policy, identity, and executable adapter behavior |
| R1.7 production orchestrator | complete | API task creation owns one durable orchestrator and the exact target proposal path consumes persisted context/runtime records through that owner |
| R1.8 runtime contracts/transfer | complete | live output, acknowledgement, and consumption boundaries are enforced; Cartographer selection remains pending until real downstream invocation and finalization |
| R1.9 backend state/recovery | complete | Source Proxy is decision authority, Next is read-only projection, and fallback is recorded within one accountable run lineage |
| R1.10 immutable evidence | complete | strict source-bound schemas, generator, validator, secret scan, and adversarial regression suites are implemented; the terminal artifacts deliberately wait for R1.11 proof |
| R1.11 clean proving task | pending | real HTTP/model/approval/apply/participants/recovery/undo/rerun |
| R1.12 closeout | pending | full matrix, terminal receipt/manifest, tag, bundle, sidecar, restoration instructions |

## Scope ledger

```text
USER_OBJECTIVE: Foundation Remediation R1
PROJECT_SCOPE: Source Proxy, SpiritFlix, Cartographer, Design security preservation, shared authority/evidence
ACTIVE_WORKTREE: /home/source/SpiritOS-foundation-remediation-r1-20260717
ACTIVE_BRANCH: codex/spiritos-foundation-remediation-r1-20260717
ALLOWED_PATHS: .gitignore, _blueprints/proposals/pending_review/, source_proxy/, src/app/api/spiritflix/, src/app/v1/actions/, src/app/v1/cartographer/, src/app/v1/coding/, src/components/coding/, src/lib/coding/, tests/ui-agent-trials/fixtures/dummy-product-site/, packages/contracts/, scripts/, docs/architecture/
FORBIDDEN_DETOURS: Campaign 3 implementation, Campaign 4, Scout/Mac/Obsidian/retained agents, Designer expansion, push
CURRENT_PHASE: R1.11
COMPLETED_GATES: R1.0, R1.1, R1.2, R1.3, R1.4, R1.5, R1.6, R1.7, R1.8, R1.9, R1.10
NEXT_GATE: independently reviewed clean production proving task
SERVICES: no R1 service active; failed proving startup scopes were fully revoked
TESTS_REQUIRED: registered R1 profiles
OPEN_BLOCKERS: none; expected validator failures are repair gates
LAST_VERIFIED_HEAD: 297151eb814512bfa4d37a6306e20a9dfe2af041
```

## Authority repair checkpoint

- Portable authority rejects relative, unregistered, symlinked, subdirectory,
  detached, and stale-source identities while isolating state by canonical Git
  worktree identity.
- Cartographer proposal review no longer accepts caller-owned actor or snapshot
  authority and no legacy approval-token validation/consumption route is registered.
- SpiritFlix administrative mutations and Design writeback both consume complete,
  server-derived bindings before mutation, independently verify the written result,
  and roll back or compensate before returning a non-success result.
- Focused observations: portable/adapter/authority matrix `76 passed`; full
  Cartographer API `263 passed`; Design security `50 passed`; SpiritFlix `419 passed`;
  TypeScript typecheck passed. These are checkpoint observations only until the
  immutable terminal manifest binds commands, artifacts, and the tested source.

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

## Production coding authority checkpoint

- One canonical `CodingOrchestrator` is created and persisted by the production task
  API. Exact LumaCart proposal generation enters it through context-broker, planner,
  model routing, and target-adapter runtime boundaries; a direct adapter bypass is
  rejected by production-path regression and static call-graph checks.
- Apply is explicitly nonterminal. Executor, reviewer, verifier, anti-cheat, and
  evidence recorder create separate invocation/output/acknowledgement records bound
  to one artifact. Finalization independently recomputes the proof and fails closed
  when any required output, consumption, participant, model, recovery, or
  Cartographer binding is missing.
- Source Proxy owns decision-bearing run state. The Next coding-runs endpoints are
  bounded read-only projections and cannot create, mutate, or finalize a run.
- The canonical model router records exact primary/fallback attempts and a recovery
  record inside one lineage. A non-model result cannot satisfy terminal proof.
- Focused observations: the combined production/orchestrator/proof/participant/
  recovery/target/runtime matrix passed `120` tests; the full long-running route
  suite passed `71`; the coding regression pack passed `133`; the real decision
  route/orchestrator binding test passed; the strengthened authority validator
  reports valid. These remain nonterminal checkpoint observations until a clean
  source commit is exercised by R1.11 and immutably anchored.

## Durable approval and participant-ownership checkpoint

- Coding finalization now persists an exact authority-finalization intent before the
  authority call. A lost response, receipt-persistence failure, or local task-commit
  failure resumes that same intent without rerunning participants or consuming a new
  approval generation. Exact already-consumed finalization is idempotent; any changed
  result or evidence is rejected.
- Production reviewer, verifier, anti-cheat, and evidence-recorder work runs in
  distinct subprocesses. Each producer emits a self-hashed v2 output after the child
  process starts; the downstream parent consumer validates that output and then emits
  its own separately hashed acknowledgement. The executor likewise owns its output,
  and the orchestrator creates its acknowledgement only after validation.
- Approval evidence contains the exact participant-owned acknowledgement objects,
  not copied identity fields or caller-authored `performed` labels. Design and
  SpiritFlix preserve their existing scope while enforcing the same output-before-
  acknowledgement ordering and distinct producer/consumer identities.
- Source Proxy remains the only decision-bearing task owner. A Next projection can
  display terminal success only when a canonical-hashed production proof binds the
  same task, run, artifact, approval generation, execution evidence, and terminal
  result. Missing or altered proof leaves the projection nonterminal.
- Focused observations: approval/participant/proof suites passed `42`; the broader
  orchestrator, Cartographer, long-running, and decision-route suites passed `92`;
  the relevant Next/Design/SpiritFlix matrix passed `55`; TypeScript typecheck and a
  full production build passed. These are implementation observations only until the
  exact committed source is rerun through every registered profile.

## Immutable evidence implementation checkpoint

- Added strict JSON schemas for profile receipts, terminal receipts, and immutable
  manifests, plus content-addressed generation, validation, protected-head reports,
  high-confidence secret scanning, and adversarial tests.
- Evidence construction requires the exact current source commit and rejects missing
  build/plugin/prompt/context/approval/participant/authority bindings. The terminal
  validator also requires a tagged closeout commit, verified bundle and sidecar, and
  tracked restoration instructions.
- No terminal receipt or success field has been created at this checkpoint. Those
  artifacts depend on the real clean proving run and full source-commit test matrix.

## Clean-proving harness checkpoint

- The inner proving client requires two distinct production HTTP runs at one exact
  source commit: a controlled primary-model failure with recorded fallback and a
  clean rerun after authenticated undo/reset. It validates real Cartographer transfer,
  runtime output consumption, participant-owned acknowledgements, approval generation,
  immutable artifact/diff/result hashes, and a 27-exchange HMAC-bound transcript.
- The outer launcher accepts only a clean registered non-detached linked worktree,
  prehashes the Python executable/environment and Node executable/dependency tree,
  launches Source Proxy, Next, and the loopback TLS proxy in one isolated user scope,
  and revalidates the complete worktree and measured runtimes after teardown.
- Process containment has a deliberately narrow claim ceiling: revocation of trusted,
  prehashed descendants that remain in the user scope. Resistance to hostile same-UID
  cgroup migration is explicitly not claimed. Terminal evidence additionally requires
  three empty descendant scans and recursively unpopulated cgroups.
- The terminal generator now validates and cross-binds standalone inner and outer
  receipt blobs and requires both in the immutable manifest/tag. Regression status:
  proving `16/16`, lifecycle `23/23`, evidence `13/13`, completion `12/12`, and
  profile-registry `5/5`. No successful real proving receipt exists; R1.11 remains
  pending.
- The first real lifecycle startup falsified an assumption that the pinned mkcert
  leaf could be used as a Python CA root. HTTPS health now enables OpenSSL partial-
  chain validation for that exact pinned leaf while preserving signature, validity,
  and hostname checks; the focused regression proves the flag is set. Failed startup
  attempts published no receipt and fully revoked their scopes.
- The next clean lifecycle attempt passed identity, runtime, build, service, and TLS
  gates but the inner client rejected Cartographer's canonical 16-hex proposal
  fingerprint as though it were a 64-hex evidence digest. No proving or lifecycle
  receipt was published, and all service scopes, ports, temporary authority state,
  and generated fixture files were revoked. The harness now validates the established
  16-hex proposal identifier separately, computes the authority's full SHA-256
  selection-content binding, and requires the consumed transfer provenance to match
  that exact observed proposal. A same-format fingerprint mutation is rejected by
  the approval authority. Regression status after repair: proving `16/16`, lifecycle
  `23/23`, focused fingerprint/selection authority `3/3`, static authority valid,
  and `git diff --check` clean.
- At source `297151eb814512bfa4d37a6306e20a9dfe2af041`, the production client advanced
  through Cartographer selection and controlled model routing before rejecting a
  read-only diff preview with `diff_preview_blocking_check_failed`. The preview
  contract intentionally marks a TypeScript syntax check `skipped` when the bounded
  LumaCart change contains JavaScript but no TS/TSX; its canonical pass predicate
  accepts blocking checks in either `passed` or `skipped` state. The proving client
  had incorrectly narrowed that predicate to `passed` only. It now mirrors the live
  contract while continuing to reject blocking `failed` and `timeout` results.
  Failed attempts published no receipt, left no fixture files, and fully revoked all
  scoped services and temporary authority state. Regression status: proving `16/16`,
  lifecycle `23/23`, focused diff-preview matrix `45/45`, and the exact LumaCart
  blocking/skipped production shape is asserted directly.
- A diagnostic replay also rejected the stale Node executable anchor `55e9b91c…`
  before service launch. Direct byte hashing, inode/stat inspection, Node version,
  and the owning `nodejs 20.20.2-1nodesource1` package establish the current
  `/usr/bin/node` SHA-256 as
  `6295488653f0d93b0a157841746fef7e72cc4328cfb60c4bbe0ca2668a836ffd`.
- At source `5466242f69763a33a8ae14e308c8202e2e1ea898`, the production lifecycle
  reached final post-apply verification, where the model-authored fixture
  `package.json` contained only `{}`. The post-apply verifier correctly rejected
  that artifact and left the task nonterminal, so neither an inner proving receipt
  nor an outer lifecycle receipt was published. Service scopes, ports, operator
  authority, and temporary approval authority were revoked, but lifecycle teardown
  then detected the ignored generated fixture still present and failed closed with
  `lifecycle_teardown_failed_after_proving_failure`.
- That attempt exposed two production-boundary defects rather than a proving
  exception: Prompt 1 pre-apply validation had not enforced the post-apply package
  identity rule, and teardown did not own the exact ignored proving-fixture path.
  Prompt 1 now uses one shared rule before and after apply: fixture `package.json`
  must be a JSON object with a non-empty string `name`. The target contract, initial
  model prompt, and repair prompt declare the same invariant. Lifecycle teardown
  now refuses tracked content or symlinked ancestors, removes only the exact proving
  fixture without following symlinks, revalidates the complete linked-worktree
  identity, and exposes mandatory receipt fields for that cleanup. Focused
  observations after repair: Prompt 1 and post-apply boundary matrix `5/5`, target
  contract matrix `11/11`, lifecycle `25/25`, and evidence `13/13`. No terminal
  success is claimed. Broader changed-surface observations also pass: coding
  regression pack `135/135`, long-running task suite `72/72`, and target-adapter
  suite `38/38`. A new clean source checkpoint and full two-run production proving
  lifecycle remain required.
- The first lifecycle attempt at source
  `46951d7220b8a4c0eddde7fcb1ea33c036df7e46` stopped at the clean Next build with
  `lifecycle_next_build_failed`; it published no receipt and restored a clean proof
  worktree. An immediate exact-command diagnostic build then completed compilation,
  TypeScript, 136 static pages, and build traces successfully, so the isolated
  failure is recorded as transient rather than rewritten as a source pass.
- A second clean lifecycle attempt passed both dependency measurements, authority
  preflight, the production build, and all three service startups. The inner client
  later failed and teardown again withheld both receipts. The proof worktree showed
  no tracked changes or generated fixture residue, but did contain newly generated
  ignored `source_proxy/**/__pycache__/*.pyc` files. Timestamps and module names bind
  those files to the independent participant-worker launch. That worker deliberately
  constructed a minimal environment but omitted the outer lifecycle's
  `PYTHONDONTWRITEBYTECODE=1` and invoked Python without `-B`, making the clean
  teardown invariant unsatisfiable once participants ran.
- Participant subprocesses now preserve the no-bytecode runtime boundary in both
  their command and minimal environment. A regression snapshots every existing
  `source_proxy` bytecode file before independent reviewer, verifier, anti-cheat, and
  evidence-recorder workers run and requires an identical snapshot afterward. The
  exact inner-client rejection from the failed attempt was not promoted into a
  claim because its transient log was removed during fail-closed teardown; the next
  proving attempt must be monitored directly and must still satisfy every receipt
  invariant. Regression observations after repair: participant suite `18/18`,
  orchestrator/proof/approval matrix `45/45`, lifecycle `25/25`, proving `16/16`,
  static authority valid, and `git diff --check` clean.

## Broad-suite diagnostic attribution

- A non-acceptance diagnostic run of all `source_proxy/tests` reached `1908 passed`
  and `12 failed`. Three failures touched R1-changed behavior: the legacy
  Cartographer apply test expected a superseded mismatch reason after the whole
  mutation surface became forbidden, and two observability fixtures still declared
  orchestrator schema v1. The safety expectation now preserves the stronger
  fail-closed rule (`15/15` focused pass), and observability now accepts only v2 while
  explicitly rejecting legacy v1 (`4/4` focused plus `89/89` orchestrator/route pass).
- The remaining nine diagnostics reproduce in areas untouched from the Campaign 2
  base: a missing/stale future Cartographer consultation contract, environment-bound
  timing fixtures, deterministic Markdown parsing, a headless-browser timeout, and a
  stale research-source mock. They are recorded as inherited repository risks, not
  accepted R1 evidence and not silently converted to passes. The mandatory R1
  profiles exercise the changed production authority and proving surfaces directly.
- A repository-wide default Vitest diagnostic reached `2354 passed` and `34 failed`
  across 765 hierarchical suites. The failures are outside the registered R1 matrix:
  Playwright/e2e and shebang-bearing scripts miscollected by Vitest, dummy fixture
  files with no suite, inherited dashboard/media/Scout assertions, legacy coding UI
  tests in untouched surfaces, and three multiline static-source assertions made
  CRLF-sensitive by this host checkout. The changed Design/SpiritFlix/Next authority
  and projection profiles pass, as do typecheck and the production build. The broad
  aggregate remains a diagnostic risk record and is not presented as terminal proof.

## Closeout rule

Markdown is never parsed to infer success. The completion evaluator must execute the
four strict validators and reconcile machine state, tracked receipt, immutable
manifest, tag, bundle, SHA sidecar, and protected heads. A normal failing gate remains
work to repair; it is not a stop condition.
