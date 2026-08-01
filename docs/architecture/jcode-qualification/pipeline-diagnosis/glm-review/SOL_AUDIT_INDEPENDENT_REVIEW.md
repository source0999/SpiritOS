# SOL_AUDIT_INDEPENDENT_REVIEW.md

Independent GLM review of the Sol Ultra Campaign 2-J human-to-coder pipeline
diagnosis. Read-only evidence review + amendment authoring. No Gate 2-J.9T
implementation, no diagnostic runs, no campaign advancement.

---

## Verdict

`SOL_AUDIT_ACCEPTED_WITH_CORRECTIONS__PACKET_AMENDMENT_READY`

The Sol Ultra diagnosis is accepted. Its causal evidence chain is sound, its
counterfactuals are valid, and its multi-factor conclusion is supported. One
correction is required (canonical amendment/gate naming per operator spec, with
the agent-loop dimension made explicit in the title); all other Sol thresholds
are retained with explicit justification.

---

## 1. Audit repository and branch

- Canonical campaign: `/home/source/SpiritOS-source-proxy-jcode-qualification-20260726`,
  branch `codex/source-proxy-jcode-qualification-20260726`.
- Isolated audit: `/home/source/SpiritOS-source-proxy-jcode-pipeline-diagnosis-20260731`,
  branch `codex/source-proxy-jcode-pipeline-diagnosis-20260731`.
- Verified: worktree resolves; branch matches; final HEAD
  `115f4f3343f1aede103e642d6853f2677d2d4a48` == upstream, 0/0 ahead-behind,
  clean working tree.

## 2. Starting and final HEAD

- Starting HEAD `07151b44cb886ac4d8c3668e947e81825d01bd50` — exists
  (`git cat-file -t` -> commit).
- Final HEAD `115f4f3343f1aede103e642d6853f2677d2d4a48` — verified live.
- 12 commits in range, led by authorization commit `c42d62f1`.

## 3. Sol authorization verification

- Operator prompt SHA-256 `f45bde0f3fd1c4c225f4a896577a0778408d449ebee41b3dc4f57c0171ab7afb`
  — **independently re-hashed** with `sha256sum` on
  `OPERATOR_AUTHORIZATION_PROMPT.txt`: MATCHES exactly.
- Authorization commit `c42d62f189542e69112e600c5e0bdef05e2705ac` — exists and
  contains the freeze/authorization receipts.
- Budget: 36 max real requests; 24 used; 12 remaining.

## 4. Number of runs independently verified

- 24 sealed run directories under `pipeline-diagnosis/runs/`.
- Executable evidence verifier (`verify-evidence`) **reproduced at HEAD**:
  `passed: true`, 24 runs, 24 model requests, 24 request finishes, 6 timeouts,
  max 1 turn/run, 1 accepted capture gap (`s1-r-e-7b`), 0 frozen benchmark runs.
- I directly inspected raw evidence for the load-bearing lanes (A/B/C/D/E,
  both models) and the s3 correction cells.

## 5. Models and exact digests

| Model | Reported digest | Live `ollama list` | Match |
| --- | --- | --- | --- |
| `qwen2.5-coder:7b` | `dae161e2...f4364` | `dae161e27b0e...f4364` | YES |
| `qwen2.5-coder:14b` | `9ec8897f...16849` | `9ec8897f747e...16849` | YES |

JCode binary `/home/source/.codex-audits/jcode-dell-remediation-20260727/approved-binary/jcode`:
reported `2c59d30e...b3f8ef6`, `v0.58.51-dev (2444e7b6)` — **independently
re-hashed and version-checked live**: MATCHES exactly.

## 6-12. Causal-claim verification (key claims)

| # | Claim | Evidence inspected | GLM status |
| --- | --- | --- | --- |
| 6 | Direct capability proven | Lane A eval receipts: R 7B PASS, R 14B PASS, W 7B PASS | VERIFIED |
| 7 | Textual-tool attempts proven | `s1-r-b-7b`: `message.tool_calls: None`, content is `{"name":"read_file","arguments":{"path":"ledger.py"}}` text; `tool_call_count: 0` | VERIFIED |
| 8 | Native tool incompatibility proven | Same run: request carried `tools` (count 1) at `/api/chat`; no native call returned | VERIFIED |
| 9 | Baseline loop reinjection defect proven | `s1-r-c-7b`: parser accepted 1 `ReadFile` (fenced_json), executor read file successfully, but `final_text: ""`, `grounded_answer_fail`; loop exited on empty `recommended_checks` | VERIFIED |
| 10 | JCode-specific incompatibility proven | Legacy D/F: `tools_reached_provider_unchanged: false`; corrected s3: `true` 4/4, but 0/4 end-to-end (text calls not parsed); 14B W also blocked by absent focused-test tool | VERIFIED |
| 11 | Packet dilution proven | Packet noise receipts: R full 12,579 B @ 0.019, task at byte 5,807; W full 14,016 B @ 0.0164, task at byte 6,663; minimal R/W ~0.455 @ byte 26 | VERIFIED |
| 12 | Evaluator mismatch proven | **Ran 14B's `re.sub` code against the actual `focused_check.py`: both assertions PASS.** Evaluator rejected it as `inline_patch_capability_fail` on AST (import/assignment). | VERIFIED |

