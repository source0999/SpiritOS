import fs from "node:fs/promises";
import path from "node:path";
import { createHash, randomUUID } from "node:crypto";
import { SPIRITFLIX_MEDIA_ROOT } from "./constants";
import { getServerJellyfinCredentials } from "./jellyfin-server";
import {
  assertWritableSpiritFlixAdminPath,
  isSpiritFlixAdminTrashPath,
  resolveSpiritFlixAdminPath,
  validateSpiritFlixAdminPathCandidate,
} from "./paths";
import { createReceiptId, writeSpiritFlixAdminReceipt } from "./receipts";
import type {
  SpiritFlixAdminActionName,
  SpiritFlixAdminActionRequest,
  SpiritFlixAdminActionResponse,
  SpiritFlixAdminActionRiskLevel,
  SpiritFlixAdminMetadataSidecar,
  SpiritFlixAdminOrderFile,
  SpiritFlixAdminReceipt,
} from "./types";

const METADATA_ROOT = path.join(SPIRITFLIX_MEDIA_ROOT, ".spiritflix-admin", "metadata");
const ORDER_FILE = path.join(SPIRITFLIX_MEDIA_ROOT, ".spiritflix-admin", "order.json");
const TRASH_ROOT = path.join(SPIRITFLIX_MEDIA_ROOT, ".trash");
const SMOKE_ROOT = path.join(SPIRITFLIX_MEDIA_ROOT, "other", ".spiritflix-admin-smoke");

const VIDEO_EXTENSIONS = new Set([".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm", ".wmv"]);
const ALLOWED_METADATA_FIELDS = new Set([
  "displayTitle",
  "customTags",
  "collection",
  "notes",
  "manualSortGroup",
  "manualSortIndex",
  "hiddenFromViewer",
  "favoriteOverride",
]);
const MAX_METADATA_BYTES = 16_384;
const MAX_ORDER_BYTES = 65_536;

const previewStore = new Map<
  string,
  { action: SpiritFlixAdminActionName; payload: SpiritFlixAdminActionRequest; receipt: SpiritFlixAdminReceipt }
>();

export type SpiritFlixAdminActionApprovalSnapshot = {
  action: SpiritFlixAdminActionName;
  payload: SpiritFlixAdminActionRequest;
  previewId: string;
  receipt: SpiritFlixAdminReceipt;
};

/**
 * Returns the immutable server-held payload behind an action preview. Approval
 * issuance and execution both call this function so a browser cannot replace
 * paths, metadata, order content, or rescan inputs after preview.
 */
export function getSpiritFlixAdminActionApprovalSnapshot(
  previewId: string,
): SpiritFlixAdminActionApprovalSnapshot | null {
  const cached = previewStore.get(previewId);
  if (!cached) return null;
  return {
    action: cached.action,
    payload: structuredClone(cached.payload),
    previewId,
    receipt: structuredClone(cached.receipt),
  };
}

export type SpiritFlixAdminActionMutationSnapshot = {
  approval: SpiritFlixAdminActionApprovalSnapshot;
  targetContent: string | null;
};

export async function captureSpiritFlixAdminActionMutation(
  previewId: string,
): Promise<SpiritFlixAdminActionMutationSnapshot> {
  const approval = getSpiritFlixAdminActionApprovalSnapshot(previewId);
  if (!approval) throw new Error("spiritflix_admin_preview_not_found");
  const target = approval.receipt.targetPath;
  let targetContent: string | null = null;
  if (target && (approval.action === "writeMetadata" || approval.action === "saveOrder")) {
    try {
      targetContent = await fs.readFile(target, "utf8");
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    }
  }
  return { approval, targetContent };
}

