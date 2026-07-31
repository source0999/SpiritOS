# Campaign 2-J Pipeline Diagnosis Operator Authorization

Receipt type: `OPERATOR_AUTHORIZATION`

Authorization ID: `OPERATOR_AUTHORIZATION__C2J_PIPELINE_DIAGNOSIS_20260731_V1`

## Prompt Binding

The complete operator prompt is stored as `OPERATOR_AUTHORIZATION_PROMPT.txt`.
It was strictly decoded as UTF-8, normalized to Unicode NFC and LF line
endings, given a terminal LF only because one was absent, and encoded as UTF-8
without a BOM.

- Canonical prompt SHA-256: `f45bde0f3fd1c4c225f4a896577a0778408d449ebee41b3dc4f57c0171ab7afb`
- Canonical bytes: `30388`
- Original attachment SHA-256: `115b05f56cb3f7dbc697598363f598042414e2473c539deeef4d9cee6b887106`
- Original attachment bytes: `30387`

This receipt's operator provenance is valid only through that prompt hash.

## Starting State

- Campaign worktree: `/home/source/SpiritOS-source-proxy-jcode-qualification-20260726`
- Campaign branch: `codex/source-proxy-jcode-qualification-20260726`
- Full starting and upstream HEAD: `07151b44cb886ac4d8c3668e947e81825d01bd50`
- Ahead/behind: `0/0`; worktree clean
- Audit worktree: `/home/source/SpiritOS-source-proxy-jcode-pipeline-diagnosis-20260731`
- Audit branch: `codex/source-proxy-jcode-pipeline-diagnosis-20260731`

## Authorized Scope

The operator authorizes an isolated, non-benchmark causal audit of task
normalization, context construction, JCode prompting/session behavior, bridge
transformation, exact local-model input/output, tool schemas and parsing, agent
loop recovery, and evaluation. Diagnostic-only instrumentation, immutable Task
R and Task W fixtures, tests, evidence schemas, one global correction, bounded
confirmation runs, root-cause reports, and a proposed Campaign 2-J amendment
are permitted.

Repository writes are limited to the diagnosis directory, the named
diagnostic modules/CLI/test/fixture paths, and the named runner script in the
JSON receipt. Commits and pushes to the isolated audit branch are authorized;
merge and deployment are not.

## Request Budget

- Maximum real local-model requests, including retries and multi-turn tool
  loops: `36`
- Maximum model turns per run: `3`
- Authorized exact models: `qwen2.5-coder:7b` at digest
  `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`
  and `qwen2.5-coder:14b` at digest
  `9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849`
- Model requests before this receipt: `0`

## Denied Actions

Frozen benchmarks, benchmark solutions, hidden expectations, daily runtime,
production mutation/deployment, Campaign 4 advancement, cloud or paid models,
direct JCode-to-Ollama access, fallback, unrestricted networking, credentials,
persistent sessions/memory, JCode Git authority, cross-run answer reuse, and
task-specific prompt tuning remain denied. The full forbidden path list and
stop conditions are binding in the JSON receipt.

This receipt must be committed and pushed before any diagnostic model request.