## 13. Sol claims accepted unchanged

The full causal verdict, root-cause tree priorities 1-10, the ruled-out list
(raw-model-capability-limit, grounding-limit, path-mismatch, session/default
contamination, output-budget-insufficient, model substitution), the diagnostic
matrix, the packet-quality measurements, the bridge/tool-protocol audits, the
global-correction counterfactual (4/4 structural, 0/4 end-to-end), and all
retained/blocked gate assignments.

## 14. Sol claims accepted with correction

- **Amendment/gate naming.** Sol used
  `CAMPAIGN_2J_GATE_9T_PACKET_TOOL_COMPATIBILITY_V1`. Corrected to the
  operator-specified canonical
  `CAMPAIGN_2J_PACKET_TOOL_LOOP_COMPATIBILITY_AMENDMENT_V1` and gate
  `Gate 2-J.9T - Model-Ready Packet, Tool Protocol, and Agent-Loop
  Qualification`. The agent-loop dimension was in Sol's body but not its title;
  the canonical title makes it explicit.
- **9I attribution wording.** Sol already refined this correctly; this review
  ratifies the refinement (9I model-quality attribution is `EVIDENCE_INCOMPLETE`,
  not incapability) and carries it into the canonical amendment.

## 15. Sol claims rejected

None. Every load-bearing claim is supported by raw evidence that I
independently reproduced or re-inspected.

---

## Run-verification table (24 runs)

Legend: VERIFIED (V), EVIDENCE_INCOMPLETE (E-I).

