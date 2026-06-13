# final-l3-clean-05 Transparent Trace

- Prompt: make a pretend balcony forecast tile
- Family: weather/forecast/tile
- Route: GO / disposable_small_file_bundle
- Model lane: QWEN_ONLY (qwen2.5-coder:7b)
- Gemma status: VERIFIER_PREVIEW_ONLY
- Probe: weather-card-fields
- Open/probe: PASS / FAIL
- Before: City: San Francisco  Temperature: 68°F  Condition: Sunny  Change Weather to New York
- After: City: San Francisco  Temperature: 68°F  Condition: Sunny  Change Weather to New York
- Strict final: FAIL

## Evidence

- preview: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/workspace/index.html`
- score: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/score.json`
- receipt: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/receipt.json`
- transcript: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/transcript.txt`
- workspace_diff: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/workspace.diff`
- behavior_probe: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/behavior-probe.json`
- behavior_failure_packet: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/behavior-failure-packet.json`
- repair_result: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/post-behavior-repair-result.json`
