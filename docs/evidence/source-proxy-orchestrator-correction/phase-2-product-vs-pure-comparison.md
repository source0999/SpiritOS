# Source Proxy Orchestrator Correction Phase 2 Product vs Pure Comparison

## Status

Local/mocked comparison only.

No provider/model calls, benchmark prompts, runtime changes, test changes, real app mutation, or git mutation were performed.

## Comparison Table

| Case | Route | Task Shape | Proxy Scope Help | Model Target | Files Touched | Score | Benchmark Eligible | Key Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Product homepage | `product` | `disposable_single_file_artifact` | artifact class `.html` boundary | `index.html` | `index.html` | `GO` | `false` | Generic resolver, no exact proxy target, model-authored bytes match file |
| Pure homepage | `pure_diagnostic` | none | none | `site/home.html` | `site/home.html` | `GO` | `true` | Model chose path, no Product helper, no system preselected target |
| Product markdown artifact | `product` | `disposable_single_file_artifact` | artifact class `.md` boundary | `release-checklist.md` | `release-checklist.md` | `NO-GO` by legacy homepage scorer | `false` | Receipt completed and proves generic artifact orchestration; score is homepage-specific |
| Product JSON wrong extension | `product` | `disposable_single_file_artifact` | artifact class `.json` boundary | `config.txt` | none | `NO-GO` | `false` | Executor blocked `target_not_allowed` |

## Product Assertions

Product mode passed these local/mocked assertions:

* Proxy task shape is visible in receipts.
* Generic artifact resolver is visible through `task_shape_source`.
* Artifact class is recorded separately from model-authored target.
* Product homepage did not use a proxy exact target suggestion.
* Runtime executed model-authored `WriteFile` actions only.
* File bytes matched model action content for accepted homepage output.
* Non-homepage Markdown artifact completed at the receipt/executor layer.
* JSON wrong extension was blocked.
* Product route was benchmark-ineligible when proxy orchestration was used.

## Pure Assertions

Pure mode passed these local/mocked assertions:

* Route type is `pure_diagnostic`.
* No Product artifact class was supplied.
* No proxy exact target was supplied.
* Model authored the target path.
* Benchmark eligibility was true only for Pure with useful model-chosen output and no helper fields.

## Scoring Boundary

The current `human_messy_homepage` scoring surface is still homepage-centered. It can label a non-homepage Markdown artifact `NO-GO` despite a completed Product receipt with model-authored content and no real app mutation.

Phase 2 should therefore treat receipt-level verification as the authority for generic non-homepage artifacts until a later approved patch generalizes the scoring surface.

## Decision

GO for local/mocked Product/Pure route separation.

NO-GO for using the legacy homepage score as a universal generic artifact success label.
