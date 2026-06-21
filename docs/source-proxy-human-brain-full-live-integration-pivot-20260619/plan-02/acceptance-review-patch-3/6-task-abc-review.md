# Task A/B/C Review

## Task A

Verdict: NEEDS_FIX

Task A depends on the specialist/model-lane proof. Gemma and Hermes are live, but the Qwen coder and browser/functional verifier proof is not live enough for the review prompt. Advisory UNVERIFIED verifier output and metadata-only Qwen availability cannot be counted as true Plan 2 GO.

## Task B

Verdict: PASS

The research path uses live SearXNG evidence, records sources, marks them untrusted, changes downstream behavior, and blocks an explicit bad provider without silent fallback.

## Task C

Verdict: PASS

The Mac write/action and Mac search/check proofs are live, causal, consumed, and include fail-closed unsafe-path behavior. This review also confirmed read-only task trace consumer events for representative Mac write and search/check tasks.

## Task Summary

Task B and Task C are acceptable. Task A is not acceptable until the specialist lane stops treating advisory/metadata-only states as sufficient for GO or the required Qwen/browser verifier lanes are actually proven live and consumed.
