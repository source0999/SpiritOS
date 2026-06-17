# Model-Lane Audit (evidence-based)

Date: 2026-06-16 (UTC). Basis: 30-row battery receipts + source inspection.

## Qwen (coder/action only)

- Role correct: `used` 30/30; produced `replace_file` actions; never planned or verified.
- Hash discipline PERFECT: `final_coder_packet_hash == coder_received_packet_hash` 30/30.
- Output contract: strict (`_fip4_extract_qwen_file_action` rejects diffs/markdown; accepts
  `<file>` or JSON `replace_file`). 0 output-contract failures in the battery.
- Quality concern: emits plausible-but-non-functional scaffolds and ignores file-type intent
  (React/JSX written into plain `.js` targets). `s1-02-calculator` content = `<h1>Calculator</h1>`
  + "Add your calculator components here". No arithmetic. Still GO.
- Latency: ~190-360s/row including cold loads and contention.

## Gemma (pre-coder advisory/spec/context)

- Role correct: live Ollama JSON call; rejects any `qwen` model (anti-fallback in source).
- Stability ISSUE: `failed` on ~6 rows via `local_ollama_model_timeout` (ReadTimeout) under
  3-model VRAM contention; e.g., `s2-10-health` gemma `failed` yet productive GO.
- AUTHORITY GAP: Gemma failure does NOT gate or downgrade the FIP-5 verdict. The pre-coder
  spec lane can die and the row still passes -> the "context packet" is decorative for acceptance.

## Hermes critic (pre-coder critique/risk)

- Role correct: live call; distinct from verifier; rejects `qwen`.
- `failed` on `s3-04-tasks` (productive GO) -> same non-gating gap as Gemma.

## Hermes verifier (post-code verifier)

- Role correct: post-code only; cannot turn UNVERIFIED->PASS; cannot override deterministic or
  browser (`_fip5_normalize_hermes_verifier_output` downgrades PASS on det/browser failure —
  proven: 8/8 `.html` rows Hermes returned FAIL/NEEDS_FIX, never PASS).
- Evidence-quality concern: for non-`.html` rows there is no functional/browser evidence, so
  PASS rests only on structural deterministic pass — a low-evidence rubber-stamp.
- Model: `hermes3:8b-abliterated` (a safety-stripped model serving as integrity authority).

## Designer / design context

- Read-only advisory; present in plumbing, typically `skipped`/`blocked` when refs absent.

## Cartographer

- Advisory context only; READ_ONLY authority (can_apply/commit/push/worker = false). Real repo
  map (files_indexed ~180 in prior receipts). NOT a route owner. Correct.

## Scout / SearXNG / Mac worker advisory

- Scout: honest evidence lane; `skipped` 30/30 (no current-info prompts). Default 500ms timeout.
- SearXNG: honest; `skipped` 30/30. Receipt guard forces `used`->`failed` without a provider call.
- Mac worker: hardcoded `skipped` stub; never invoked. Cosmetic lane.

## Verdict

Role SEPARATION is correct and enforced (Qwen != planner/verifier; verifier != critic;
advisory lanes reject qwen). The two real problems are (1) local advisory model INSTABILITY
under contention and (2) advisory failures being NON-GATING, so a degraded lane vanishes behind
a productive GO. Plus the verifier's PASS has no functional evidence for non-UI code.
