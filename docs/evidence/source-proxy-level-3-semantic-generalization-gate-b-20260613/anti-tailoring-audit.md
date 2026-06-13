# Anti-Tailoring Audit

Required claim:

No exact prompt tailoring found in searched runtime/source scopes.

Do not overclaim:

This does not prove prompt tailoring does not exist anywhere.

## Runtime/Source Scopes Searched

- `source_proxy/decision`
- `source_proxy/api`
- `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py`
- `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs`

## Exact Failed Prompt String Search

Searched:

- `make a parking garage cost sharer`
- `make a dusk dawn palette switch`
- `make a pretend balcony forecast tile`
- `make a secret phrase strength gauge`
- `make a finger paint doodle pad`

Result: no matches in searched runtime/source scopes.

## Exact Failed Prompt ID Search

Searched:

- `final-l3-clean-02`
- `final-l3-clean-03`
- `final-l3-clean-05`
- `final-l3-clean-09`
- `final-l3-clean-10`

Result: no matches in searched runtime/source scopes.

## Suspicious Branch Search

Searched for prompt-id branches, exact failed prompt strings, canned artifacts, deterministic scaffold, fallback scaffold, and backend-authored terms.

Findings:

- No exact failed prompt string branch found.
- No failed prompt id branch found.
- No canned artifact output tied to exact failed prompts found.
- No deterministic scaffold branch found.
- No fallback scaffold branch found.
- `source_proxy/api/decision.py` has unrelated existing `prompt_id` handling for `coder-001-init-dummy-product-site`; this is not one of the final clean failed prompt ids.
- `artifact_repair_contract.py` includes text forbidding backend-authored rescue content; this is a guardrail, not a rescue implementation.

## Evidence/Test Strings

Exact prompt strings appear in evidence outputs and prompt-lock results as expected. Gate B added synonym fixtures to tests, not exact final failed prompt branches in runtime.

## Broad Search Note

An initial broad grep over larger share paths timed out; the audit was rerun with narrower runtime/source scopes and fixed-string searches.
