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
  SMART_ANALYSIS_LIMITS,
  parseSpiritFlixSmartAnalysisJson,
  validateSpiritFlixSmartAnalysis,
  validateSpiritFlixSmartSample,
  validateSpiritFlixSmartTag,
  type SpiritFlixSmartAnalysis,
  type SpiritFlixSmartConfidenceBand,
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
