import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { SPIRITFLIX_MEDIA_ROOT } from "./admin/constants";
import { writeSpiritFlixAdminReceipt } from "./admin/receipts";

export const SPIRITFLIX_MANUAL_MODEL_SCHEMA = "spiritflix-manual-model/v1";
export const SPIRITFLIX_MANUAL_MODEL_INDEX_SCHEMA = "spiritflix-manual-model-index/v1";
export const SPIRITFLIX_MANUAL_MODELS_ROOT = path.join(SPIRITFLIX_MEDIA_ROOT, ".spiritflix-admin", "metadata", "manual-models");

export interface SpiritFlixManualModelRecord {
  schema: typeof SPIRITFLIX_MANUAL_MODEL_SCHEMA;
  itemId: string;
  filePath?: string;
  modelName: string;
  updatedAt: string;
  source: "manual";
  createdBy?: "local-user";
}

export interface SpiritFlixManualModelSummary {
  modelName: string;
  count: number;
}

export interface SpiritFlixManualModelIndex {
  schema: typeof SPIRITFLIX_MANUAL_MODEL_INDEX_SCHEMA;
  updatedAt: string;
  models: SpiritFlixManualModelSummary[];
}

export interface SpiritFlixManualModelStoreOptions {
  rootDir?: string;
  modelIndexPath?: string;
  lookupFilePath?: string;
}

export interface SetSpiritFlixManualModelInput {
  itemId: string;
  filePath?: string;
  modelName: string;
  knownModelNames?: string[];
}

function getManualModelRoot(options: SpiritFlixManualModelStoreOptions = {}): string {
  return options.rootDir ?? process.env.SPIRITFLIX_MANUAL_MODEL_ROOT ?? SPIRITFLIX_MANUAL_MODELS_ROOT;
}

function getManualModelIndexPath(options: SpiritFlixManualModelStoreOptions = {}): string {
  return path.join(getManualModelRoot(options), "index.json");
}

function getKnownModelIndexPath(options: SpiritFlixManualModelStoreOptions = {}): string {
  return options.modelIndexPath ?? process.env.SPIRITFLIX_MODEL_INDEX_PATH ?? path.join(process.cwd(), "scripts", "media", "model_index.json");
}

export function canonicalizeSpiritFlixManualModelName(input: unknown): string {
  if (typeof input !== "string") return "";
  return input.trim().replace(/\s+/g, " ");
}

function getModelNameKey(input: string): string {
  return canonicalizeSpiritFlixManualModelName(input).toLowerCase();
}

function getCompactModelNameKey(input: string): string {
  return getModelNameKey(input).replace(/[^a-z0-9]+/g, "");
}

function getFilePathKey(input: unknown): string {
  return typeof input === "string" ? input.trim().replace(/\\/g, "/").toLowerCase() : "";
}

interface SpiritFlixKnownModelIndex {
  models?: Array<{
    name?: unknown;
    slug?: unknown;
    aliases?: unknown;
    profile_handles?: unknown;
  }>;
}

function addKnownModelAlias(aliasMap: Map<string, string>, alias: unknown, canonicalName: string): void {
  if (typeof alias !== "string") return;
  const key = getModelNameKey(alias);
  if (key && !aliasMap.has(key)) aliasMap.set(key, canonicalName);
  const compactKey = getCompactModelNameKey(alias);
  if (compactKey && !aliasMap.has(compactKey)) aliasMap.set(compactKey, canonicalName);
}

async function getKnownModelAliasMap(options: SpiritFlixManualModelStoreOptions = {}): Promise<Map<string, string>> {
  const aliasMap = new Map<string, string>();
  const modelIndex = await readJsonFile<SpiritFlixKnownModelIndex>(getKnownModelIndexPath(options));
  for (const model of modelIndex?.models ?? []) {
    const canonicalName = canonicalizeSpiritFlixManualModelName(model.name);
    if (!canonicalName) continue;
    addKnownModelAlias(aliasMap, model.name, canonicalName);
    addKnownModelAlias(aliasMap, model.slug, canonicalName);
    if (Array.isArray(model.aliases)) {
      model.aliases.forEach((alias) => addKnownModelAlias(aliasMap, alias, canonicalName));
    }
    if (Array.isArray(model.profile_handles)) {
      model.profile_handles.forEach((profile) => {
        if (!profile || typeof profile !== "object") return;
        addKnownModelAlias(aliasMap, (profile as { handle?: unknown }).handle, canonicalName);
      });
    }
  }
  return aliasMap;
}

function resolveKnownModelName(modelName: string, knownModelNames: string[] = [], aliasMap: Map<string, string> = new Map()): string {
  const key = getModelNameKey(modelName);
  const aliasCanonical = aliasMap.get(key) ?? aliasMap.get(getCompactModelNameKey(modelName));
  if (aliasCanonical) return aliasCanonical;
  const compactKey = getCompactModelNameKey(modelName);
  return knownModelNames.find((candidate) => getModelNameKey(candidate) === key || getCompactModelNameKey(candidate) === compactKey) ?? modelName;
}

function assertManualModelItemId(itemId: string): string {
  const normalized = itemId.trim();
  if (!normalized) throw new Error("Manual model item id is required.");
  return normalized;
}

function getManualModelRecordPath(itemId: string, options: SpiritFlixManualModelStoreOptions = {}): string {
  const hash = createHash("sha256").update(assertManualModelItemId(itemId)).digest("hex");
  return path.join(getManualModelRoot(options), "items", `${hash}.json`);
}

async function readJsonFile<T>(filePath: string): Promise<T | null> {
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8")) as T;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return null;
    throw error;
  }
}

