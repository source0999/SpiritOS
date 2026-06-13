# False-Positive / False-Negative Review

Status: COMPLETE BEFORE PATCHING

## Counts

- False-positive PASS: 1
- False-negative FAIL: 0
- Correct as reported: 9
- Probe/report mismatch: 1

## False Positive

`make a quick jot pad app`

- Reported: PASS.
- Strict verdict: FAIL.
- Evidence: `behavior-probe.json` recorded `appears: false`.
- Visible after-action text: `Note saved successfully.`
- Required behavior: the typed note text itself must appear visibly after save/add.
- Classification: `false_positive_pass`, `probe_contract_mismatch`, `report_verdict_mismatch`.

## False Negatives

No false-negative FAIL was found in the 10d evidence.

`make a pizza money splitter` remains PASS under strict review. The typed sentinel text does not need to appear for calculator/splitter behavior; the relevant criterion is visible numeric/result output changing after input/action.
