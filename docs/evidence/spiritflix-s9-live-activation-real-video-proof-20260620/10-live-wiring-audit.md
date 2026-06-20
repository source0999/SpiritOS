# Live Wiring Audit

- Batch Analyze reaches `runSpiritFlixSmartBatch`, which calls `runSpiritFlixSmartReviewPipeline` with `force:true` for refreshed items.
- The scanner writes sampled frames through `extractSpiritFlixFrameSample` under `.spiritflix-admin/analysis-cache/frames`.
- `runSpiritFlixSmartReviewPipeline` calls `applyLocalVisualAnalysisToSpiritFlixAnalysis`, which sends cached frames to local Ollama and writes VLM tags to sample tags, `contentTagEvidence`, and now `visualAnalysis`.
- `updateSmartAnalysisWithHeuristicSuggestions` promotes primary frame/VLM tags into `suggestedTags` and now mirrors them to `pendingSmartTags` plus `pendingDisplayName`.
- The smart batch API returns `items[].tags`, `visualTaggingAvailable`, and `proposedFilename`; the batch panel renders `item.tags` in Smart Tags and keeps technical tags in Quality/technical.
- The review panel calls `confirmMetadata`, which writes approved metadata sidecars through `writeApprovedSmartMetadataSidecar`.
- Old sidecars can mask S9 results when the row is `already_current`; `Analyze/refresh item` or `force:true` is required to refresh stale rows.
- The observed empty HTTP probe was transport mismatch: the live Next app on port 3000 is HTTPS-only. HTTPS API probes work.
- Live bug found and fixed: source-spam filenames like `Visit onlyshare.io for MORE 130.mkv` were treated as readable, so recommended names ignored visual tags. They now fall back to `Model - visual tags 01`.

Raw source/probe evidence: raw/10-audit-source-snapshot.txt and raw/10-live-route-probe.txt
