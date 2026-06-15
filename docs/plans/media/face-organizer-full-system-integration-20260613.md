# Face Organizer Full System Integration Plan

Date: 2026-06-13
Repo: `Z:\` / `/home/source/SpiritOS`
Primary script: `scripts/media/face_organizer.py`
Current media source: `/DATA/yes`

## Authority And Scope

This is a plan-only document. It does not authorize implementation, media movement, web evidence collection, face enrollment, organizer `--apply`, git mutation, or service restarts. Every phase and increment below has a manual pause gate. Britton must approve the next phase before work proceeds.

Allowed future evidence sources are public/stage/profile handles, visible text watermarks, profile URLs, filenames, folder hints, local sidecars, local known-performer face embeddings, and explicit user corrections. The system must not perform internet face recognition, compare local video frames/crops/embeddings against Yandex or web images, download adult media, download web images/thumbnails/leaked content, use repost/leak hosts as final identity authority, or infer legal names/private identity/age/location.

## Current-State Summary

The current Face Organizer is a local media sorter with three useful but uneven signal paths:

- Local face matching exists through InsightFace and `scripts/media/known_performers/`, but the current known face DB is tiny: one performer, `Sava Schultz`, with one embedding row.
- OCR/profile text evidence is the strongest current model naming source. The pipeline scans watermark-heavy frame regions and parses profile handles such as `OnlyFans.com/<handle>`, `Fansly.com/<handle>`, `Fanvue.com/<handle>`, `@handle`, and `stolen/leaked/from` patterns.
- Registry/model cleanup exists through `performer_verification.json`, `model_index.json`, aliases, trusted profile handles, and `verify_performers`.

Current artifact snapshot from local diagnostics:

- `scripts/media/performer_verification.json`: 37 performers, 46 aliases, source dir `/DATA/yes`, `online_metadata_requested=false`.
- `scripts/media/model_index.json`: 37 models: 7 `user-confirmed`, 9 `local-auto`, 21 `profile-url`.
- `scripts/media/known_performers/index.json`: one performer, `Sava Schultz`.
- `scripts/media/known_performers/performer_map.json`: one embedding row.
- `scripts/media/face_verification_report.html`: stale relative to current code; 15 needs-review cards; contains `407017_720p.mp4`; does not yet include newly patched manual text verification links.

## Evidence Map

Face Organizer files:

- `scripts/media/face_organizer.py:84` - scan exclusions, confidence thresholds, defaults.
- `scripts/media/face_organizer.py:275` - optional pAPI/RapidAPI lookup hook.
- `scripts/media/face_organizer.py:318` - OCR region crop generation.
- `scripts/media/face_organizer.py:359` - RapidOCR execution.
- `scripts/media/face_organizer.py:585` - watermark/profile candidate parsing.
- `scripts/media/face_organizer.py:647` - metadata hint assembly.
- `scripts/media/face_organizer.py:690` - local known performer DB.
- `scripts/media/face_organizer.py:786` - face match threshold classification.
- `scripts/media/face_organizer.py:805` - seed aliases.
- `scripts/media/face_organizer.py:856` - trusted profile handles.
- `scripts/media/face_organizer.py:938` - extracted profile handles from hints.
- `scripts/media/face_organizer.py:1113` - combined watermark/face identity decision.
- `scripts/media/face_organizer.py:1177` - InsightFace recognizer.
- `scripts/media/face_organizer.py:1236` - video discovery.
- `scripts/media/face_organizer.py:1293` - ffmpeg frame extraction.
- `scripts/media/face_organizer.py:1327` - face rejection rules.
- `scripts/media/face_organizer.py:1341` - performer aggregation from face observations.
- `scripts/media/face_organizer.py:1424` - per-video scan.
- `scripts/media/face_organizer.py:1525` - batch scan.
- `scripts/media/face_organizer.py:1572` - sidecar metadata collection.
- `scripts/media/face_organizer.py:1696` - metadata enrichment.
- `scripts/media/face_organizer.py:1854` - organization/move logic.
- `scripts/media/face_organizer.py:1921` - performer verification and model index rebuild.
- `scripts/media/face_organizer.py:2062` - review frame backfill.
- `scripts/media/face_organizer.py:2140` - manual text verification link generation.
- `scripts/media/face_organizer.py:2181` - HTML report rendering.
- `scripts/media/face_organizer.py:2407` - add confirmed performer from crop.
- `scripts/media/face_organizer.py:2428` - CLI modes and flags.

Existing diagnostic docs:

- `scripts/media/face_organizer_system_diag.md` - compact system diagnostic.
- `scripts/media/face_organizer_context_packet.xml` - compact XML context packet.

Existing search-adjacent reusable code:

- `scripts/mac-worker/spirit_mac_worker.py:175` - Scout research packet dispatch.
- `scripts/mac-worker/spirit_mac_worker.py:247` - `web_search_packet`.
- `scripts/mac-worker/spirit_mac_worker.py:331` - SearXNG provider URL selection using `SPIRIT_MAC_SEARXNG_URL`.
- `scripts/mac-worker/spirit_mac_worker.py:338` - SearXNG search URL builder.
- `scripts/mac-worker/spirit_mac_worker.py:350` - result normalization into title/url/snippet/provider.
- `scripts/mac-worker/spirit-mac-worker.mjs:233` - JS equivalent `webSearchPacket`.
- `scout/src/scout/sources/search.py:28` - `run_searxng_search`.
- `scout/src/scout/sources/search.py:113` - normalized search result sources.
- `scout/src/scout/sources/search_candidates.py:18` - bounded candidate extraction from search results.
- `scout/src/scout/api/source_trust.py:51` - source trust classification.
- `scout/src/scout/tests/test_search_provider.py:6` - SearXNG search provider tests.

## What Is Already Integrated

- Local frame sampling with `ffmpeg`.
- Local face detection/embedding through InsightFace.
- Local known-performer DB.
- Face crop and review frame persistence when `--apply`.
- OCR over multiple watermark-heavy frame regions.
- OCR text parsing for profile URLs, handles, and `from/stolen/leaked` text.
- Noise filtering for host/repost/generic junk.
- Seed aliases and canonicalization.
- Profile handle extraction for OnlyFans/Fansly/Fanvue text.
- `performer_verification.json` registry.
- `model_index.json` for SpiritFlix.
- Moving eligible records to `/DATA/yes/models/<slug>/` and unresolved records to `/DATA/yes/unknown/`.
- HTML review report.
- Manual report-side search links in code for Yandex, Yandex `site:pimpbunny.com`, Yandex `site:coomer.st`, and Coomer.

## What Is Not Integrated

- No live Yandex/private/Mac/browser text search is run by Face Organizer batches.
- No text web evidence schema is persisted in sidecars, registry, or model index.
- No Face Organizer provider abstraction exists for search results.
- No configured trust-tier list exists for model-verification domains.
- `verify_performers(enable_online=True)` only records the flag; it does not enrich web evidence.
- pAPI is present but optional and not the primary desired route.
- The report does not yet show durable web evidence cards, identity traces, or "why this name?" explanations.
- The report only shows needs-review records, not all records.
- Confirmed-crop enrollment exists as a CLI action, but the review-to-enroll workflow is not hardened with explicit audit and guardrails.

## Non-Goals And Boundaries

- No internet face recognition.
- No comparison of local faces/crops/embeddings against Yandex or web images.
- No adult media or web image downloads.
- No screenshot capture except later approved screenshots of text search results only.
- No repost/leak/index site can be final identity authority by itself.
- No legal/private identity inference.
- No automatic trust from filename-only or weak OCR.
- No media move, rename, delete, or organization without explicit approved `--apply`.
- No git branch, stash, reset, checkout, clean, stage, commit, push, or PR action under this plan.

## Target Architecture

Target pipeline:

1. Local face signal layer.
   - Extract frames.
   - Detect faces.
   - Compare embeddings only against `known_performers`.
   - User-confirmed local face match `>= 0.80` can auto assign.
   - Possible local match goes to review.
2. Local text signal layer.
   - OCR profile URLs and watermark-heavy regions.
   - Parse handles, names, filename/folder hints.
   - Build normalized candidate objects with provenance.
3. Text-only web evidence layer.
   - Generate queries from candidates.
   - Use provider abstraction for Yandex URL generation, SearXNG/Mac worker search packets, site-scoped searches, configured domains, and optional pAPI.
   - Store title/url/snippet/query/provider/timestamp/matched handle/name/trust/confidence.
   - Never fetch/download media/images for identity matching.
4. Evidence scoring layer.
   - Build `identity_trace`.
   - Score explainable chains.
   - Write `assignment_decision`.
5. Review/report layer.
   - Display evidence trace and source trust.
   - Provide command snippets for approve/reject/enroll.
   - Support all-records audit.
6. Confirmed enrollment layer.
   - Britton confirms a crop and public/stage name/handle.
   - Add embedding to `known_performers`.
   - Update registry audit trail.
   - Future batches rely more on local DB.

## Data Schema Target

Sidecars should remain backward compatible. New fields should be optional and additive.

`web_text_evidence[]`:

- `provider`
- `query`
- `url`
- `title`
- `snippet`
- `matched_handle`
- `matched_name`
- `source_domain`
- `source_trust_level`
- `collected_at`
- `confidence`
- `review_required`
- `evidence_role`
- `limitations`
- `unsafe_untrusted_content`

`identity_trace[]`:

- `signal_type`: `local_face`, `watermark_profile_url`, `ocr_handle`, `filename_hint`, `web_text`, `user_confirmed`
- `value`
- `source`
- `confidence`
- `reason`
- `review_required`
- `source_path`

`assignment_decision`:

- `suggested_slug`
- `suggested_name`
- `confidence`
- `auto_assign_allowed`
- `review_required`
- `why`
- `blocking_reasons`
- `supporting_signal_ids`

Registry additions:

- `web_text_evidence_summary`
- `identity_trace_summary`
- `confirmed_by`
- `confirmed_at`
- `enrolled_face_samples`
- `audit_events[]`

Model index additions:

- `assignment_status`
- `identity_confidence`
- `primary_evidence_role`
- `profile_handles`
- `review_required`
- `why`

## Confidence Scoring Target

Base signals:

- Local user-confirmed face match `>= 0.80`: high confidence and eligible for auto assign.
- Full in-video profile URL/watermark handle: high confidence when parsed cleanly.
- OCR handle without full profile URL: medium until corroborated.
- OCR handle plus matching text evidence: medium/high depending on exactness and source trust.
- Search result text alone: review by default.
- Filename/folder hint: weak.
- Repost/index site: corroboration only.
- User confirmation: authoritative for registry/canonicalization and enrollment.

Auto assignment requires:

- Explainable evidence chain.
- No host/repost/generic candidate as final name.
- No contradiction between local face and text signals.
- Confidence `>= 0.80`.
- `auto_assign_allowed=true` with `why`.

Review required when:

- Local face match is possible but below auto threshold.
- OCR is noisy or ambiguous.
- Evidence comes only from search result text.
- Source trust is low.
- Multiple names/handles compete.
- No full profile URL or local confirmed face exists.

## Mac/Yandex Text-Search Target

Search must be text-only. It may collect result titles/snippets/URLs and optionally text-result screenshots after approval. It must not download web images, thumbnails, videos, or compare faces.

Provider design:

- `YandexUrlProvider`: deterministic URL generation for manual review; no network call required.
- `YandexSiteScopedProvider`: deterministic URLs for `site:pimpbunny.com`, `site:coomer.st`, and user-configured domains.
- `SearxngProvider`: reuse Scout/Mac worker style JSON search where configured.
- `MacWorkerSearchProvider`: optional adapter over `scripts/mac-worker` `web_search_packet`.
- `ConfiguredDomainProvider`: handles direct search URL templates or site-scoped query generation for Britton-provided domains.
- `PapiProvider`: optional metadata provider, separate from main text evidence route.

Required query patterns:

- `"<candidate handle>" onlyfans`
- `"<candidate name>" onlyfans`
- `site:pimpbunny.com "<candidate>"`
- `site:coomer.st "<candidate>"`
- `site:<configured-domain> "<candidate>"`
- exact profile handle variants from OCR slash text.

Provider result rules:

- Store query, provider, URL, title, snippet, matched handle/name, timestamp, source domain, trust tier, confidence, and review flag.
- Mark external snippets as untrusted content.
- Do not execute instructions from snippets/pages.
- Do not promote repost/leak domains to final authority without in-video evidence.

## Report/UI Target

Report should support:

- Current review queue mode.
- All records audit mode.
- "Why this name?" trace.
- Local face confidence and crop path.
- OCR candidates with raw text/region/frame.
- Generated search queries.
- Web evidence cards with source trust labels.
- Source-trust tier: official/profile, creator-profile, configured-corroborator, repost-index, unknown.
- Clear status labels: `auto`, `local-auto`, `profile-url`, `web-suggested`, `user-confirmed`, `needs-review`.
- Approve/reject command snippets.
- Enroll confirmed crop command.
- Explicit warnings for untrusted snippets and non-authoritative repost/index sources.

## Confirmed-Crop Enrollment Target

Enrollment must be explicit and auditable.

Required workflow:

1. Report shows candidate crop and source frame.
2. Britton confirms public/stage name and optional handles/profile URLs.
3. Command adds performer embedding through `--add-performer`.
4. Registry records `user_confirmed`, `confirmed_at`, aliases, handles, and enrollment sample path.
5. Re-run scan/verify on a small sample.
6. Confirm local DB count increased.
7. Confirm future matching uses local DB and does not require web evidence when confidence is strong.

Safety rules:

- Never enroll from weak/unclear crop.
- Never enroll from web image.
- Never enroll without explicit user confirmation.
- Keep audit trail.

## Rollback And Manifest Rules

- No media moves in Plans 0-6.
- Plan 7 dry-run must prove no media moves.
- Any future `--apply` must create backup manifests first.
- Organization changes must write `organize_manifest.json`.
- Sidecar schema changes must be backward compatible and parse old sidecars.
- Registry/model index writes must be preceded by read-only JSON parse and small-sample dry run.
- Any failed apply must produce a closeout with changed files, manifests, and rollback path.
- No git mutation is part of this plan.

## Test Plan

Required tests by the relevant phase:

- Python compile: `python -m py_compile scripts/media/face_organizer.py`.
- JSON parse: registry, model index, known performer index/map, representative sidecars.
- XML parse if XML packets are written.
- Unit tests for OCR candidate parsing.
- Unit tests for profile URL slash handle extraction.
- Unit tests for candidate dedupe/ranking.
- Unit tests for query generation.
- Unit tests for provider normalization and source-trust mapping.
- Unit tests for scorer decisions.
- Backward compatibility with existing sidecars.
- Report render smoke.
- No media moves in dry-run.
- Explicit approval required before organizer `--apply`.

## Plan 0 - Dell Report Refresh And Current-State Lock

Goal: Refresh the stale Dell report and capture exact current system state before any integration.

Increment 0.1 - Inspect current state.

- Inspect repo status without mutation.
- Inspect current media artifacts and timestamps.
- Inspect current report timestamp and whether `Text verification links` render.
- Inspect `known_performers` DB count and embedding rows.
- Inspect registry/model index counts.
- Evidence commands:
  - `git status --short -- scripts/media/face_organizer.py scripts/media/performer_verification.json scripts/media/model_index.json scripts/media/known_performers`
  - JSON parse/count scripts only.
  - `Select-String` or `grep` for `Text verification links`.

Acceptance:

- Exact current counts recorded.
- Stale/fresh report status recorded.
- No media files moved or changed.

Pause gate: Stop after 0.1 closeout if SSH/Dell access is blocked.

Increment 0.2 - Regenerate the report on Dell.

Allowed diagnostic command only:

```bash
cd /home/source/SpiritOS
. .venv-face-organizer/bin/activate
python scripts/media/face_organizer.py --source /DATA/yes --report --ctx-id -1
```

Acceptance:

- `scripts/media/face_verification_report.html` timestamp updates.
- No sidecars, registry, model index, or media moves are produced by this command.

Pause gate: Stop and report if the command fails.

Increment 0.3 - Verify new manual links render.

- Check report HTML for `Text verification links`.
- Check `407017_720p.mp4` has Yandex/Coomer/PimpBunny manual text links if its hints remain present.
- Check served report URL if server is already running.
- Do not start or restart services unless separately approved.

Acceptance:

- Report contains link section.
- Link URLs are text-search URLs only.
- No web search execution is required.

Pause gate: Stop if link rendering is missing.

Increment 0.4 - Write Plan 0 closeout evidence.

- Record commands run, timestamps, changed generated files, and state counts.
- Mark Plan 0 `PASS` or `NEEDS_FIX`.

Pause gate: Stop and ask Britton before Plan 1.

## Plan 1 - Durable Evidence Schema

Goal: Add durable sidecar/registry/model_index fields for web text evidence and identity reasoning without changing organizer behavior yet.

Increments:

- 1.1 Define additive schema constants/types and migration helpers.
- 1.2 Add backward-compatible readers for optional `web_text_evidence`, `identity_trace`, and `assignment_decision`.
- 1.3 Write schema-only unit tests using current sidecars.
- 1.4 Add no-behavior-change closeout.

Acceptance:

- Existing sidecars still load.
- No media moves.
- No web calls.
- No scoring behavior changes.
- Tests prove backward compatibility.

Pause gate: Stop and ask Britton before Plan 2.

## Plan 2 - OCR Candidate Cleanup And Search Query Builder

Goal: Improve candidate quality before any web search.

Increments:

- 2.1 Define normalized candidate object with source, raw text, region, confidence, variants, and evidence role.
- 2.2 Improve profile slash extraction for OnlyFans, Fansly, Fanvue, `@handle`, and `from/stolen/leaked`.
- 2.3 Add OCR variant generation for noisy examples.
- 2.4 Add dedupe/ranking and host/repost/generic noise filters.
- 2.5 Add query builder with no live web calls.
- 2.6 Add fixtures for `407017_720p.mp4` OCR hints.

Acceptance:

- Query builder returns deterministic text queries only.
- No provider calls.
- No behavior change to organization.
- No media moves.

Pause gate: Stop and ask Britton before Plan 3.

## Plan 3 - Text-Only Web Evidence Provider Abstraction

Goal: Design and implement provider abstraction for text evidence only.

Increments:

- 3.1 Add provider interface returning normalized title/url/snippet records.
- 3.2 Add deterministic Yandex URL generation provider.
- 3.3 Add Yandex site-scoped URL generation provider.
- 3.4 Add configured-domain query provider.
- 3.5 Evaluate reuse of Mac worker `web_search_packet` and Scout/SearXNG normalizers.
- 3.6 Add optional pAPI adapter as separate metadata provider.
- 3.7 Add provider tests with mocked results only.

Provider rules:

- Metadata only.
- No media download.
- No web-image face matching.
- No frame-to-web-image comparison.
- No automatic trust from repost sites.
- User-configured source list with trust tiers.

Acceptance:

- Provider dry-run returns query URLs or mocked normalized results.
- No live search unless Britton separately approves.
- No sidecar writes until Plan 1 schema is accepted.

Pause gate: Stop and ask Britton before Plan 4.

## Plan 4 - Evidence Scorer And Auto-Assignment Policy

Goal: Create explainable scoring rules.

Increments:

- 4.1 Implement scorer inputs from local face, watermark profile URL, OCR handle, filename hint, web text, and user confirmation.
- 4.2 Encode auto/review policy.
- 4.3 Add contradiction checks.
- 4.4 Write `assignment_decision.why`.
- 4.5 Add scorer tests.

Required policy:

- Local user-confirmed known face match `>= 0.80` can auto assign.
- Full in-video profile URL/watermark handle is high confidence.
- OCR handle plus matching web text can become high confidence only if trace is explainable.
- Search result text alone usually means review unless paired with in-video handle/profile evidence.
- Filename hints are weak.
- Repost/index sites are corroboration only.
- Host names must never become model names.
- Weak OCR remains unknown/review.
- Every auto assignment must write why.

Acceptance:

- All auto decisions have trace and reason.
- Weak/noisy cases remain review.
- Tests cover positive, weak, contradiction, and host-name cases.

Pause gate: Stop and ask Britton before Plan 5.

## Plan 5 - Report UI And Audit Report

Goal: Make the report useful for real review.

Increments:

- 5.1 Add "why this name?" trace rendering.
- 5.2 Add local face confidence and crop/source-frame visibility.
- 5.3 Add OCR candidate and query sections.
- 5.4 Add web text evidence cards with trust labels.
- 5.5 Add approve/reject/enroll command snippets.
- 5.6 Add all-records mode.
- 5.7 Add report render smoke test.

Acceptance:

- Report clearly separates auto, profile-url, user-confirmed, local-auto, web-suggested, and needs-review.
- Evidence cards are text-only and marked untrusted where appropriate.
- UI does not imply repost sites are final authority.
- No media moves.

Pause gate: Stop and ask Britton before Plan 6.

## Plan 6 - Confirmed-Crop Enrollment Workflow

Goal: Grow `known_performers` safely from Britton-approved crops.

Increments:

- 6.1 Harden add-performer command generation in report.
- 6.2 Add explicit alias/handle/profile URL recording.
- 6.3 Add audit trail in registry.
- 6.4 Add safeguards against wrong/empty crops.
- 6.5 Add tests around enrollment metadata and DB count checks.

Acceptance:

- Requires explicit user confirmation.
- Adds performer from local crop only.
- Records audit trail.
- Rebuild/verify local DB count.
- No web identity inference.

Pause gate: Stop and ask Britton before Plan 7.

## Plan 7 - Dry-Run Batch, Then Small Apply Batch

Goal: Run a controlled test only after all previous gates pass.

Sequence:

- 7.1 Dry-run scan/evidence collection on a small sample.
- 7.2 Verify no media moves.
- 7.3 Review evidence report.
- 7.4 Britton approval.
- 7.5 Small apply batch only after approval.
- 7.6 Verify organize manifest, sidecars, registry, model index, and report.
- 7.7 Produce closeout with `PASS` or `NEEDS_FIX`.

Acceptance:

- Dry-run proves no media movement.
- Apply is small, bounded, and approved.
- All generated manifests parse.
- Model index and registry match expected counts.
- Report shows evidence and decisions.

Pause gate: Stop before any larger batch.

## Overall Acceptance Criteria

- Face Organizer remains preservation-first.
- Existing sidecars remain readable.
- Local confirmed face matching works and grows safely.
- OCR/profile text candidates are cleaner and explainable.
- Text-only web evidence is durable and auditable.
- No internet face recognition occurs.
- No web images/media are downloaded or compared.
- Auto assignments require explainable confidence `>= 0.80`.
- Report shows clear review actions and trust labels.
- Every phase has a closeout and Britton approval before the next phase.
