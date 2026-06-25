# Direct SearXNG A3 Query 10x Durable Provider Proof - 2026-06-25

## Purpose

Capture durable direct SearXNG provider proof for the Plan 3 A3 query so the prior
`/tmp` direct-provider proof is no longer ephemeral.

This proves direct SearXNG availability for the A3 query at capture time.
This does not rerun Set A.
This does not prove Set B/C.
This does not replace append-only Set A receipts.
This only removes the /tmp ephemeral-provider-proof caveat before Set B readback.

## Branch / Head

- repo: `/home/source/SpiritOS`
- branch: `integration/cleanup-plan3-debug-20260623`
- HEAD: `73e87d8d10d286cfd911b6ced1616f15ec3bc08d`

## Provider / Query

- provider URL: `http://127.0.0.1:8080`
- query: `Android Jetpack Compose share intent local task app receipt polling`
- capture window: `2026-06-25T14:50:35.924018+00:00` to `2026-06-25T14:51:07.433924+00:00`
- raw JSONL: `direct-searxng-a3-query-10x-20260625.jsonl`
- machine summary: `direct-searxng-a3-query-10x-20260625-summary.json`

## Why This Proof Was Needed

The GLM Set A stability and lane audit confirmed Set A readiness but preserved one
non-blocking caveat: `MISSING_EPHEMERAL_TMP_PROVIDER_EVIDENCE`. The direct SearXNG
10x proof existed under `/tmp`, while durable provider evidence also survived inside
append-only Set A receipts. This file captures the direct provider check in the Plan
3 docs tree before Set B readback.

## Attempt Summary

| Attempt | Timestamp UTC | HTTP status | Result count | Error |
| --- | --- | ---: | ---: | --- |
| 1 | `2026-06-25T14:50:35.924018+00:00` | 200 | 20 | none |
| 2 | `2026-06-25T14:50:40.128107+00:00` | 200 | 20 | none |
| 3 | `2026-06-25T14:50:43.520689+00:00` | 200 | 20 | none |
| 4 | `2026-06-25T14:50:46.953034+00:00` | 200 | 20 | none |
| 5 | `2026-06-25T14:50:50.329383+00:00` | 200 | 20 | none |
| 6 | `2026-06-25T14:50:53.692630+00:00` | 200 | 20 | none |
| 7 | `2026-06-25T14:50:57.179180+00:00` | 200 | 20 | none |
| 8 | `2026-06-25T14:51:00.583515+00:00` | 200 | 20 | none |
| 9 | `2026-06-25T14:51:04.029832+00:00` | 200 | 20 | none |
| 10 | `2026-06-25T14:51:07.433924+00:00` | 200 | 20 | none |

## Counts

- attempts: 10
- ok count: 10
- HTTP 200 count: 10
- zero-result count: 0
- timeout/error count: 0
- result counts: `20, 20, 20, 20, 20, 20, 20, 20, 20, 20`

## Top Source Titles / Hosts

Representative top returned titles across the 10 attempts:

- `Send simple data to other apps | App data and files - Android Developers`
- `Kotlin Multiplatform samples`
- `Take your messaging to the next level - basic, better, and best`
- `The ULTIMATE Guide to Sharing Data Between Screens in Jetpack ...`
- `Jetpack Compose Add a Share Button to your App`
- `Intent In Jetpack Compose`
- `Intercepting Android's action_send Intents`
- `Moderne Recipes | OpenRewrite Docs`

Representative returned hosts/URLs:

- `developer.android.com/training/sharing/send`
- `developer.android.com/social-and-messaging/guides/communication/basic-better-best`
- `kotlinlang.org/docs/multiplatform/multiplatform-samples.html`
- `youtube.com/watch?v=h61Wqy3qcKg`
- `medium.com/@jpmtech/jetpack-compose-add-a-share-button-to-your-app-5f26b7554e94`
- `medium.com/@kathankraithatha/intent-in-jetpack-compose-88275bc3b878`
- `credera.com/en-au/insights/intercepting-androids-action_send-intents`
- `docs.openrewrite.org/reference/moderne-recipes`

## Relationship To Set A Evidence

This durable direct-provider proof addresses only the GLM caveat about `/tmp`
provider evidence. The Set A verdict remains based on the already-captured Set A
append-only receipts and audits. No Set A receipt, runner, model contract, or verdict
was changed by this capture.

## Caveats

- This is a point-in-time direct SearXNG availability check.
- Result ordering varied slightly across attempts, which is normal for live search.
- The source titles/hosts here are summarized for human review; the complete per-run
  raw result samples are preserved in the JSONL.
- This does not exercise Set B/C prompts, patch/verifier lanes, model generation, or
  Plan 4 behavior.

## Verdict

`DURABLE_SEARXNG_PROOF_CAPTURED`
