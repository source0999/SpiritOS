import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { SPIRITFLIX_MEDIA_ROOT } from "./admin/constants";
import { writeSpiritFlixAdminReceipt } from "./admin/receipts";
export {
  canonicalizeSpiritFlixManualTag,
  getSpiritFlixManualTagScope,
  type SpiritFlixManualTagScope,
} from "./manual-tag-scope";
import { canonicalizeSpiritFlixManualTag, getSpiritFlixManualTagScope } from "./manual-tag-scope";

export const SPIRITFLIX_MANUAL_TAG_SCHEMA = "spiritflix-manual-tags/v1";
export const SPIRITFLIX_MANUAL_TAG_INDEX_SCHEMA = "spiritflix-manual-tag-index/v1";
export const SPIRITFLIX_MANUAL_TAGS_ROOT = path.join(SPIRITFLIX_MEDIA_ROOT, ".spiritflix-admin", "metadata", "manual-tags");
export const SPIRITFLIX_MANUAL_TAGS_INDEX_PATH = path.join(SPIRITFLIX_MANUAL_TAGS_ROOT, "index.json");

export const SPIRITFLIX_MANUAL_STARTER_TAGS = [
  "2 girls",
  "asmr",
  "backshot",
  "blowjob",
  "car",
  "compilation",
  "cum on tits",
  "dance",
  "deep throat",
  "handjob",
  "solo",
  "wet noises",
] as const;

export interface SpiritFlixManualTagRecord {
  schema: typeof SPIRITFLIX_MANUAL_TAG_SCHEMA;
  itemId: string;
  filePath?: string;
  manualTags: string[];
  updatedAt: string;
  source: "manual";
  createdBy?: "local-user";
}

export interface SpiritFlixManualTagSummary {
  tag: string;
  label: string;
  count: number;
}

export interface SpiritFlixManualTagIndex {
  schema: typeof SPIRITFLIX_MANUAL_TAG_INDEX_SCHEMA;
  updatedAt: string;
  tags: SpiritFlixManualTagSummary[];
  modelAttributes?: SpiritFlixManualTagSummary[];
}

export interface SpiritFlixManualTagStoreOptions {
  rootDir?: string;
  lookupFilePath?: string;
}

export interface SetSpiritFlixManualTagsInput {
  itemId: string;
  filePath?: string;
  manualTags: string[];
}

export interface SpiritFlixManualTagPropagationItem {
  itemId: string;
  filePath?: string;
}

function getManualTagRoot(options: SpiritFlixManualTagStoreOptions = {}): string {
  return options.rootDir ?? process.env.SPIRITFLIX_MANUAL_TAG_ROOT ?? SPIRITFLIX_MANUAL_TAGS_ROOT;
}

function getManualTagIndexPath(options: SpiritFlixManualTagStoreOptions = {}): string {
  return path.join(getManualTagRoot(options), "index.json");
}

export function normalizeSpiritFlixManualTags(inputs: unknown[]): string[] {
  const seen = new Set<string>();
  const tags: string[] = [];
  inputs.forEach((input) => {
    const tag = canonicalizeSpiritFlixManualTag(input);
    if (!tag || seen.has(tag)) return;
    seen.add(tag);
    tags.push(tag);
  });
  return tags;
}

function assertManualTagItemId(itemId: string): string {
  const normalized = itemId.trim();
  if (!normalized) throw new Error("Manual tag item id is required.");
  return normalized;
}

function getFilePathKey(input: unknown): string {
  return typeof input === "string" ? input.trim().replace(/\\/g, "/").toLowerCase() : "";
}

