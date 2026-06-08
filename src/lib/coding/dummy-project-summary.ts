import { DUMMY_CODER_10_FIXTURE_ROOT } from "@/lib/coding/dummy-coder-10-prompts";

export type DummyProjectFeatureFlags = {
  hasProductData?: boolean;
  hasProductCards?: boolean;
  hasSearch?: boolean;
  hasCategoryFilters?: boolean;
  hasCartCount?: boolean;
  hasSmokeTests?: boolean;
};

export type DummyProjectSummaryInput = {
  files: string[];
  features?: DummyProjectFeatureFlags;
  importedIntoSpiritOS?: boolean;
};

const starterFiles = [
  "README.md",
  "package.json",
  "index.html",
  "src/main.js",
  "src/products.js",
  "src/styles.css",
] as const;

function normalizePath(path: string) {
  return path.replace(/\\/g, "/").replace(/^\.\//, "");
}

function relativeDummyFile(path: string) {
  const normalized = normalizePath(path);
  if (normalized.startsWith(DUMMY_CODER_10_FIXTURE_ROOT)) {
    return normalized.slice(DUMMY_CODER_10_FIXTURE_ROOT.length);
  }
  return normalized;
}

function fileListSentence(files: string[]) {
  const unique = [...new Set(files.map(relativeDummyFile).filter(Boolean))].sort();
  if (unique.length === 0) return "no detected files";
  if (unique.length === 1) return unique[0];
  if (unique.length <= 8) return `${unique.slice(0, -1).join(", ")}, and ${unique.at(-1)}`;
  return `${unique.slice(0, 8).join(", ")}, and ${unique.length - 8} more files`;
}

function featureList(features: DummyProjectFeatureFlags) {
  const names = [
    features.hasProductData ? "fake product data" : "",
    features.hasProductCards ? "product card rendering" : "",
    features.hasSearch ? "search" : "",
    features.hasCategoryFilters ? "category filters" : "",
    features.hasCartCount ? "a local cart count" : "",
    features.hasSmokeTests ? "smoke tests" : "",
  ].filter(Boolean);
  if (names.length === 0) return "";
  return names.join(", ");
}

export function buildExistingDummyProjectSummary(input: DummyProjectSummaryInput) {
  const files = input.files.map(normalizePath);
  const dummyFiles = files.filter((file) => file.startsWith(DUMMY_CODER_10_FIXTURE_ROOT));
  const relativeFiles = dummyFiles.map(relativeDummyFile);
  const exists = dummyFiles.length > 0;
  const hasAllStarterFiles = starterFiles.every((file) => relativeFiles.includes(file));
  const importStatus = input.importedIntoSpiritOS
    ? "Import status is flagged for review because a SpiritOS import was reported."
    : "It is not reported as imported into SpiritOS.";

  if (!exists) {
    return `LumaCart is not present under ${DUMMY_CODER_10_FIXTURE_ROOT}. ${importStatus}`;
  }

  const features = featureList(input.features ?? {});
  if (features) {
    return `LumaCart exists under ${DUMMY_CODER_10_FIXTURE_ROOT} with ${features}. ${importStatus}`;
  }

  if (hasAllStarterFiles) {
    return `LumaCart exists under ${DUMMY_CODER_10_FIXTURE_ROOT} with ${fileListSentence([...starterFiles])}. ${importStatus}`;
  }

  return `LumaCart exists under ${DUMMY_CODER_10_FIXTURE_ROOT} with ${fileListSentence(dummyFiles)}. ${importStatus}`;
}
