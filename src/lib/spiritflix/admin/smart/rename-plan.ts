// SpiritFlix smart rename plan (S8)
// Builds preview/export data only. It never renames, moves, or calls Level 2 execute.

import fs from "node:fs/promises";
import path from "node:path";
import { resolveSpiritFlixAdminPath } from "../paths";
import { readSmartAnalysis } from "./analysis-store";
import { buildSmartRenamePreviewDraft } from "./rename-preview";
import { isSpiritFlixSmartVideoExtension } from "./probe";
import { projectApprovedSmartMetadata } from "./metadata-bridge";
import type { SpiritFlixApprovedMetadataProjection } from "./metadata-bridge";
import type { SpiritFlixSmartAnalysis } from "./types";

export type SpiritFlixSmartRenamePlanItemStatus =
  | "ready"
  | "blocked"
  | "needs_review"
  | "skipped";

export interface SpiritFlixSmartRenamePlanItem {
  sourcePath: string;
  currentName: string;
  suggestedName?: string;
  targetPath?: string;
  status: SpiritFlixSmartRenamePlanItemStatus;
  reviewStatus: string;
  approvedTags: string[];
  rejectedTagIds: string[];
  warnings: string[];
  readyForLevel2Preview: boolean;
}

export interface SpiritFlixSmartRenamePlanCounts {
  candidates: number;
  ready: number;
  blocked: number;
  needs_review: number;
  skipped: number;
  collisions: number;
  target_conflicts: number;
}

export interface SpiritFlixSmartRenamePlan {
  schema: "spiritflix-smart-rename-plan/v1";
  generatedAt: string;
  rootPath: string;
  recursive: boolean;
  maxItems: number;
  applyEnabled: false;
  applyGate: string;
  items: SpiritFlixSmartRenamePlanItem[];
  counts: SpiritFlixSmartRenamePlanCounts;
}

export interface SpiritFlixSmartRenamePlanOptions {
  path?: string;
  paths?: string[];
  recursive?: boolean;
  maxItems?: number;
  mediaRoot?: string;
}

interface PlanTarget {
  videoPath: string;
  mediaRoot?: string;
}

const DEFAULT_PLAN_LIMIT = 50;
const MAX_PLAN_LIMIT = 200;

function boundedLimit(value: number | undefined): number {
  if (!Number.isFinite(value ?? NaN)) return DEFAULT_PLAN_LIMIT;
  return Math.max(1, Math.min(MAX_PLAN_LIMIT, Math.floor(value ?? DEFAULT_PLAN_LIMIT)));
}

function emptyCounts(): SpiritFlixSmartRenamePlanCounts {
  return {
    candidates: 0,
    ready: 0,
    blocked: 0,
    needs_review: 0,
    skipped: 0,
    collisions: 0,
    target_conflicts: 0,
  };
}

function summarize(items: SpiritFlixSmartRenamePlanItem[]): SpiritFlixSmartRenamePlanCounts {
  const counts = emptyCounts();
  for (const item of items) {
    counts.candidates += 1;
    if (item.status === "ready") counts.ready += 1;
    if (item.status === "blocked") counts.blocked += 1;
    if (item.status === "needs_review") counts.needs_review += 1;
    if (item.status === "skipped") counts.skipped += 1;
    if (item.warnings.some((warning) => /duplicate target/i.test(warning))) counts.collisions += 1;
    if (item.warnings.some((warning) => /target path already exists/i.test(warning))) counts.target_conflicts += 1;
  }
  return counts;
}

function isHiddenPathPart(name: string): boolean {
  return name.startsWith(".");
}

async function enumerateFolder(folderPath: string, recursive: boolean, maxItems: number, mediaRoot?: string): Promise<PlanTarget[]> {
  const found: PlanTarget[] = [];
  const pending = [folderPath];

  while (pending.length > 0 && found.length < maxItems) {
    const current = pending.shift()!;
    const entries = await fs.readdir(current, { withFileTypes: true });
    for (const entry of entries) {
      if (isHiddenPathPart(entry.name)) continue;
      const childPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        if (recursive) pending.push(childPath);
        continue;
      }
      if (!entry.isFile()) continue;
      if (!isSpiritFlixSmartVideoExtension(path.extname(entry.name).toLowerCase())) continue;
      found.push({ videoPath: childPath, mediaRoot });
      if (found.length >= maxItems) break;
    }
  }

  return found;
}

async function resolvePlanTargets(options: SpiritFlixSmartRenamePlanOptions, maxItems: number): Promise<{ rootPath: string; targets: PlanTarget[] }> {
  const requestedPaths = (options.paths ?? []).map((entry) => entry.trim()).filter(Boolean);
  if (requestedPaths.length > 0) {
    const targets: PlanTarget[] = [];
    for (const requested of requestedPaths.slice(0, maxItems)) {
      const { allowedRoot, realPath } = await resolveSpiritFlixAdminPath(requested);
      const stat = await fs.stat(realPath);
      if (stat.isFile() && isSpiritFlixSmartVideoExtension(path.extname(realPath).toLowerCase())) {
        targets.push({ videoPath: realPath, mediaRoot: options.mediaRoot ?? allowedRoot });
      }
    }
    return { rootPath: path.dirname(targets[0]?.videoPath ?? requestedPaths[0]), targets };
  }

  const { allowedRoot, realPath } = await resolveSpiritFlixAdminPath(options.path);
  const mediaRoot = options.mediaRoot ?? allowedRoot;
  const stat = await fs.stat(realPath);
  if (stat.isFile()) {
    return {
      rootPath: path.dirname(realPath),
      targets: isSpiritFlixSmartVideoExtension(path.extname(realPath).toLowerCase()) ? [{ videoPath: realPath, mediaRoot }] : [],
    };
  }
  if (!stat.isDirectory()) throw new Error("Smart rename plan requires a folder or video selection.");
  return { rootPath: realPath, targets: await enumerateFolder(realPath, Boolean(options.recursive), maxItems, mediaRoot) };
}

