PIPELINE_DIAGNOSIS_COMPLETE__MULTI_FACTOR_FAILURE__AMENDMENT_READY

# Sol Ultra Final Pipeline Diagnosis

1. **Repository and audit branch.** Canonical Campaign 2-J repository:
   `/home/source/SpiritOS-source-proxy-jcode-qualification-20260726`, branch
   `codex/source-proxy-jcode-qualification-20260726`. Isolated audit:
   `/home/source/SpiritOS-source-proxy-jcode-pipeline-diagnosis-20260731`, branch
   `codex/source-proxy-jcode-pipeline-diagnosis-20260731`.
2. **Starting and final HEAD.** Starting HEAD is
   `07151b44cb886ac4d8c3668e947e81825d01bd50`. Root-cause report HEAD is
   `abf6b61c4576ab423d11aa0ff9c62f8ca74f0c61`. The final handoff commit cannot
   contain its own hash; exact final HEAD is resolved by `git rev-parse HEAD`
   after this artifact is committed and reported in the external final response.
3. **Authorization.** Operator prompt SHA-256 is
   `f45bde0f3fd1c4c225f4a896577a0778408d449ebee41b3dc4f57c0171ab7afb`.
   Authorization commit is
   `c42d62f189542e69112e600c5e0bdef05e2705ac`.
4. **Current Campaign 2-J status.** The canonical branch remains
   `GATE_2J_9I_MODEL_FAILED_SAFETY_PATH_HELD__LATER_GATES_BLOCKED`; no canonical
   campaign mutation or merge occurred.
5. **Models tested.** `qwen2.5-coder:7b`, digest
   `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`;
   `qwen2.5-coder:14b`, digest
   `9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849`.
6. **Run/request count.** 24 diagnostic runs made exactly 24 real local model
   requests of the authorized 36. Maximum observed turns per run was one of
   three. Six requests timed out; there were no retries.
7. **Task R results.** Lane A: 7B PASS, 14B PASS. B: both FAIL with text JSON
   reads/no native calls. C: both FAIL after one successful read because no
   observation reinjection occurs. D: 7B FAIL/generic acknowledgement, 14B
   TIMEOUT. E: both TIMEOUT, with E7 the sole exact-request capture gap. F: 7B
   FAIL/generic acknowledgement, 14B TIMEOUT.
8. **Task W results.** Lane A: 7B PASS; 14B evaluator FAIL despite semantically
   correct code. B: both FAIL with text JSON reads/no native calls. D and F: 7B
   FAIL after legacy bridge loss; 14B TIMEOUT; no edit or test in any tool lane.
9. **Direct inline capability.** Both models pass Task R. 7B passes Task W.
   14B produces correct Task W behavior but needs evaluator alignment before a
   formal pass. No evidence supports a raw incapability verdict.
10. **Minimal tool calling.** Neither model passes. Both recognize the need to
    read but emit assistant-text JSON rather than provider-native calls.
11. **Baseline harness.** It does not pass Task R in minimal Lane C. Its parser
    and executor accept one read, then the loop stops without reinjecting the
    observation. Full Lane E also does not pass and times out for both models.
12. **JCode minimal mode.** Legacy D does not pass. Corrected D preserves tools
    but still does not pass because text reads are not parsed; JCode records
    zero tool events.
13. **Full Proxy packet.** No full lane passes. Baseline E times out; JCode F
    cannot read the mounted packet because the first-turn tool path fails.
14. **First proven causal failure.** Lane B proves
    `MODEL_TOOL_DIALECT_INCOMPATIBILITY` plus `TOOL_CALL_PARSE_FAILURE`: tools
    reach Ollama unchanged, while both models return text calls that the
    native-only harness ignores. The first JCode-specific loss is
    `TOOL_SCHEMA_DROPPED` at the legacy bridge.