| Run ID | Task | Lane | Model | Expected | Observed | Evidence | Sol class | GLM class | Agree | Conf. | Correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s1-r-a-7b | R | A | 7B | ground+answer | PASS 58.9s | complete | direct_pass | direct_pass | yes | 1.00 | none |
| s1-r-a-14b | R | A | 14B | ground+answer | PASS 125.8s | complete | direct_pass | direct_pass | yes | 1.00 | none |
| s1-r-b-7b | R | B | 7B | native tool read | text JSON, 0 native calls | complete (re-inspected) | dialect_incompat | dialect_incompat | yes | 1.00 | none |
| s1-r-b-14b | R | B | 14B | native tool read | text JSON, 0 native calls | complete | dialect_incompat | dialect_incompat | yes | 0.99 | none |
| s1-r-c-7b | R | C | 7B | read+reinject+answer | read executed, no reinject, no answer | complete (re-inspected) | loop_reinject_fail | loop_reinject_fail | yes | 1.00 | none |
| s1-r-c-14b | R | C | 14B | read+reinject+answer | same | complete | loop_reinject_fail | loop_reinject_fail | yes | 1.00 | none |
| s1-r-d-7b | R | D | 7B | JCode tool read | bridge drops tools, generic ack | complete | bridge_loss | bridge_loss | yes | 1.00 | none |
| s1-r-d-14b | R | D | 14B | JCode tool read | bridge drops tools, timeout | complete | bridge_loss+timeout | bridge_loss+timeout | yes | 1.00 | none |
| s1-r-e-7b | R | E | 7B | full-packet ground | timeout, request body gap | E-I | timeout+gap | timeout+gap | yes | 0.90 | none (gap honestly declared) |
| s1-r-e-14b | R | E | 14B | full-packet ground | timeout, 15,490-char prompt | complete | packet_pressure | packet_pressure | yes | 0.98 | none |
| s1-r-f-7b | R | F | 7B | JCode full read | bridge loss turn 1 | complete | bridge_loss | bridge_loss | yes | 1.00 | none |
| s1-r-f-14b | R | F | 14B | JCode full read | bridge loss, timeout | complete | bridge_loss+timeout | bridge_loss+timeout | yes | 1.00 | none |
| s2-w-a-7b | W | A | 7B | correct write | PASS 53.6s | complete | direct_pass | direct_pass | yes | 1.00 | none |
| s2-w-a-14b | W | A | 14B | correct write | semantically correct, evaluator reject | complete (re-tested) | eval_mismatch | eval_mismatch | yes | 1.00 | none |
| s2-w-b-7b | W | B | 7B | native read+edit | text JSON reads | complete | dialect_incompat | dialect_incompat | yes | 1.00 | none |
| s2-w-b-14b | W | B | 14B | native read+edit | text JSON reads | complete | dialect_incompat | dialect_incompat | yes | 0.99 | none |
| s2-w-d-7b | W | D | 7B | JCode edit | bridge loss, no mutation | complete | bridge_loss | bridge_loss | yes | 1.00 | none |
| s2-w-d-14b | W | D | 14B | JCode edit | bridge loss, timeout | complete | bridge_loss+timeout | bridge_loss+timeout | yes | 1.00 | none |
| s2-w-f-7b | W | F | 7B | JCode full edit | bridge loss, no mutation | complete | bridge_loss | bridge_loss | yes | 1.00 | none |
| s2-w-f-14b | W | F | 14B | JCode full edit | bridge loss, timeout | complete | bridge_loss+timeout | bridge_loss+timeout | yes | 1.00 | none |
| s3-r-dtp-7b | R | D-corr | 7B | corrected bridge read | roles/tools preserved; promises read, 0 events | complete | counterfact_pass/task_fail | counterfact_pass/task_fail | yes | 1.00 | none |
| s3-r-dtp-14b | R | D-corr | 14B | corrected bridge read | preserved; fenced text read, 0 events | complete | counterfact_pass/task_fail | counterfact_pass/task_fail | yes | 1.00 | none |
| s3-w-dtp-7b | W | D-corr | 7B | corrected bridge edit | preserved; fenced text read, 0 events; no test tool | complete | counterfact_pass/task_fail | counterfact_pass/task_fail | yes | 1.00 | none |
| s3-w-dtp-14b | W | D-corr | 14B | corrected bridge edit | preserved; fenced text read, 0 events; no test tool | complete | counterfact_pass/task_fail | counterfact_pass/task_fail | yes | 1.00 | none |

Summary: 23 VERIFIED, 1 EVIDENCE_INCOMPLETE (`s1-r-e-7b`, honestly declared, no
reconstruction). Zero contradictions.

---

## Contract-break matrix (earliest break per path)

| Contract edge | Expected input | Actual input | Expected output | Actual output | Loss/distortion | Evidence | Severity | Owning component | Proposed correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Acceptance-criteria creation | criteria in intake | `literal_requirements: []` | criteria in packet | absent | criteria never created | CONTEXT_PACKET_QUALITY_AUDIT | high | task intake | packet schema requires criteria (9T-A) |
| Context truncation/order | critical bytes preserved | 6,000-char silent slice | complete critical source | buried/possibly truncated | task buried @ ~5,800 B; 1.6-1.9% relevant | packet noise receipts | high | context builder | packet gate (9T-A) |
| Model-ready packet | concise coder contract | human paste-back packet | concise task-first body | governance-noise body | 12 governance markers | packet noise receipts | high | packet builder | packet gate (9T-A) |
| Bridge (legacy) | roles+tools carried | flattened `/api/generate` prompt | provider-visible tools | tools dropped | roles/tools/`tool_choice` lost | BRIDGE audit; D/F receipts | critical | bridge/JCode adapter | chat-preserving bridge (9T-B) |
| Tool parse | native call OR accepted text | native-only parser | parsed tool call | 0 calls | text dialect ignored | B receipts; s3 receipts | critical | model profile/adapter | normalizer (9T-C) |
| Observation reinjection | observation -> next turn | empty checks -> completed | loop continues | loop exits | read result never returned | C receipts | critical | agent loop | loop contract (9T-D) |
| Focused-test capability | test tool available | no command tool | run focused test | impossible | Task W uncompletable | JCODE_PROMPT audit | high | JCode tool policy | focused-test tool (9T-E) |
| JCode system prompt | task-aligned instructions | 2,004-char generic prompt | sealed-task behavior | self-modify/commit conflict | instruction conflict | JCODE_PROMPT audit | high | JCode project prompt | JCode profile (9T-H) |
| Evaluator | behavioral equivalence | AST allowlist | accept correct code | reject import/assignment | semantic code rejected | s2-w-a-14b | high | evaluator | evaluator alignment (9T-E) |
| Evidence completeness | exact bytes | (9I) hash only / (E7) body gap | byte-complete | incomplete | raw response/body missing | EVIDENCE_VALIDATION | medium | evidence design | retain as declared gap |