function reviewedFilenameSuggestion(
  analysis: SpiritFlixSmartAnalysis,
  projection: SpiritFlixApprovedMetadataProjection,
): string | undefined {
  const reviewed = analysis.reviewedMetadata;
  if (reviewed?.editedFilenameSuggestion) return reviewed.editedFilenameSuggestion;

  const base = reviewed?.editedDisplayTitle ?? analysis.suggestedDisplayTitle ?? path.parse(analysis.fileName).name;
  const approvedLabels = projection.approvedTags.map((tag) => tag.label).filter(Boolean);
  if (approvedLabels.length === 0) return projection.filenameSuggestion ?? base;

  const suffix = approvedLabels.slice(0, 3).filter((label) => !base.toLowerCase().includes(label.toLowerCase())).join(" ");
  return suffix ? `${base} ${suffix}` : base;
}

async function targetExists(targetPath: string, sourcePath: string): Promise<boolean> {
  if (path.resolve(targetPath) === path.resolve(sourcePath)) return false;
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function itemFromTarget(target: PlanTarget): Promise<SpiritFlixSmartRenamePlanItem> {
  const stat = await fs.stat(target.videoPath);
  const analysis = await readSmartAnalysis(
    { videoPath: target.videoPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs },
    target.mediaRoot ? { mediaRoot: target.mediaRoot } : undefined,
  );
  if (!analysis) {
    return {
      sourcePath: target.videoPath,
      currentName: path.basename(target.videoPath),
      status: "skipped",
      reviewStatus: "missing_analysis",
      approvedTags: [],
      rejectedTagIds: [],
      warnings: ["No smart analysis sidecar exists for this video."],
      readyForLevel2Preview: false,
    };
  }

  const reviewStatus = analysis.reviewedMetadata?.reviewStatus ?? "unreviewed";
  if (reviewStatus === "unreviewed") {
    return {
      sourcePath: target.videoPath,
      currentName: path.basename(target.videoPath),
      status: "needs_review",
      reviewStatus,
      approvedTags: [],
      rejectedTagIds: [],
      warnings: ["Analysis must be reviewed before rename preview."],
      readyForLevel2Preview: false,
    };
  }

  const projection = projectApprovedSmartMetadata(analysis);
  const filenameSuggestion = reviewedFilenameSuggestion(analysis, projection);
  if (!filenameSuggestion || projection.reviewStatus === "rejected") {
    return {
      sourcePath: target.videoPath,
      currentName: path.basename(target.videoPath),
      status: "blocked",
      reviewStatus,
      approvedTags: projection.approvedTags.map((tag) => tag.label),
      rejectedTagIds: projection.rejectedTagIds,
      warnings: ["Reviewed metadata does not contain an approved filename proposal."],
      readyForLevel2Preview: false,
    };
  }

  const draft = buildSmartRenamePreviewDraft({
    sourcePath: target.videoPath,
    filenameSuggestion,
  });
  const warnings = [...draft.warnings];
  if (await targetExists(draft.targetPath, target.videoPath)) {
    warnings.push("Target path already exists.");
  }
  const readyForLevel2Preview = draft.readyForLevel2Preview && warnings.length === 0;

  return {
    sourcePath: target.videoPath,
    currentName: path.basename(target.videoPath),
    suggestedName: draft.suggestedName,
    targetPath: draft.targetPath,
    status: readyForLevel2Preview ? "ready" : "blocked",
    reviewStatus,
    approvedTags: projection.approvedTags.map((tag) => tag.label),
    rejectedTagIds: projection.rejectedTagIds,
    warnings,
    readyForLevel2Preview,
  };
}

export async function buildSpiritFlixSmartRenamePlan(
  options: SpiritFlixSmartRenamePlanOptions = {},
): Promise<SpiritFlixSmartRenamePlan> {
  const maxItems = boundedLimit(options.maxItems);
  const { rootPath, targets } = await resolvePlanTargets(options, maxItems);
  const items = await Promise.all(targets.map((target) => itemFromTarget(target)));

  const targetGroups = new Map<string, SpiritFlixSmartRenamePlanItem[]>();
  for (const item of items) {
    if (!item.targetPath) continue;
    const key = item.targetPath.toLowerCase();
    targetGroups.set(key, [...(targetGroups.get(key) ?? []), item]);
  }

  for (const group of targetGroups.values()) {
    if (group.length < 2) continue;
    for (const item of group) {
      item.warnings.push("Duplicate target path in this plan.");
      item.readyForLevel2Preview = false;
      item.status = "blocked";
    }
  }

  return {
    schema: "spiritflix-smart-rename-plan/v1",
    generatedAt: new Date().toISOString(),
    rootPath,
    recursive: Boolean(options.recursive),
    maxItems,
    applyEnabled: false,
    applyGate: "Preview/export only. Real rename or move must use a future explicit Level 2 apply task.",
    items,
    counts: summarize(items),
  };
}