export async function verifySpiritFlixAdminActionMutation(
  result: SpiritFlixAdminActionResponse,
): Promise<Record<string, unknown>> {
  if (!result.allowed || result.phase !== "execute" || result.receipt?.status !== "executed") {
    throw new Error("spiritflix_admin_action_verification_failed");
  }
  const receipt = result.receipt;
  const paths = await Promise.all(receipt.affectedPaths.map(async (candidate) => {
    try {
      const details = await fs.lstat(candidate);
      if (details.isSymbolicLink()) throw new Error("spiritflix_admin_action_symlink_forbidden");
      return { exists: true, isDirectory: details.isDirectory(), path: candidate, size: details.size };
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return { exists: false, path: candidate };
      throw error;
    }
  }));
  if (receipt.targetPath && result.action !== "requestJellyfinRescan") {
    const target = paths.find((entry) => entry.path === receipt.targetPath);
    if (!target?.exists) throw new Error("spiritflix_admin_action_target_missing");
  }
  if (receipt.sourcePath && ["move", "rename", "restore", "softDelete"].includes(result.action)) {
    const source = paths.find((entry) => entry.path === receipt.sourcePath);
    if (source?.exists) throw new Error("spiritflix_admin_action_source_still_exists");
  }
  return {
    action: result.action,
    affectedPaths: paths,
    previewId: result.previewId,
    receiptId: receipt.id,
    status: receipt.status,
  };
}

export async function rollbackSpiritFlixAdminActionMutation(
  snapshot: SpiritFlixAdminActionMutationSnapshot,
  result: SpiritFlixAdminActionResponse | undefined,
): Promise<void> {
  const receipt = result?.receipt ?? snapshot.approval.receipt;
  const action = snapshot.approval.action;
  if (result?.allowed || result?.mutationApplied) {
    if (action === "createFolder" && receipt.targetPath) {
      await fs.rmdir(receipt.targetPath);
    } else if (["rename", "move", "softDelete", "restore"].includes(action) && receipt.sourcePath && receipt.targetPath) {
      await fs.mkdir(path.dirname(receipt.sourcePath), { recursive: true });
      await moveSpiritFlixAdminPath(receipt.targetPath, receipt.sourcePath);
    } else if ((action === "writeMetadata" || action === "saveOrder") && receipt.targetPath) {
      if (snapshot.targetContent === null) {
        await fs.unlink(receipt.targetPath).catch((error: NodeJS.ErrnoException) => {
          if (error.code !== "ENOENT") throw error;
        });
      } else {
        await atomicWriteFile(receipt.targetPath, snapshot.targetContent);
      }
    }
  }
  await writeSpiritFlixAdminReceipt({
    ...receipt,
    id: randomUUID(),
    status: "rolled_back",
    reason: result?.allowed
      ? "Authority finalization or result verification failed; mutation was compensated."
      : "Execution did not produce an authoritative success.",
  });
}

export function normalizeSpiritFlixAdminActionRequest(request: SpiritFlixAdminActionRequest): SpiritFlixAdminActionRequest {
  const phase = request.mode ?? request.phase ?? "preview";
  const previewId = request.confirmToken ?? request.previewId;
  const folderName = request.folderName ?? (request.action === "createFolder" ? request.name : undefined);
  const newName = request.newName ?? (request.action === "rename" ? request.name : undefined);
  const targetPath =
    request.targetPath ??
    (request.action === "createFolder" ? request.parentPath : undefined) ??
    (request.action === "move" ? request.parentPath : undefined);

  return {
    ...request,
    phase,
    previewId,
    folderName,
    newName,
    targetPath,
  };
}

