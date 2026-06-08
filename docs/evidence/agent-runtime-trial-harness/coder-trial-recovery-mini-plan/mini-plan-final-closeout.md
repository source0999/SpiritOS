# Coder Trial Recovery Mini-Plan Final Closeout

## Summary

Completed Gate 1 and Gate 2 only. Did not execute future gates. Did not rerun Coder 10, Coder 25/50/100, grading, prompt expectations, dropdown runner, Designer, Combined, media, SpiritFlix, Scout, Oracle, 999Playr, or unrelated routes.

## Gate 1 status

GO. Trial mode now bans scaffold/fallback/backend-generated page output from PASS and records provenance/trust fields.

## Gate 2 status

GO for future hardening after manual approval. Research report written and optional read-only Obsidian context integration added.

## Contaminated suite status

`suite-mq4in5v9` remains invalid benchmark evidence. Do not claim it proves Coder model ability.

## Verification snapshot

Commands and latest results are recorded in the final assistant report. Final verification should be rerun after any later edits using the pasteable block below.

## Final pasteable terminal verification block

```bash
cd /home/source/SpiritOS
set -euo pipefail

echo "=== repo status ==="
git status --short
git diff --stat

echo "=== trial contamination / scaffold ban tests ==="
npm run test -- src/lib/coding/__tests__/reversible-trial-runner.test.ts src/lib/coding/__tests__/durable-run-store.test.ts src/components/coding/__tests__/coding-cockpit-shell.test.tsx

echo "=== source proxy scaffold/fallback tests ==="
.venv-source-proxy/bin/python -m unittest \
  source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_agent_lab_create_blocks_known_scaffold_in_live_trial_mode \
  source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_calculator_create_blocks_fallback_after_invalid_model_tsx_in_live_trial \
  source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_agent_lab_known_apps_cannot_fall_back_to_pass_in_live_trial \
  source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_agent_lab_known_scaffold_remains_available_outside_live_trial \
  source_proxy.tests.test_verification_contracts \
  source_proxy.tests.test_diff_verification

echo "=== obsidian context tests ==="
.venv-source-proxy/bin/python -m unittest source_proxy.tests.test_obsidian_context source_proxy.tests.test_self_status source_proxy.tests.test_prompt_packet_context_metadata

echo "=== typecheck ==="
npm run typecheck -- --pretty false

echo "=== diff check ==="
git diff --check

echo "=== HTTPS LAN health ==="
curl -k -I --max-time 10 https://localhost:3000/coding || true
curl -k -s --max-time 10 https://localhost:3000/v1/coding/runs/active | jq . || true
curl -k -s --max-time 10 https://localhost:3000/v1/coding/agent-lab-baseline | jq . || true

echo "=== source proxy health ==="
curl -k -s --max-time 10 https://localhost:8787/v1/self/status | jq . || true

echo "=== fallback/scaffold audit ==="
grep -RIn "KNOWN_PAGE_SCAFFOLDS\|bounded_create\|deterministic scaffold\|fallback" source_proxy src | head -n 200 || true

echo "=== final criteria ==="
echo "Trial PASS requires proven model-authored output."
echo "Scaffold/fallback/provenance-missing rows must be INVALID or NEEDS_FIX."
echo "Obsidian context must be read-only, optional, and disabled by default unless configured."
```

## Recommended next gate

Gate 3: hardening plan based on this research and read-only context work.

## Approval recommendation

Britton should approve moving to hardening only after reviewing the Gate 1/2 closeouts and accepting that `suite-mq4in5v9` is invalid model evidence.
