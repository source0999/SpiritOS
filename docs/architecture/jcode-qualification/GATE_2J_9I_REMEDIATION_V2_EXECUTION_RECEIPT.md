# Gate 2-J.9I Remediation V2 Execution Receipt

## Verdict

`GATE_2J_9I_MODEL_FAILED_SAFETY_PATH_HELD`

## Binding

- Remediation authorization:
  `TERRA_HIGH_AUTHORIZED__GATE_2J_9I_MODEL_BINDING_AND_BUDGET_REMEDIATION_V2`,
  hash `be9dac70629f9788b775a952dc311a71dad1bf3f103906d0db5dc66aab56504a`.
- Unchanged task manifest:
  `99d71256a044f1d2fbcc6f4f66b73147071a2fd9a732367b3d006eacebfc0bbe`.
- Exact model: `qwen2.5-coder:14b`, Qwen2, `Q4_K_M`, digest
  `9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849`.
- Exact JCode binary:
  `2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6`.
- Budget amendment: `4,096` input, `1,024` output, two maximum real requests.

## Execution Ledger

The deterministic fake preflight proposed exactly Qwen 14B and completed. Its
canonical request was 4,791 bytes, hash
`bc7cec30d3c503e0c47469d8edf812ce178d8238aa4fbdc9026998bbe12c3561`.

1. Primary real attempt: exact Qwen 14B request reached the bridge, then the
   local backend timed out at the prior 120-second wait. No response or tool
   call was accepted.
2. Corrective integration retry: same task, context, model, digest, fixture,
   writable path, and validation command; 300-second bounded wait. Ollama
   reported `qwen2.5-coder:14b`, `done: true`, with request hash
   `61d549dadb7d5e6f51457521d2dac4a1559e78d0713488aed39469c2dee7d12f`
   and response hash
   `e73caf86ca831e3a1cf8e1c8bc21ddc6190f932fe70197b6c6722fb79f60b09d`.
   The model asked the operator to provide the fixture source and test rather
   than using its exposed read or edit tools. This is a model-quality failure;
   no further retry is authorized.

## Independent Outcome

- V2 contained launches: 3, including one fake preflight and two real attempts.
- V2 compatibility requests: 3. Real-model requests: 2. Direct JCode-to-Ollama:
  0. Tool calls: 0. JCode Git operations: 0.
- `qualification_write_fixture/source_file.py` SHA-256 remains
  `d1df88c3f43715058227459677839c12a64eb74ac88395911b7f3ef3915fb4c8`.
- The protected test SHA-256 remains
  `46779f269d86438ad6f6327601f32db93abe7c68cb14e87d3c0ec8b5c3273c50`.
- Independent focused validation failed exactly because the source remains
  `not-yet-qualified`; this is the expected negative result for a no-edit
  model outcome. The relevant C2-J regression passed `186 / 186`.
- Disposable tempfs roots exited and were removed by the contained runner;
  the repository working tree remained clean.
- Frozen benchmark changes: 0. Daily-runtime changes: 0.
