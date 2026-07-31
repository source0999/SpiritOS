# Gate 2-J.9I Safe Write-Smoke Authorization

`TERRA_HIGH_AUTHORIZED__GATE_2J_9I_SAFE_WRITE_SMOKE_V1` is an operator-issued,
prospective authorization bound to clean commit `6c1f9dbac332cc91405eea0ddbdf58e43d6be1cb`.
Its canonical JSON and self-hash are in
`gate_2j_9i_safe_write_smoke_authorization.json`.

It permits one non-benchmark, contained task against exactly
`qwen2.5-coder:14b` at digest
`9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849`, only
through the sealed Proxy bridge. The sole writable path is
`qualification_write_fixture/source_file.py` in a disposable worktree.

It does not permit a model fallback, direct JCode-to-Ollama traffic, cloud
access, package installation, a JCode Git operation, benchmark or daily-runtime
access, Gate 2-J.9J, the 20-task diagnostic set, or the 80-run comparison.

Passing Gate 2-J.9I with Qwen 14B proves only the safe contained write path; it
does not establish Qwen 7B as the primary production coder.