async function writeJsonFile(filePath: string, value: unknown): Promise<void> {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

export async function getSpiritFlixManualModelForItem(
  itemId: string,
  options: SpiritFlixManualModelStoreOptions = {},
): Promise<SpiritFlixManualModelRecord> {
  const normalizedItemId = assertManualModelItemId(itemId);
  const existing = await readJsonFile<SpiritFlixManualModelRecord>(getManualModelRecordPath(normalizedItemId, options));
  const aliasMap = await getKnownModelAliasMap(options);
  if (existing?.schema === SPIRITFLIX_MANUAL_MODEL_SCHEMA) {
    const modelName = canonicalizeSpiritFlixManualModelName(existing.modelName);
    return {
      ...existing,
      modelName: resolveKnownModelName(modelName, [], aliasMap),
    };
  }
  const lookupFilePath = getFilePathKey(options.lookupFilePath);
  if (lookupFilePath) {
    const fileMatchedRecord = (await listSpiritFlixManualModelRecords({ ...options, lookupFilePath: undefined }))
      .find((record) => getFilePathKey(record.filePath) === lookupFilePath);
    if (fileMatchedRecord) {
      return {
        ...fileMatchedRecord,
        itemId: normalizedItemId,
        modelName: resolveKnownModelName(fileMatchedRecord.modelName, [], aliasMap),
      };
    }
  }
  return {
    schema: SPIRITFLIX_MANUAL_MODEL_SCHEMA,
    itemId: normalizedItemId,
    modelName: "",
    updatedAt: new Date(0).toISOString(),
    source: "manual",
    createdBy: "local-user",
  };
}

export async function listSpiritFlixManualModelRecords(
  options: SpiritFlixManualModelStoreOptions = {},
): Promise<SpiritFlixManualModelRecord[]> {
  const itemsRoot = path.join(getManualModelRoot(options), "items");
  let entries: string[];
  try {
    entries = await fs.readdir(itemsRoot);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return [];
    throw error;
  }

  const records = await Promise.all(
    entries
      .filter((entry) => entry.endsWith(".json"))
      .map((entry) => readJsonFile<SpiritFlixManualModelRecord>(path.join(itemsRoot, entry))),
  );
  const aliasMap = await getKnownModelAliasMap(options);
  return records
    .filter((record): record is SpiritFlixManualModelRecord => Boolean(record?.schema === SPIRITFLIX_MANUAL_MODEL_SCHEMA))
    .map((record) => {
      const modelName = canonicalizeSpiritFlixManualModelName(record.modelName);
      return { ...record, modelName: resolveKnownModelName(modelName, [], aliasMap) };
    })
    .filter((record) => Boolean(record.modelName));
}

export async function buildSpiritFlixManualModelIndex(
  options: SpiritFlixManualModelStoreOptions = {},
): Promise<SpiritFlixManualModelIndex> {
  const counts = new Map<string, SpiritFlixManualModelSummary>();
  const records = await listSpiritFlixManualModelRecords(options);
  records.forEach((record) => {
    const key = getModelNameKey(record.modelName);
    const current = counts.get(key);
    counts.set(key, {
      modelName: current?.modelName ?? record.modelName,
      count: (current?.count ?? 0) + 1,
    });
  });
  const index: SpiritFlixManualModelIndex = {
    schema: SPIRITFLIX_MANUAL_MODEL_INDEX_SCHEMA,
    updatedAt: new Date().toISOString(),
    models: Array.from(counts.values()).sort((left, right) => right.count - left.count || left.modelName.localeCompare(right.modelName)),
  };
  await writeJsonFile(getManualModelIndexPath(options), index);
  return index;
}

export async function getSpiritFlixManualModelIndex(
  options: SpiritFlixManualModelStoreOptions = {},
): Promise<SpiritFlixManualModelIndex> {
  return buildSpiritFlixManualModelIndex(options);
}

export async function setSpiritFlixManualModelForItem(
  input: SetSpiritFlixManualModelInput,
  options: SpiritFlixManualModelStoreOptions = {},
): Promise<{ record: SpiritFlixManualModelRecord; previousModelName: string; index: SpiritFlixManualModelIndex }> {
  const itemId = assertManualModelItemId(input.itemId);
  const aliasMap = await getKnownModelAliasMap(options);
  const modelName = resolveKnownModelName(canonicalizeSpiritFlixManualModelName(input.modelName), input.knownModelNames, aliasMap);
  if (!modelName) throw new Error("Model name cannot be empty.");

  const previous = await getSpiritFlixManualModelForItem(itemId, options);
  const record: SpiritFlixManualModelRecord = {
    schema: SPIRITFLIX_MANUAL_MODEL_SCHEMA,
    itemId,
    filePath: input.filePath ?? previous.filePath,
    modelName,
    updatedAt: new Date().toISOString(),
    source: "manual",
    createdBy: "local-user",
  };

  await writeJsonFile(getManualModelRecordPath(itemId, options), record);
  const index = await buildSpiritFlixManualModelIndex(options);

  if (!options.rootDir && !process.env.SPIRITFLIX_MANUAL_MODEL_ROOT) {
    try {
      await writeSpiritFlixAdminReceipt({
        action: "manual-model:update",
        status: "executed",
        sourcePath: record.filePath,
        jellyfinItemIds: [itemId],
        affectedPaths: [getManualModelRecordPath(itemId, options), getManualModelIndexPath(options)],
        reason: JSON.stringify({
          itemId,
          previousModelName: previous.modelName,
          newModelName: record.modelName,
          updatedAt: record.updatedAt,
        }),
        reversible: true,
        rollbackHint: "Reapply previousModelName from receipt to the same item id.",
      });
    } catch {
      // Manual model metadata is the source of truth; receipt logging must not undo a successful save.
    }
  }

  return { record, previousModelName: previous.modelName, index };
}
