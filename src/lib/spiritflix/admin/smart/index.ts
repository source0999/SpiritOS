// ── SpiritFlix Smart Tagging S1+S2+S3 public surface ─────────────────
// Scanner + heuristic suggestion lanes. No Level 2 action imports.

export {
  SPIRITFLIX_SMART_ANALYSIS_DIR,
  SPIRITFLIX_SMART_ANALYSIS_CACHE_DIR,
  SPIRITFLIX_SMART_ADMIN_SUBDIR,
  assertSmartAnalysisPathMatchesInput,
  assertSmartAnalysisPathSafe,
  assertSmartVideoPathCandidate,
  createSmartAnalysisPathKey,
  getSmartAnalysisCacheRoot,
  getSmartAnalysisPath,
  getSmartAnalysisRoot,
  normalizeSmartVideoPath,
  type SpiritFlixSmartPathInput,
  type SpiritFlixSmartPathOptions,
} from "./analysis-paths";

export {
  SPIRITFLIX_SMART_ANALYZER_VERSION_S1,
  createEmptySmartAnalysis,
  readSmartAnalysis,
  writeSmartAnalysis,
  type CreateEmptySmartAnalysisInput,
} from "./analysis-store";

export {
  SpiritFlixSmartProbeError,
  SpiritFlixSmartSamplerError,
  SpiritFlixSmartScannerError,
} from "./errors";

export {
  SPIRITFLIX_SMART_VIDEO_EXTENSIONS,
  isSpiritFlixSmartVideoExtension,
  parseFfprobeJson,
  parseRationalFrameRate,
  probeSpiritFlixVideo,
  type SpiritFlixProbeOptions,
  type SpiritFlixProbeResult,
} from "./probe";

export {
  buildSpiritFlixFrameCacheFileName,
  extractSpiritFlixFrameSample,
  getSpiritFlixFrameCachePath,
  planSpiritFlixSampleTimestamps,
  type SpiritFlixFrameExtractionOptions,
  type SpiritFlixFrameSample,
  type SpiritFlixSamplePlanOptions,
} from "./sampler";

export {
  SPIRITFLIX_SMART_ANALYZER_VERSION_S2,
  scanOneSpiritFlixVideoEvidence,
  type SpiritFlixScanOneVideoOptions,
} from "./scanner";

export {
  buildHeuristicNotes,
  inferCategoryHint,
  inferFormatTags,
  inferPerformerTags,
  inferQualityTags,
  inferSourceTags,
  inferSourceTokens,
  isAmbiguousSpiritFlixFilename,
  normalizeSpiritFlixTitle,
  stripKnownNoiseTokens,
  tokenizeSpiritFlixName,
  type SpiritFlixSmartHeuristicInput,
} from "./heuristics";

export {
  SPIRITFLIX_SMART_ANALYZER_VERSION_S3,
  applySpiritFlixReviewSuggestionsToAnalysis,
  buildSpiritFlixReviewSuggestions,
  buildSuggestedFilename,
  updateSmartAnalysisWithHeuristicSuggestions,
  type SpiritFlixSmartSuggestionResult,
} from "./suggestions";

export {
  SPIRITFLIX_SMART_ANALYZER_VERSION_S4,
  markSpiritFlixSmartAnalysisReviewed,
  runSpiritFlixSmartReviewPipeline,
  saveSpiritFlixSmartAnalysisReview,
  type SpiritFlixSmartReviewOptions,
} from "./review";

export {
  SPIRITFLIX_SMART_ANALYZER_VERSION_S5,
  applySmartReviewToAnalysis,
  assertSpiritFlixSmartReviewPayload,
  buildEmptyReviewDraft,
  countReviewTagStates,
  sanitizeEditedFilenameSuggestion,
  tagReviewState,
  validateSpiritFlixSmartReviewInput,
} from "./review-metadata";

export {
  SMART_ANALYSIS_LIMITS,
  parseSpiritFlixSmartAnalysisJson,
  validateSpiritFlixSmartAnalysis,
  validateSpiritFlixSmartReviewedMetadata,
  validateSpiritFlixSmartSample,
  validateSpiritFlixSmartTag,
  type SpiritFlixSmartAnalysis,
  type SpiritFlixSmartConfidenceBand,
  type SpiritFlixSmartReviewInput,
  type SpiritFlixSmartReviewStatus,
  type SpiritFlixSmartReviewedMetadata,
  type SpiritFlixSmartSample,
  type SpiritFlixSmartStatus,
  type SpiritFlixSmartTag,
  type SpiritFlixSmartTagGroup,
} from "./types";

export {
  confidenceBand,
  findSmartTagDefinition,
  getSmartTagVocabulary,
  isKnownSmartTagId,
  normalizeSmartTagId,
  tagDefinitionRequiresReviewByPolicy,
  type SpiritFlixSmartTagDefinition,
} from "./vocabulary";

export {
  metadataSidecarPath,
  projectApprovedSmartMetadata,
  writeApprovedSmartMetadataSidecar,
  type SpiritFlixApprovedMetadataProjection,
} from "./metadata-bridge";

export {
  buildSmartRenamePreviewDraft,
  type SpiritFlixSmartRenamePreviewDraft,
  type SpiritFlixSmartRenamePreviewInput,
} from "./rename-preview";

export {
  previewSpiritFlixSmartBatch,
  reviewSpiritFlixSmartBatch,
  runSpiritFlixSmartBatch,
  type SpiritFlixSmartBatchCounts,
  type SpiritFlixSmartBatchItem,
  type SpiritFlixSmartBatchItemStatus,
  type SpiritFlixSmartBatchOptions,
  type SpiritFlixSmartBatchPreview,
  type SpiritFlixSmartBatchReviewMode,
  type SpiritFlixSmartBatchReviewOptions,
} from "./batch";

export {
  buildSpiritFlixSmartRenamePlan,
  type SpiritFlixSmartRenamePlan,
  type SpiritFlixSmartRenamePlanCounts,
  type SpiritFlixSmartRenamePlanItem,
  type SpiritFlixSmartRenamePlanItemStatus,
  type SpiritFlixSmartRenamePlanOptions,
} from "./rename-plan";