function getManualTagRecordPath(itemId: string, options: SpiritFlixManualTagStoreOptions = {}): string {
  const hash = createHash("sha256").update(assertManualTagItemId(itemId)).digest("hex");
  return path.join(getManualTagRoot(options), "items", `${hash}.json`);
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

function mergeStarterTags(records: SpiritFlixManualTagRecord[]): SpiritFlixManualTagIndex {
  const counts = new Map<string, number>();
  const attributeCounts = new Map<string, number>();
  SPIRITFLIX_MANUAL_STARTER_TAGS.forEach((tag) => counts.set(tag, 0));
  records.forEach((record) => {
    record.manualTags.forEach((tag) => {
      if (getSpiritFlixManualTagScope(tag) === "model") {
        attributeCounts.set(tag, (attributeCounts.get(tag) ?? 0) + 1);
        return;
      }
      counts.set(tag, (counts.get(tag) ?? 0) + 1);
    });
  });
  return {
    schema: SPIRITFLIX_MANUAL_TAG_INDEX_SCHEMA,
    updatedAt: new Date().toISOString(),
    tags: Array.from(counts.entries())
      .map(([tag, count]) => ({ tag, label: tag, count }))
      .sort((left, right) => right.count - left.count || left.label.localeCompare(right.label)),
    modelAttributes: Array.from(attributeCounts.entries())
      .map(([tag, count]) => ({ tag, label: tag, count }))
      .sort((left, right) => right.count - left.count || left.label.localeCompare(right.label)),
  };
}

export async function getSpiritFlixManualTagsForItem(
  itemId: string,
  options: SpiritFlixManualTagStoreOptions = {},
): Promise<SpiritFlixManualTagRecord> {
  const normalizedItemId = assertManualTagItemId(itemId);
  const existing = await readJsonFile<SpiritFlixManualTagRecord>(getManualTagRecordPath(normalizedItemId, options));
  if (existing?.schema === SPIRITFLIX_MANUAL_TAG_SCHEMA) {
    return {
      ...existing,
      manualTags: normalizeSpiritFlixManualTags(existing.manualTags),
    };
  }
  const lookupFilePath = getFilePathKey(options.lookupFilePath);
  if (lookupFilePath) {
    const fileMatchedRecord = (await listSpiritFlixManualTagRecords({ ...options, lookupFilePath: undefined }))
      .find((record) => getFilePathKey(record.filePath) === lookupFilePath);
    if (fileMatchedRecord) {
      return {
        ...fileMatchedRecord,
        itemId: normalizedItemId,
        manualTags: normalizeSpiritFlixManualTags(fileMatchedRecord.manualTags),
      };
    }
  }
  return {
    schema: SPIRITFLIX_MANUAL_TAG_SCHEMA,
    itemId: normalizedItemId,
    manualTags: [],
    updatedAt: new Date(0).toISOString(),
    source: "manual",
    createdBy: "local-user",
  };
}

export async function listSpiritFlixManualTagRecords(
  options: SpiritFlixManualTagStoreOptions = {},
): Promise<SpiritFlixManualTagRecord[]> {
  const itemsRoot = path.join(getManualTagRoot(options), "items");
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
      .map((entry) => readJsonFile<SpiritFlixManualTagRecord>(path.join(itemsRoot, entry))),
  );
  return records
    .filter((record): record is SpiritFlixManualTagRecord => Boolean(record?.schema === SPIRITFLIX_MANUAL_TAG_SCHEMA))
    .map((record) => ({ ...record, manualTags: normalizeSpiritFlixManualTags(record.manualTags) }));
}

export async function buildSpiritFlixManualTagIndex(
  options: SpiritFlixManualTagStoreOptions = {},
): Promise<SpiritFlixManualTagIndex> {
  const records = await listSpiritFlixManualTagRecords(options);
  const index = mergeStarterTags(records);
  await writeJsonFile(getManualTagIndexPath(options), index);
  return index;
}

export async function getSpiritFlixManualTagIndex(
  options: SpiritFlixManualTagStoreOptions = {},
): Promise<SpiritFlixManualTagIndex> {
  return buildSpiritFlixManualTagIndex(options);
}