function sanitizeName(value: string): string {
  const cleaned = value.trim().replace(/[\\/:*?"<>|]/g, "_").replace(/\.\.+/g, ".");
  if (!cleaned || cleaned === "." || cleaned === ".." || cleaned.includes("/") || cleaned.includes("\\")) {
    throw new Error("Name is not allowed.");
  }
  return cleaned;
}

function stableItemKey(value: string): string {
  const normalized = value.replace(/\\/g, "/").toLowerCase();
  return `path:${createHash("sha256").update(normalized).digest("hex")}`;
}

function riskForAction(action: SpiritFlixAdminActionName): SpiritFlixAdminActionRiskLevel {
  switch (action) {
    case "softDelete":
    case "move":
      return "medium";
    case "requestJellyfinRescan":
      return "high";
    case "rename":
    case "restore":
      return "medium";
    default:
      return "low";
  }
}

async function assertAllowedPath(candidate: string): Promise<string> {
  const resolved = await resolveSpiritFlixAdminPath(candidate);
  return resolved.realPath;
}

async function assertParentExists(parentPath: string): Promise<string> {
  const realParent = await assertAllowedPath(parentPath);
  const stats = await fs.stat(realParent);
  if (!stats.isDirectory()) throw new Error("Parent path must be a folder.");
  return realParent;
}

function buildPlannedReceipt(
  action: string,
  affectedPaths: string[],
  extra: Partial<SpiritFlixAdminReceipt> = {},
): SpiritFlixAdminReceipt {
  return {
    id: createReceiptId(),
    timestamp: new Date().toISOString(),
    actor: "spiritflix-admin",
    action,
    status: "planned",
    affectedPaths,
    reversible: extra.reversible ?? true,
    ...extra,
  };
}

function response(
  action: SpiritFlixAdminActionName,
  phase: "preview" | "execute",
  previewId: string,
  allowed: boolean,
  message: string,
  extra: Partial<SpiritFlixAdminActionResponse> = {},
): SpiritFlixAdminActionResponse {
  return {
    schema: "spiritflix-admin-action/v1",
    action,
    phase,
    previewId,
    allowed,
    message,
    riskLevel: extra.riskLevel ?? riskForAction(action),
    ...extra,
  };
}

function resolveRenameTarget(sourcePath: string, rawName: string): string {
  const sanitized = sanitizeName(rawName);
  const extension = path.extname(sourcePath);
  if (VIDEO_EXTENSIONS.has(extension.toLowerCase()) && !path.extname(sanitized)) {
    return `${sanitized}${extension}`;
  }
  return sanitized;
}

function validateMetadata(payload: unknown): SpiritFlixAdminMetadataSidecar {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Metadata payload is required.");
  }
  const record = payload as Record<string, unknown>;
  for (const key of Object.keys(record)) {
    if (!ALLOWED_METADATA_FIELDS.has(key)) {
      throw new Error(`Unknown metadata field: ${key}`);
    }
  }
  const serialized = JSON.stringify(record);
  if (serialized.length > MAX_METADATA_BYTES) {
    throw new Error("Metadata payload is too large.");
  }
  return record as SpiritFlixAdminMetadataSidecar;
}

async function atomicWriteFile(filePath: string, content: string): Promise<void> {
  const tempPath = `${filePath}.tmp-${process.pid}-${Date.now()}`;
  await fs.writeFile(tempPath, content, "utf8");
  await moveSpiritFlixAdminPath(tempPath, filePath);
}

/** Rename when possible; copy+delete across mount points (yes/ vs .trash on sda1). */
export async function moveSpiritFlixAdminPath(sourcePath: string, targetPath: string): Promise<void> {
  try {
    await fs.rename(sourcePath, targetPath);
    return;
  } catch (error) {
    const err = error as NodeJS.ErrnoException;
    if (err.code !== "EXDEV") throw error;
  }

  await fs.mkdir(path.dirname(targetPath), { recursive: true });
  const stats = await fs.stat(sourcePath);
  if (stats.isDirectory()) {
    await fs.cp(sourcePath, targetPath, { recursive: true, errorOnExist: true });
    await fs.rm(sourcePath, { recursive: true, force: true });
    return;
  }

  await fs.copyFile(sourcePath, targetPath);
  await fs.unlink(sourcePath);
}

async function crossDeviceMoveWarning(sourcePath: string, targetPath: string): Promise<string | null> {
  try {
    const [sourceStat, targetParentStat] = await Promise.all([
      fs.stat(sourcePath),
      fs.stat(path.dirname(targetPath)),
    ]);
    if (sourceStat.dev !== targetParentStat.dev) {
      return "Source and trash are on different volumes; delete copies the file then removes the original.";
    }
  } catch {
    return null;
  }
  return null;
}

async function uniqueTrashPath(targetPath: string): Promise<string> {
  let candidate = targetPath;
  let counter = 1;
  while (true) {
    try {
      await fs.access(candidate);
      const directory = path.dirname(candidate);
      const base = path.basename(candidate);
      candidate = path.join(directory, `${base}.__trash-${counter}`);
      counter += 1;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return candidate;
      throw error;
    }
  }
}

function restoreTargetFromTrash(trashPath: string): string {
  if (!isSpiritFlixAdminTrashPath(trashPath)) {
    throw new Error("Restore source must be inside the trash folder.");
  }
  const relative = trashPath.split(`${path.sep}.trash${path.sep}`)[1]?.split(path.sep).slice(1).join(path.sep);
  if (!relative) throw new Error("Could not determine restore target.");
  return path.join(SPIRITFLIX_MEDIA_ROOT, relative);
}

export async function handleSpiritFlixAdminAction(rawRequest: SpiritFlixAdminActionRequest): Promise<SpiritFlixAdminActionResponse> {
  const request = normalizeSpiritFlixAdminActionRequest(rawRequest);
  const phase = request.phase ?? "preview";
  const previewId = request.previewId ?? createReceiptId();

  if (phase === "execute") {
    const cached = previewStore.get(previewId);
    if (!cached || cached.action !== request.action) {
      return response(request.action, "execute", previewId, false, "Preview confirmation is required before executing this action.");
    }
    previewStore.delete(previewId);
    return executeAction(cached.action, normalizeSpiritFlixAdminActionRequest(cached.payload), previewId, cached.receipt);
  }

  try {
    return await previewAction(request.action, request, previewId);
  } catch (error) {
    const reason = error instanceof Error ? error.message : "Action blocked.";
    return response(request.action, "preview", previewId, false, reason);
  }
}

async function previewAction(
  action: SpiritFlixAdminActionName,
  request: SpiritFlixAdminActionRequest,
  previewId: string,
): Promise<SpiritFlixAdminActionResponse> {
  switch (action) {
    case "createFolder":
      return previewCreateFolder(request, previewId);
    case "rename":
      return previewRename(request, previewId);
    case "move":
      return previewMove(request, previewId);
    case "softDelete":
      return previewSoftDelete(request, previewId);
    case "restore":
      return previewRestore(request, previewId);
    case "writeMetadata":
      return previewWriteMetadata(request, previewId);
    case "saveOrder":
      return previewSaveOrder(request, previewId);
    case "requestJellyfinRescan":
      return previewRescan(request, previewId);
    default:
      return response(action, "preview", previewId, false, "Unknown action.");
  }
}

async function previewCreateFolder(request: SpiritFlixAdminActionRequest, previewId: string) {
  const parentPath = await assertParentExists(request.targetPath ?? SPIRITFLIX_MEDIA_ROOT);
  const folderName = sanitizeName(request.folderName ?? "");
  const targetPath = path.join(parentPath, folderName);
  await fs.access(targetPath).then(() => {
    throw new Error("Folder already exists.");
  }).catch((error: NodeJS.ErrnoException) => {
    if (error.code !== "ENOENT") throw error;
  });

  const receipt = buildPlannedReceipt("createFolder", [targetPath], {
    targetPath,
    sourcePath: parentPath,
    rollbackHint: "Delete the created folder if empty.",
    previewId,
  });
  previewStore.set(previewId, { action: "createFolder", payload: request, receipt });
  return response("createFolder", "preview", previewId, true, `Create folder ${folderName}`, {
    receipt,
    preview: {
      targetPath,
      sourcePath: parentPath,
      affectedPaths: [targetPath],
      warnings: [],
      reversible: true,
    },
  });
}

async function previewRename(request: SpiritFlixAdminActionRequest, previewId: string) {
  const sourcePath = await assertAllowedPath(request.sourcePath ?? "");
  assertWritableSpiritFlixAdminPath(sourcePath, "rename");
  const parentPath = path.dirname(sourcePath);
  const newName = resolveRenameTarget(sourcePath, request.newName ?? "");
  const targetPath = path.join(parentPath, newName);
  if (targetPath === sourcePath) throw new Error("New name matches the current name.");
  await fs.access(targetPath).then(() => {
    throw new Error("Target already exists.");
  }).catch((error: NodeJS.ErrnoException) => {
    if (error.code !== "ENOENT") throw error;
  });

  const receipt = buildPlannedReceipt("rename", [sourcePath, targetPath], {
    sourcePath,
    targetPath,
    rollbackHint: "Rename back to the original filename.",
    previewId,
  });
  previewStore.set(previewId, { action: "rename", payload: request, receipt });
  return response("rename", "preview", previewId, true, `Rename to ${newName}`, {
    receipt,
    preview: {
      sourcePath,
      targetPath,
      affectedPaths: [sourcePath, targetPath],
      warnings: [],
      reversible: true,
    },
  });
}

async function previewMove(request: SpiritFlixAdminActionRequest, previewId: string) {
  const sourcePath = await assertAllowedPath(request.sourcePath ?? "");
  assertWritableSpiritFlixAdminPath(sourcePath, "move");
  const targetParent = await assertParentExists(request.targetPath ?? request.parentPath ?? "");
  const targetPath = path.join(targetParent, path.basename(sourcePath));

  if (targetPath === sourcePath) throw new Error("Item is already at the target location.");
  await fs.access(targetPath).then(() => {
    throw new Error("Target already exists.");
  }).catch((error: NodeJS.ErrnoException) => {
    if (error.code !== "ENOENT") throw error;
  });

  const warnings: string[] = [];
  const sourceStats = await fs.stat(sourcePath);
  if (sourceStats.isDirectory()) warnings.push("Moving folders can take time. Review the affected path before confirming.");

  const receipt = buildPlannedReceipt("move", [sourcePath, targetPath], {
    sourcePath,
    targetPath,
    rollbackHint: "Move the item back to the source folder.",
    previewId,
  });
  previewStore.set(previewId, { action: "move", payload: request, receipt });
  return response("move", "preview", previewId, true, `Move to ${targetParent}`, {
    receipt,
    preview: {
      sourcePath,
      targetPath,
      affectedPaths: [sourcePath, targetPath],
      warnings,
      reversible: true,
    },
  });
}

async function previewSoftDelete(request: SpiritFlixAdminActionRequest, previewId: string) {
  const sourcePath = await assertAllowedPath(request.sourcePath ?? "");
  assertWritableSpiritFlixAdminPath(sourcePath, "soft delete");
  const relative = path.relative(SPIRITFLIX_MEDIA_ROOT, sourcePath);
  const trashDay = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const targetPath = await uniqueTrashPath(path.join(TRASH_ROOT, trashDay, relative));
  const crossDeviceWarning = await crossDeviceMoveWarning(sourcePath, targetPath);
  const warnings = [
    "Soft delete moves to SpiritFlix trash, not permanent delete.",
    "No hard delete is performed.",
    ...(crossDeviceWarning ? [crossDeviceWarning] : []),
  ];
  const receipt = buildPlannedReceipt("softDelete", [sourcePath, targetPath], {
    sourcePath,
    targetPath,
    rollbackHint: "Restore from trash to the original path.",
    previewId,
  });
  previewStore.set(previewId, { action: "softDelete", payload: request, receipt });
  return response("softDelete", "preview", previewId, true, "Move item to soft trash", {
    receipt,
    preview: {
      sourcePath,
      targetPath,
      affectedPaths: [sourcePath, targetPath],
      warnings,
      reversible: true,
    },
  });
}

async function previewRestore(request: SpiritFlixAdminActionRequest, previewId: string) {
  const trashPath = await assertAllowedPath(request.sourcePath ?? "");
  const targetPath = request.targetPath
    ? await validateSpiritFlixAdminPathCandidate(request.targetPath)
    : await validateSpiritFlixAdminPathCandidate(restoreTargetFromTrash(trashPath));
  await fs.access(targetPath).then(() => {
    throw new Error("Restore target already exists.");
  }).catch((error: NodeJS.ErrnoException) => {
    if (error.code !== "ENOENT") throw error;
  });

  const receipt = buildPlannedReceipt("restore", [trashPath, targetPath], {
    sourcePath: trashPath,
    targetPath,
    rollbackHint: "Soft-delete again if needed.",
    previewId,
  });
  previewStore.set(previewId, { action: "restore", payload: request, receipt });
  return response("restore", "preview", previewId, true, "Restore item from trash", {
    receipt,
    preview: {
      sourcePath: trashPath,
      targetPath,
      affectedPaths: [trashPath, targetPath],
      warnings: [],
      reversible: true,
    },
  });
}

async function previewWriteMetadata(request: SpiritFlixAdminActionRequest, previewId: string) {
  const sourcePath = await assertAllowedPath(request.sourcePath ?? "");
  validateMetadata(request.metadata ?? {});
  const hash = createHash("sha256").update(sourcePath.replace(/\\/g, "/").toLowerCase()).digest("hex");
  const targetPath = path.join(METADATA_ROOT, `${hash}.json`);
  const receipt = buildPlannedReceipt("writeMetadata", [targetPath], {
    sourcePath,
    targetPath,
    rollbackHint: "Edit or delete the metadata sidecar.",
    previewId,
  });
  previewStore.set(previewId, { action: "writeMetadata", payload: request, receipt });
  return response("writeMetadata", "preview", previewId, true, "Write SpiritFlix metadata sidecar", {
    receipt,
    preview: {
      sourcePath,
      targetPath,
      affectedPaths: [targetPath],
      warnings: ["Does not edit Jellyfin database rows.", "Metadata is stored under .spiritflix-admin/metadata only."],
      reversible: true,
    },
  });
}

async function previewSaveOrder(request: SpiritFlixAdminActionRequest, previewId: string) {
  const order = request.order;
  if (!order || order.version !== 1 || !Array.isArray(order.groups)) throw new Error("Invalid custom order payload.");
  const serialized = JSON.stringify(order);
  if (serialized.length > MAX_ORDER_BYTES) throw new Error("Custom order payload is too large.");
  for (const group of order.groups) {
    for (const key of group.itemKeys) {
      if (!validateOrderItemKey(key)) {
        throw new Error(`Invalid order item key: ${key}`);
      }
    }
  }
  const receipt = buildPlannedReceipt("saveOrder", [ORDER_FILE], {
    targetPath: ORDER_FILE,
    rollbackHint: "Restore the previous order.json backup.",
    previewId,
  });
  previewStore.set(previewId, { action: "saveOrder", payload: request, receipt });
  return response("saveOrder", "preview", previewId, true, "Save custom shelf order", {
    receipt,
    preview: { targetPath: ORDER_FILE, affectedPaths: [ORDER_FILE], warnings: [], reversible: true },
  });
}

async function previewRescan(request: SpiritFlixAdminActionRequest, previewId: string) {
  const targetPath = await assertAllowedPath(request.rescanPath ?? SPIRITFLIX_MEDIA_ROOT);
  const credentials = getServerJellyfinCredentials();
  if (!credentials) {
    return response(
      "requestJellyfinRescan",
      "preview",
      previewId,
      false,
      "Rescan action is not active yet because safe Jellyfin admin auth is unavailable.",
      {
        riskLevel: "high",
        preview: {
          targetPath,
          affectedPaths: [targetPath],
          warnings: ["Preview only — rescan execution is gated until server credentials are configured."],
          reversible: false,
        },
      },
    );
  }

  const receipt = buildPlannedReceipt("requestJellyfinRescan", [targetPath], {
    targetPath,
    reversible: false,
    rollbackHint: "Rescan is not reversible.",
    previewId,
  });
  previewStore.set(previewId, { action: "requestJellyfinRescan", payload: request, receipt });
  return response("requestJellyfinRescan", "preview", previewId, true, `Request Jellyfin rescan for ${targetPath}`, {
    receipt,
    preview: {
      targetPath,
      affectedPaths: [targetPath],
      warnings: ["Does not restart Jellyfin."],
      reversible: false,
    },
  });
}

function assertExactPlannedPath(actual: string, expected: string | undefined): void {
  if (!expected || path.resolve(actual) !== path.resolve(expected)) {
    throw new Error("SpiritFlix admin preview path changed before execution.");
  }
}

async function executeAction(
  action: SpiritFlixAdminActionName,
  request: SpiritFlixAdminActionRequest,
  previewId: string,
  planned: SpiritFlixAdminReceipt,
): Promise<SpiritFlixAdminActionResponse> {
  let mutationApplied = false;
  try {
    switch (action) {
      case "createFolder": {
        const parentPath = await assertParentExists(request.targetPath ?? SPIRITFLIX_MEDIA_ROOT);
        const folderName = sanitizeName(request.folderName ?? "");
        const targetPath = path.join(parentPath, folderName);
        assertExactPlannedPath(targetPath, planned.targetPath);
        await fs.mkdir(targetPath, { recursive: false });
        mutationApplied = true;
        const receipt = await writeSpiritFlixAdminReceipt({
          ...planned,
          status: "executed",
          targetPath,
          affectedPaths: [targetPath],
          previewId,
        });
        return response(action, "execute", previewId, true, "Folder created.", {
          receipt,
          mutationApplied,
          preview: { targetPath, affectedPaths: [targetPath], warnings: [] },
        });
      }
      case "rename": {
        const sourcePath = await assertAllowedPath(request.sourcePath ?? "");
        assertExactPlannedPath(sourcePath, planned.sourcePath);
        assertWritableSpiritFlixAdminPath(sourcePath, "rename");
        const targetPath = path.join(path.dirname(sourcePath), resolveRenameTarget(sourcePath, request.newName ?? ""));
        assertExactPlannedPath(targetPath, planned.targetPath);
        await moveSpiritFlixAdminPath(sourcePath, targetPath);
        mutationApplied = true;
        const receipt = await writeSpiritFlixAdminReceipt({
          ...planned,
          status: "executed",
          sourcePath,
          targetPath,
          affectedPaths: [sourcePath, targetPath],
          previewId,
        });
        return response(action, "execute", previewId, true, "Rename complete.", {
          receipt,
          mutationApplied,
          preview: { sourcePath, targetPath, affectedPaths: [sourcePath, targetPath], warnings: [] },
        });
      }
      case "move": {
        const sourcePath = await assertAllowedPath(request.sourcePath ?? "");
        assertExactPlannedPath(sourcePath, planned.sourcePath);
        assertWritableSpiritFlixAdminPath(sourcePath, "move");
        const targetParent = await assertParentExists(request.targetPath ?? request.parentPath ?? "");
        const targetPath = path.join(targetParent, path.basename(sourcePath));
        assertExactPlannedPath(targetPath, planned.targetPath);
        await moveSpiritFlixAdminPath(sourcePath, targetPath);
        mutationApplied = true;
        const receipt = await writeSpiritFlixAdminReceipt({
          ...planned,
          status: "executed",
          sourcePath,
          targetPath,
          affectedPaths: [sourcePath, targetPath],
          previewId,
        });
        return response(action, "execute", previewId, true, "Move complete.", {
          receipt,
          mutationApplied,
          preview: { sourcePath, targetPath, affectedPaths: [sourcePath, targetPath], warnings: [] },
        });
      }
      case "softDelete": {
        const sourcePath = await assertAllowedPath(request.sourcePath ?? "");
        assertExactPlannedPath(sourcePath, planned.sourcePath);
        assertWritableSpiritFlixAdminPath(sourcePath, "soft delete");
        const relative = path.relative(SPIRITFLIX_MEDIA_ROOT, sourcePath);
        const trashDay = new Date().toISOString().slice(0, 10).replace(/-/g, "");
        const targetPath = await uniqueTrashPath(path.join(TRASH_ROOT, trashDay, relative));
        assertExactPlannedPath(targetPath, planned.targetPath);
        await fs.mkdir(path.dirname(targetPath), { recursive: true });
        await moveSpiritFlixAdminPath(sourcePath, targetPath);
        mutationApplied = true;
        const receipt = await writeSpiritFlixAdminReceipt({
          ...planned,
          status: "executed",
          sourcePath,
          targetPath,
          affectedPaths: [sourcePath, targetPath],
          previewId,
        });
        return response(action, "execute", previewId, true, "Moved to trash.", {
          receipt,
          mutationApplied,
          preview: { sourcePath, targetPath, affectedPaths: [sourcePath, targetPath], warnings: [] },
        });
      }
      case "restore": {
        const trashPath = await assertAllowedPath(request.sourcePath ?? "");
        assertExactPlannedPath(trashPath, planned.sourcePath);
        const targetPath = request.targetPath
          ? await validateSpiritFlixAdminPathCandidate(request.targetPath)
          : await validateSpiritFlixAdminPathCandidate(restoreTargetFromTrash(trashPath));
        assertExactPlannedPath(targetPath, planned.targetPath);
        await fs.access(targetPath).then(() => {
          throw new Error("Restore target already exists.");
        }).catch((error: NodeJS.ErrnoException) => {
          if (error.code !== "ENOENT") throw error;
        });
        await fs.mkdir(path.dirname(targetPath), { recursive: true });
        await moveSpiritFlixAdminPath(trashPath, targetPath);
        mutationApplied = true;
        const receipt = await writeSpiritFlixAdminReceipt({
          ...planned,
          status: "executed",
          sourcePath: trashPath,
          targetPath,
          affectedPaths: [trashPath, targetPath],
          previewId,
        });
        return response(action, "execute", previewId, true, "Restore complete.", {
          receipt,
          mutationApplied,
          preview: { sourcePath: trashPath, targetPath, affectedPaths: [trashPath, targetPath], warnings: [] },
        });
      }
      case "writeMetadata": {
        const sourcePath = await assertAllowedPath(request.sourcePath ?? "");
        assertExactPlannedPath(sourcePath, planned.sourcePath);
        const metadata = validateMetadata(request.metadata ?? {});
        const hash = createHash("sha256").update(sourcePath.replace(/\\/g, "/").toLowerCase()).digest("hex");
        const targetPath = path.join(METADATA_ROOT, `${hash}.json`);
        assertExactPlannedPath(targetPath, planned.targetPath);
        await fs.mkdir(METADATA_ROOT, { recursive: true });
        await atomicWriteFile(targetPath, JSON.stringify({ sourcePath, ...metadata }, null, 2));
        mutationApplied = true;
        const receipt = await writeSpiritFlixAdminReceipt({
          ...planned,
          status: "executed",
          sourcePath,
          targetPath,
          affectedPaths: [targetPath],
          previewId,
        });
        return response(action, "execute", previewId, true, "Metadata saved.", {
          receipt,
          mutationApplied,
          preview: { sourcePath, targetPath, affectedPaths: [targetPath], warnings: [] },
        });
      }
      case "saveOrder": {
        assertExactPlannedPath(ORDER_FILE, planned.targetPath);
        await fs.mkdir(path.dirname(ORDER_FILE), { recursive: true });
        const order: SpiritFlixAdminOrderFile = {
          ...(request.order as SpiritFlixAdminOrderFile),
          version: 1,
          updatedAt: new Date().toISOString(),
        };
        await atomicWriteFile(ORDER_FILE, JSON.stringify(order, null, 2));
        mutationApplied = true;
        const receipt = await writeSpiritFlixAdminReceipt({
          ...planned,
          status: "executed",
          targetPath: ORDER_FILE,
          affectedPaths: [ORDER_FILE],
          previewId,
        });
        return response(action, "execute", previewId, true, "Custom order saved.", {
          receipt,
          mutationApplied,
          preview: { targetPath: ORDER_FILE, affectedPaths: [ORDER_FILE], warnings: [] },
        });
      }
      case "requestJellyfinRescan": {
        const credentials = getServerJellyfinCredentials();
        if (!credentials) {
          throw new Error("Rescan action is not active yet because safe Jellyfin admin auth is unavailable.");
        }
        const targetPath = await assertAllowedPath(request.rescanPath ?? SPIRITFLIX_MEDIA_ROOT);
        assertExactPlannedPath(targetPath, planned.targetPath);
        const refresh = await fetch(`${credentials.serverUrl}/Library/Refresh`, {
          method: "POST",
          headers: { "X-Emby-Token": credentials.accessToken },
        });
        if (!refresh.ok) throw new Error(`Jellyfin rescan request failed (HTTP ${refresh.status}).`);
        mutationApplied = true;
        const receipt = await writeSpiritFlixAdminReceipt({
          ...planned,
          status: "executed",
          targetPath,
          affectedPaths: [targetPath],
          reversible: false,
          previewId,
        });
        return response(action, "execute", previewId, true, "Jellyfin rescan requested.", {
          receipt,
          mutationApplied,
          preview: { targetPath, affectedPaths: [targetPath], warnings: [] },
        });
      }
      default:
        return response(action, "execute", previewId, false, "Unknown action.");
    }
  } catch (error) {
    const failedReceipt: SpiritFlixAdminReceipt = {
      ...planned,
      id: randomUUID(),
      status: "failed",
      reason: error instanceof Error ? error.message : "Action failed.",
      affectedPaths: planned.affectedPaths,
      previewId,
    };
    const receipt = await writeSpiritFlixAdminReceipt(failedReceipt).catch(() => failedReceipt);
    return response(action, "execute", previewId, false, receipt.reason ?? "Action failed.", { mutationApplied, receipt });
  }
}

export function getSmokeRoot(): string {
  return SMOKE_ROOT;
}

export function validateOrderItemKey(key: string): boolean {
  return /^jellyfin:[^:]+$/.test(key) || /^path:[a-f0-9]{64}$/.test(key);
}

export function buildPathItemKey(filePath: string): string {
  return stableItemKey(filePath);
}

export function clearSpiritFlixAdminPreviewStore(): void {
  previewStore.clear();
}
