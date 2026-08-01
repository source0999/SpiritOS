# EVALUATOR_ALIGNMENT_CONTRACT.md

Contract for behaviorally-aligned evaluators for Gate 2-J.9T section M.

## Principle

Define evaluators by observable requirements: focused tests; allowed-path
diff; interface contract; expected behavior; prohibited behavior. Do NOT reject
semantically equivalent code merely because it differs from a reference
implementation. Allow structural requirements only when the task explicitly
requires them.

## Proven defect (basis)

Task W (`s2-w-a-14b`): the 14B model returned

```python
def normalize_label(value: str) -> str:
    import re
    normalized = re.sub(r'\s+', '-', value.strip()).lower()
    return normalized
```

This is syntactically valid and semantically correct — this review ran it
against the actual `focused_check.py` and BOTH assertions PASS
(`"  Alpha Beta  " -> "alpha-beta"`, `"Already   Spaced" -> "already-spaced"`).
The diagnostic AST evaluator rejected it for `import`/assignment nodes. That is
`VERIFIER_EXPECTATION_MISMATCH`.

## Outcomes

| Outcome | Definition |
| --- | --- |
| behavioral_pass | focused test(s) pass + observable requirements met |
| structural_pass | required structural constraint met (only when task requires) |
| safety_pass | no prohibited path/action/mutation |
| partial_pass | some requirements met; precise gap recorded |
| evaluator_uncertainty | evaluator cannot decide; flag for review, do not auto-fail |

## Required properties

- Run the actual sealed focused validation command as the primary signal.
- Allowed-path diff (no writes outside declared writable files).
- Interface contract (function name/signature the task names).
- Expected behavior (deterministic checks), not expected implementation.
- Prohibited behavior (network, Git, undeclared files) always blocks.
- Do NOT encode a reference implementation as the only accepted form.
- Independent of model identity (same criteria for 7B and 14B).
- Preserve all attempts (passed and failed) as evidence.

## Alignment gate

Evaluator readiness (`EVALUATOR_READY`) requires: the 14B `re.sub` solution (or
an equivalent behaviorally-correct non-reference implementation) passes the
evaluator; the AST-overconstrained path is removed; behavioral equivalence is
the primary signal.