export async function setSpiritFlixManualTagsForItem(
  input: SetSpiritFlixManualTagsInput,
  options: SpiritFlixManualTagStoreOptions = {},
): Promise<{ record: SpiritFlixManualTagRecord; previousManualTags: string[]; addedTags: string[]; removedTags: string[]; index: SpiritFlixManualTagIndex }> {
  const itemId = assertManualTagItemId(input.itemId);
  const manualTags = normalizeSpiritFlixManualTags(input.manualTags);
  const hadMalformed = input.manualTags.some((tag) => !canonicalizeSpiritFlixManualTag(tag));
  if (hadMalformed) throw new Error("Manual tags cannot be empty.");
  const canonicalInputs = input.manualTags.map((tag) => canonicalizeSpiritFlixManualTag(tag)).filter(Boolean);
  if (manualTags.length !== canonicalInputs.length) {
    throw new Error("Manual tags cannot contain duplicates.");
  }

  const previous = await getSpiritFlixManualTagsForItem(itemId, options);
  const previousSet = new Set(previous.manualTags);
  const nextSet = new Set(manualTags);
  const addedTags = manualTags.filter((tag) => !previousSet.has(tag));
  const removedTags = previous.manualTags.filter((tag) => !nextSet.has(tag));
  const record: SpiritFlixManualTagRecord = {
    schema: SPIRITFLIX_MANUAL_TAG_SCHEMA,
    itemId,
    filePath: input.filePath ?? previous.filePath,
    manualTags,
    updatedAt: new Date().toISOString(),
    source: "manual",
    createdBy: "local-user",
  };

  await writeJsonFile(getManualTagRecordPath(itemId, options), record);
  const index = await buildSpiritFlixManualTagIndex(options);

  if (!options.rootDir && !process.env.SPIRITFLIX_MANUAL_TAG_ROOT) {
    try {
      await writeSpiritFlixAdminReceipt({
        action: "manual-tags:update",
        status: "executed",
        sourcePath: record.filePath,
        jellyfinItemIds: [itemId],
        affectedPaths: [getManualTagRecordPath(itemId, options), getManualTagIndexPath(options)],
        reason: JSON.stringify({
          itemId,
          previousManualTags: previous.manualTags,
          newManualTags: record.manualTags,
          addedTags,
          removedTags,
          updatedAt: record.updatedAt,
        }),
        reversible: true,
        rollbackHint: "Reapply previousManualTags from receipt to the same item id.",
      });
    } catch {
      // Manual tags are the source of truth; receipt logging must not undo a successful tag save.
    }
  }

  return { record, previousManualTags: previous.manualTags, addedTags, removedTags, index };
}

export async function applySpiritFlixModelScopedTagChanges(
  items: SpiritFlixManualTagPropagationItem[],
  addedTags: string[],
  removedTags: string[],
  options: SpiritFlixManualTagStoreOptions = {},
): Promise<{ updatedRecords: SpiritFlixManualTagRecord[]; index: SpiritFlixManualTagIndex }> {
  const modelAddedTags = normalizeSpiritFlixManualTags(addedTags).filter((tag) => getSpiritFlixManualTagScope(tag) === "model");
  const modelRemovedTags = normalizeSpiritFlixManualTags(removedTags).filter((tag) => getSpiritFlixManualTagScope(tag) === "model");
  const uniqueItems = Array.from(
    new Map(
      items
        .map((item) => ({ itemId: item.itemId.trim(), filePath: item.filePath }))
        .filter((item) => item.itemId)
        .map((item) => [item.itemId, item]),
    ).values(),
  );
  if (!uniqueItems.length || (!modelAddedTags.length && !modelRemovedTags.length)) {
    return { updatedRecords: [], index: await buildSpiritFlixManualTagIndex(options) };
  }

  const updatedRecords: SpiritFlixManualTagRecord[] = [];
  for (const relatedItem of uniqueItems) {
    const existing = await getSpiritFlixManualTagsForItem(relatedItem.itemId, options);
    const nextTags = new Set(existing.manualTags);
    modelAddedTags.forEach((tag) => nextTags.add(tag));
    modelRemovedTags.forEach((tag) => nextTags.delete(tag));
    const nextManualTags = Array.from(nextTags).sort((left, right) => left.localeCompare(right));
    if (nextManualTags.join("\u0000") === existing.manualTags.join("\u0000")) continue;
    const record: SpiritFlixManualTagRecord = {
      schema: SPIRITFLIX_MANUAL_TAG_SCHEMA,
      itemId: relatedItem.itemId,
      filePath: relatedItem.filePath ?? existing.filePath,
      manualTags: nextManualTags,
      updatedAt: new Date().toISOString(),
      source: "manual",
      createdBy: "local-user",
    };
    await writeJsonFile(getManualTagRecordPath(relatedItem.itemId, options), record);
    updatedRecords.push(record);
  }

  const index = await buildSpiritFlixManualTagIndex(options);
  return { updatedRecords, index };
}

export async function findSpiritFlixManualTaggedItems(
  tag: string,
  options: SpiritFlixManualTagStoreOptions = {},
): Promise<SpiritFlixManualTagRecord[]> {
  const canonicalTag = canonicalizeSpiritFlixManualTag(tag);
  if (!canonicalTag) throw new Error("Manual tag filter is required.");
  if (getSpiritFlixManualTagScope(canonicalTag) === "model") return [];
  const records = await listSpiritFlixManualTagRecords(options);
  return records.filter((record) => record.manualTags.includes(canonicalTag));
}