15. **Secondary failures.** Bridge role/tool loss; baseline result-reinjection
    failure; packet bloat/task burial/context misallocation; unreceipted
    truncation risk; missing intake criteria/test completeness; JCode prompt
    conflict; absent focused-test tool; 14B verifier mismatch; evidence gaps.
16. **7B meaning.** 7B can solve both tiny direct tasks. It is currently
    `MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS`, not incapable.
17. **14B meaning.** 14B grounds the read task and supplies semantically correct
    write code. It shares the text-call incompatibility and has material
    latency/context sensitivity. Incapability is not proven.
18. **Packet readiness.** The current packet is not model-ready: relevant ratio
    falls below two percent in full diagnostic packets, task text is buried,
    acceptance criteria are absent from production intake, and critical
    truncation/completeness is not enforced.
19. **Tool-dialect readiness.** The current native-only dialect is not
    Qwen-compatible for either tested digest. A bounded native-plus-text profile
    must be qualified.
20. **JCode suitability.** The binary and containment are identity/safety
    suitable. The current prompt, bridge/parser profile, missing test tool, and
    absent production dispatcher make it unsuitable for these selected models
    today.
21. **Global correction.** The diagnostic bridge was changed to preserve
    ordered roles and tools through Ollama `/api/chat` and reconstruct OpenAI
    SSE. Legacy remained default; no production behavior changed.
22. **Confirmation result.** The bridge field-preservation counterfactual passes
    in 4 of 4 cells. End-to-end tasks pass in 0 of 4 because Qwen text reads
    remain unparsed; W also lacks a test tool.
23. **Amendment.** `CAMPAIGN_2J_GATE_9T_PACKET_TOOL_COMPATIBILITY_V1` creates
    Gate 2-J.9T immediately after 9I and before 9J.
24. **Accepted gates retained.** Gates 2-J.9B through 2-J.9E Batch 1; Runtime
    Gates 2-J.9G-D through 2-J.9H technical acceptance; and the 2-J.9I
    containment/safety-path finding remain accepted. The unsupported model
    incapability implication is refined, not the safety result.
25. **Gates blocked.** Gate 2-J.9T qualification, 2-J.9J, 2-J.9K, the sealed
    20-task diagnostics, the 80-run comparison, and Campaign 4 remain blocked.
26. **Tests/evidence.** 203 JCode-focused tests pass. All audit JSON validates.
    The executable evidence verifier passes 24 runs/24 requests, exact digests,
    run hashes, request budget, turn cap, six timeouts, and the one declared
    gap. `git diff --check` passes.
27. **Benchmark integrity.** Frozen benchmark runs and mutations are zero; no
    benchmark path changed.
28. **Daily-runtime integrity.** Daily-runtime mutations and service changes are
    zero; no daily-runtime worktree was used for model execution.
29. **Files changed.** Changes are limited to diagnostic JCode instrumentation,
    its CLI/tests/immutable fixtures, authorization/freeze/manifests, request
    ledger/journal, 24 sealed run directories, causal reports, amendment, and
    handoff under the isolated audit branch.
30. **Push status.** Authorization, instrumentation, matrix, confirmation, and
    root-cause stages are pushed. Final amendment/handoff push and exact 0/0
    status are verified after this self-referential artifact is committed and
    reported externally. No force-push or merge is authorized.
31. **Remaining uncertainty.** E7 lacks its exact request body; prior 9I lacks
    raw response bytes; no provider-native tool-call fragment was available to
    test fragmented reconstruction; no production request was run; 14B's
    behavioral evaluator and latency budget require qualification.
32. **Exact next authorized action.** Review/adopt Gate 2-J.9T, then issue a new
    bounded diagnostic authorization to implement one concise packet, a
    native-plus-Qwen-text parser with observation reinjection, a sealed focused
    test tool, and behaviorally aligned evaluation; rerun only the minimal
    qualification cells. Do not start 2-J.9J/9K, 20-task, 80-run, production,
    merge, deployment, or Campaign 4 work.