The earliest **global** breaks are the bridge tool-drop and the textual-tool
parse failure; the amendment fixes upstream packet + protocol first (per the
operator's instruction not to design around downstream symptoms while leaving
upstream failures intact).

---

## 16. Primary root cause

`MULTI_FACTOR_FAILURE` — confirmed. No single model defect explains the
observations. The earliest controlled failure is the tool-dialect/parser
mismatch (Lane B); the earliest JCode-specific loss is the legacy bridge
dropping roles/tools (Lane D/F counterfactual).

## 17. Secondary causes

Bridge role/tool loss; baseline result-reinjection failure; packet
bloat/task burial/context misallocation; unreceipted truncation risk; missing
intake criteria/test completeness; JCode prompt conflict; absent focused-test
tool; 14B verifier mismatch; evidence gaps (E7 body, 9I raw bytes).

## 18. Models' actual qualified capabilities

- **7B:** Task R direct PASS; Task W direct PASS. Read-tool intent present.
  Qualified for read-only direct; `MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS` (not
  incapable).
- **14B:** Task R direct PASS; Task W behaviorally correct (evaluator-aligned
  pending). Higher latency (4 timeouts). `MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS`;
  incapability not proven.

## 19-21. Current readiness

- Packet: `PIPELINE_NOT_READY` (<2% relevant, task buried).
- Baseline harness: `PIPELINE_NOT_READY` (reinjection defect).
- JCode: `JCODE_TOOL_COMPATIBILITY_READY=false` (binary/safety suitable;
  prompt/bridge/parser/test-tool unsuitable for these models today).

## 22-24. Artifacts and sub-gates

`PACKET_AMENDMENT.md` is the controlling spec. Supporting artifacts listed in
section 9 of the operator prompt. Sub-gates 2-J.9T-A through 2-J.9T-I defined
in the amendment (section O).

## 25-26. Gates

Retained: 2-J.9B-9E Batch 1; runtime 9G-D-9H technical acceptance; 9I
containment/safety (9I model-quality attribution refined to
`EVIDENCE_INCOMPLETE`).
Blocked: 2-J.9T execution, 2-J.9J, 2-J.9K, 20-task, 80-run, Campaign 4,
production promotion, production-default bridge change.

## 27. Files changed by THIS review

New author-only artifacts under
`docs/architecture/jcode-qualification/pipeline-diagnosis/glm-review/`:
`PACKET_AMENDMENT.md`, `packet_amendment.json`,
`SOL_AUDIT_INDEPENDENT_REVIEW.md`, `sol_audit_independent_review.json`,
`PACKET_READINESS_ACCEPTANCE_MATRIX.md`,
`packet_readiness_acceptance_matrix.json`, `MODEL_READY_PACKET_SCHEMA.json`,
`TOOL_DIALECT_NORMALIZATION_SCHEMA.json`, `AGENT_LOOP_CONTRACT.md`,
`JCODE_COMPATIBILITY_PROFILE.md`, `QWEN_7B_COMPATIBILITY_PROFILE.md`,
`QWEN_14B_COMPATIBILITY_PROFILE.md`, `EVALUATOR_ALIGNMENT_CONTRACT.md`,
`TERRA_HIGH_GATE_2J_9T_HANDOFF.md`. No source, no test, no fixture, no
benchmark, no production path, no daily-runtime path touched.

## 28. Tests and validations

- Executable evidence verifier reproduced at HEAD: `passed: true`.
- 203 JCode-focused tests are Sol's claim (not re-run by this read-only review);
  the amendment adds no executable code, so no new tests apply.
- All new JSON artifacts validated with `jq empty`.

## 29. Benchmark integrity

Frozen benchmark runs = 0, mutations = 0 (commit-range `git diff --name-only`
shows zero benchmark/qualification_fixture/fixture_proxy paths).

## 30. Daily-runtime integrity

Daily-runtime mutations = 0; no daily-runtime worktree used for execution.

## 31. Push status

Not pushed by this review. Local author-only commit on the isolated audit
branch is the only change, and only if the operator authorizes a commit. No
force-push, no merge.

## 32. Exact next authorized action

`Operator review and adoption of PACKET_AMENDMENT.md, followed by a prospective
Terra High authorization for Gate 2-J.9T-A through Gate 2-J.9T-D only.`
