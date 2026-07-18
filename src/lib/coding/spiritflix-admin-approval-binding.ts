import "server-only";

import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

import { getSpiritFlixManualModelForItem } from "@/lib/spiritflix/manual-models";
import { getSpiritFlixManualTagsForItem } from "@/lib/spiritflix/manual-tags";
import { getSpiritFlixFaceLearningRequest } from "@/lib/spiritflix/face-learning";
import { resolveSpiritFlixAdminPath } from "@/lib/spiritflix/admin/paths";
import {
  getSmartAnalysisPath,
  metadataSidecarPath,
  previewSpiritFlixSmartBatch,
} from "@/lib/spiritflix/admin/smart";
import { resolveSpiritFlixSmartMediaRoot } from "@/lib/spiritflix/admin/smart/media-root";
import {
  getSpiritFlixAdminActionApprovalSnapshot,
  type SpiritFlixAdminActionApprovalSnapshot,
} from "@/lib/spiritflix/admin/actions";

export const SPIRITFLIX_ADMIN_MUTATION_PLAN_SCHEMA = "spiritflix-admin-mutation-plan/v2" as const;

export type SpiritFlixAdminApprovalWriter =
  | "admin-action"
  | "face-learning"
  | "library-smart-rescan"
  | "manual-model"
  | "manual-tags"
  | "smart-analysis"
  | "smart-batch";

export type SpiritFlixAdminApprovalBinding = {
  action: string;
  target: string;
  plan: {
    schema: typeof SPIRITFLIX_ADMIN_MUTATION_PLAN_SCHEMA;
    writer: SpiritFlixAdminApprovalWriter;
    mutation: Record<string, unknown>;
    expected_current_state_hash: string;
    expected_result_contract_hash: string;
  };
};

function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record).sort().map((key) => `${JSON.stringify(key)}:${canonical(record[key])}`).join(",")}}`;
  }
  return JSON.stringify(value) ?? "null";
}

export function hashSpiritFlixAdminState(value: unknown): string {
  return createHash("sha256").update(canonical(value)).digest("hex");
}

function record(value: unknown, reason: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(reason);
  return value as Record<string, unknown>;
}

function exactKeys(value: Record<string, unknown>, keys: readonly string[], reason: string): void {
  if (Object.keys(value).some((key) => !keys.includes(key))) throw new Error(reason);
}

function requiredString(value: unknown, reason: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(reason);
  return value.trim();
}

function optionalString(value: unknown, reason: string): string | undefined {
  if (value === undefined || value === null || value === "") return undefined;
  if (typeof value !== "string") throw new Error(reason);
  return value.trim() || undefined;
}

function stringArray(value: unknown, reason: string, options: { optional?: boolean } = {}): string[] | undefined {
  if (value === undefined && options.optional) return undefined;
  if (!Array.isArray(value) || value.some((entry) => typeof entry !== "string" || !entry.trim())) throw new Error(reason);
  return value.map((entry) => entry.trim());
}

function optionalBoolean(value: unknown, reason: string): boolean | undefined {
  if (value === undefined) return undefined;
  if (typeof value !== "boolean") throw new Error(reason);
  return value;
}

function optionalPositiveInteger(value: unknown, reason: string): number | undefined {
  if (value === undefined) return undefined;
  if (!Number.isInteger(value) || Number(value) < 1) throw new Error(reason);
  return Number(value);
}

async function pathState(candidate: string | undefined): Promise<Record<string, unknown>> {
  if (!candidate) return { exists: false, path: null };
  const resolved = path.resolve(candidate);
  try {
    const details = await fs.lstat(resolved);
    if (details.isSymbolicLink()) throw new Error("spiritflix_admin_state_symlink_forbidden");
    const state: Record<string, unknown> = {
      exists: true,
      is_directory: details.isDirectory(),
      is_file: details.isFile(),
      mtime_ms: Math.trunc(details.mtimeMs),
      path: resolved,
      size: details.size,
    };
    if (details.isFile() && details.size <= 1_048_576) {
      state.content_hash = createHash("sha256").update(await fs.readFile(resolved)).digest("hex");
    } else if (details.isDirectory()) {
      state.entries = (await fs.readdir(resolved)).sort();
    }
    return state;
  } catch (error) {
    if (error instanceof Error && "code" in error && error.code === "ENOENT") return { exists: false, path: resolved };
    throw error;
  }
}

function withoutApprovalId(input: Record<string, unknown>): Record<string, unknown> {
  const { approval_id: _approvalId, ...mutation } = input;
  return mutation;
}

async function adminActionState(snapshot: SpiritFlixAdminActionApprovalSnapshot) {
  return {
    preview_id: snapshot.previewId,
    action: snapshot.action,
    receipt: snapshot.receipt,
    affected_paths: await Promise.all(snapshot.receipt.affectedPaths.map((candidate) => pathState(candidate))),
  };
}

async function manualTagsBinding(input: Record<string, unknown>): Promise<Omit<SpiritFlixAdminApprovalBinding, "plan"> & { mutation: Record<string, unknown>; state: unknown }> {
  exactKeys(input, ["itemId", "filePath", "manualTags", "approval_id"], "spiritflix_admin_manual_tags_fields_invalid");
  const itemId = requiredString(input.itemId, "spiritflix_admin_item_id_invalid");
  const filePath = optionalString(input.filePath, "spiritflix_admin_file_path_invalid");
  const manualTags = stringArray(input.manualTags, "spiritflix_admin_manual_tags_invalid")!;
  const current = await getSpiritFlixManualTagsForItem(itemId, { lookupFilePath: filePath });
  return {
    action: "metadata.mutation",
    target: `spiritflix:videos:${itemId}:tags`,
    mutation: { itemId, ...(filePath ? { filePath } : {}), manualTags },
    state: { itemId: current.itemId, filePath: current.filePath ?? null, manualTags: current.manualTags },
  };
}

async function manualModelBinding(input: Record<string, unknown>): Promise<Omit<SpiritFlixAdminApprovalBinding, "plan"> & { mutation: Record<string, unknown>; state: unknown }> {
  exactKeys(input, ["itemId", "filePath", "modelName", "knownModelNames", "approval_id"], "spiritflix_admin_manual_model_fields_invalid");
  const itemId = requiredString(input.itemId, "spiritflix_admin_item_id_invalid");
  const filePath = optionalString(input.filePath, "spiritflix_admin_file_path_invalid");
  const modelName = requiredString(input.modelName, "spiritflix_admin_model_name_invalid");
  const knownModelNames = stringArray(input.knownModelNames, "spiritflix_admin_known_models_invalid", { optional: true });
  const current = await getSpiritFlixManualModelForItem(itemId, { lookupFilePath: filePath });
  return {
    action: "metadata.mutation",
    target: `spiritflix:videos:${itemId}:model`,
    mutation: { itemId, ...(filePath ? { filePath } : {}), modelName, ...(knownModelNames ? { knownModelNames } : {}) },
    state: { itemId: current.itemId, filePath: current.filePath ?? null, modelName: current.modelName },
  };
}

async function faceLearningBinding(input: Record<string, unknown>): Promise<Omit<SpiritFlixAdminApprovalBinding, "plan"> & { mutation: Record<string, unknown>; state: unknown }> {
  exactKeys(input, ["itemId", "filePath", "modelName", "sidecarPath", "faceGuess", "relatedItems", "approval_id"], "spiritflix_admin_face_learning_fields_invalid");
  const itemId = requiredString(input.itemId, "spiritflix_admin_item_id_invalid");
  const filePath = optionalString(input.filePath, "spiritflix_admin_file_path_invalid");
  const modelName = requiredString(input.modelName, "spiritflix_admin_model_name_invalid");
  const sidecarPath = optionalString(input.sidecarPath, "spiritflix_admin_sidecar_path_invalid");
  const faceGuess = input.faceGuess === undefined ? undefined : record(input.faceGuess, "spiritflix_admin_face_guess_invalid");
  if (faceGuess && typeof faceGuess.name !== "string") throw new Error("spiritflix_admin_face_guess_invalid");
  const relatedItems = input.relatedItems === undefined ? [] : Array.isArray(input.relatedItems)
    ? input.relatedItems.map((entry) => {
        const item = record(entry, "spiritflix_admin_related_items_invalid");
        exactKeys(item, ["itemId", "filePath"], "spiritflix_admin_related_items_invalid");
        const relatedItemId = requiredString(item.itemId, "spiritflix_admin_related_items_invalid");
        const relatedFilePath = optionalString(item.filePath, "spiritflix_admin_related_items_invalid");
        return { itemId: relatedItemId, ...(relatedFilePath ? { filePath: relatedFilePath } : {}) };
      })
    : (() => { throw new Error("spiritflix_admin_related_items_invalid"); })();
  return {
    action: "face.learning",
    target: `spiritflix:videos:${itemId}:face-learning`,
    mutation: { itemId, ...(filePath ? { filePath } : {}), modelName, ...(sidecarPath ? { sidecarPath } : {}), ...(faceGuess ? { faceGuess } : {}), relatedItems },
    state: {
      request: await getSpiritFlixFaceLearningRequest(itemId),
      file: await pathState(filePath),
      sidecar: await pathState(sidecarPath),
      related: await Promise.all(relatedItems.map((item) => pathState(item.filePath))),
    },
  };
}

async function smartAnalysisBinding(input: Record<string, unknown>): Promise<Omit<SpiritFlixAdminApprovalBinding, "plan"> & { mutation: Record<string, unknown>; state: unknown }> {
  exactKeys(input, ["path", "action", "review", "approval_id"], "spiritflix_admin_smart_analysis_fields_invalid");
  const targetPath = requiredString(input.path, "spiritflix_admin_path_invalid");
  const batchAction = requiredString(input.action, "spiritflix_admin_action_invalid");
  const review = input.review === undefined ? undefined : record(input.review, "spiritflix_admin_review_invalid");
  const { realPath } = await resolveSpiritFlixAdminPath(targetPath);
  const details = await fs.stat(realPath);
  const mediaRoot = resolveSpiritFlixSmartMediaRoot(realPath);
  const analysisPath = getSmartAnalysisPath(
    { videoPath: realPath, fileSizeBytes: details.size, mtimeMs: details.mtimeMs },
    { mediaRoot },
  );
  return {
    action: "smart.analysis",
    target: `spiritflix:smart-analysis:${targetPath}`,
    mutation: { path: targetPath, action: batchAction, ...(review ? { review } : {}) },
    state: {
      source: await pathState(realPath),
      analysis: await pathState(analysisPath),
      metadata: await pathState(metadataSidecarPath(realPath, mediaRoot)),
    },
  };
}

async function smartBatchBinding(input: Record<string, unknown>): Promise<Omit<SpiritFlixAdminApprovalBinding, "plan"> & { mutation: Record<string, unknown>; state: unknown }> {
  exactKeys(input, ["path", "paths", "action", "reviewMode", "editedFilenameSuggestion", "recursive", "maxItems", "force", "approval_id"], "spiritflix_admin_smart_batch_fields_invalid");
  const targetPath = optionalString(input.path, "spiritflix_admin_path_invalid");
  const paths = stringArray(input.paths, "spiritflix_admin_paths_invalid", { optional: true });
  if (!targetPath && (!paths || paths.length === 0)) throw new Error("spiritflix_admin_batch_target_invalid");
  const batchAction = requiredString(input.action, "spiritflix_admin_action_invalid");
  const reviewMode = optionalString(input.reviewMode, "spiritflix_admin_review_mode_invalid");
  const editedFilenameSuggestion = optionalString(input.editedFilenameSuggestion, "spiritflix_admin_edited_filename_invalid");
  const recursive = optionalBoolean(input.recursive, "spiritflix_admin_recursive_invalid");
  const maxItems = optionalPositiveInteger(input.maxItems, "spiritflix_admin_max_items_invalid");
  const force = optionalBoolean(input.force, "spiritflix_admin_force_invalid");
  const mutation = {
    ...(targetPath ? { path: targetPath } : {}),
    ...(paths ? { paths } : {}),
    action: batchAction,
    ...(reviewMode ? { reviewMode } : {}),
    ...(editedFilenameSuggestion ? { editedFilenameSuggestion } : {}),
    ...(recursive !== undefined ? { recursive } : {}),
    ...(maxItems !== undefined ? { maxItems } : {}),
    ...(force !== undefined ? { force } : {}),
  };
  const preview = await previewSpiritFlixSmartBatch({
    path: targetPath,
    paths,
    recursive,
    maxItems,
    force,
  });
  const sidecars = await Promise.all(preview.items.map(async (item) => {
    const details = await fs.stat(item.path);
    const mediaRoot = resolveSpiritFlixSmartMediaRoot(item.path);
    return pathState(getSmartAnalysisPath(
      { videoPath: item.path, fileSizeBytes: details.size, mtimeMs: details.mtimeMs },
      { mediaRoot },
    ));
  }));
  return {
    action: "smart.batch",
    target: `spiritflix:smart-batch:${targetPath ?? paths!.join(",")}`,
    mutation,
    state: { root: await pathState(targetPath), sidecars },
  };
}

async function adminActionBinding(input: Record<string, unknown>): Promise<Omit<SpiritFlixAdminApprovalBinding, "plan"> & { mutation: Record<string, unknown>; state: unknown }> {
  const mutation = withoutApprovalId(input);
  const previewId = optionalString(mutation.confirmToken ?? mutation.previewId, "spiritflix_admin_preview_id_invalid");
  if (!previewId) throw new Error("spiritflix_admin_preview_id_required");
  const snapshot = getSpiritFlixAdminActionApprovalSnapshot(previewId);
  if (!snapshot) throw new Error("spiritflix_admin_preview_not_found");
  if ((mutation.action !== undefined && mutation.action !== snapshot.action) || (mutation.mode ?? mutation.phase) !== "execute") {
    throw new Error("spiritflix_admin_preview_mismatch");
  }
  const exactMutation = {
    ...snapshot.payload,
    action: snapshot.action,
    mode: "execute",
    confirmToken: previewId,
  } as Record<string, unknown>;
  delete exactMutation.phase;
  delete exactMutation.previewId;
  return {
    action: "admin.action",
    target: `spiritflix:admin-actions:${snapshot.action}`,
    mutation: exactMutation,
    state: await adminActionState(snapshot),
  };
}

async function libraryRescanBinding(input: Record<string, unknown>): Promise<Omit<SpiritFlixAdminApprovalBinding, "plan"> & { mutation: Record<string, unknown>; state: unknown }> {
  exactKeys(input, ["approval_id"], "spiritflix_admin_library_rescan_fields_invalid");
  const statusPath = path.join(process.cwd(), "scripts", "media", "spiritflix_library_smart_rescan_status.json");
  return {
    action: "index.rebuild",
    target: "spiritflix:library-smart-rescan",
    mutation: {
      runner: "face-organizer",
      version: 2,
      source: "/mnt/spirit-8tb/media/yes",
      modelLimit: Math.max(1, Number.parseInt(process.env.SPIRITFLIX_SMART_RESCAN_MODEL_LIMIT ?? "80", 10) || 80),
      videoLimit: Math.max(1, Number.parseInt(process.env.SPIRITFLIX_SMART_RESCAN_VIDEO_LIMIT ?? "120", 10) || 120),
      contextId: process.env.SPIRITFLIX_FACE_ORGANIZER_CTX_ID ?? "-1",
      cpuSet: process.env.SPIRITFLIX_FACE_ORGANIZER_CPUSET ?? (process.platform === "linux" ? "6,7" : ""),
      threads: Math.max(1, Number.parseInt(process.env.SPIRITFLIX_FACE_ORGANIZER_THREADS ?? "2", 10) || 2),
    },
    state: await pathState(statusPath),
  };
}

export async function resolveSpiritFlixAdminApprovalBinding(
  writer: SpiritFlixAdminApprovalWriter,
  rawMutation: unknown,
): Promise<SpiritFlixAdminApprovalBinding> {
  const input = record(rawMutation, "spiritflix_admin_mutation_invalid");
  const resolved = writer === "manual-tags"
    ? await manualTagsBinding(input)
    : writer === "manual-model"
      ? await manualModelBinding(input)
      : writer === "face-learning"
        ? await faceLearningBinding(input)
        : writer === "smart-analysis"
          ? await smartAnalysisBinding(input)
          : writer === "smart-batch"
            ? await smartBatchBinding(input)
            : writer === "admin-action"
              ? await adminActionBinding(input)
              : writer === "library-smart-rescan"
                ? await libraryRescanBinding(input)
                : (() => { throw new Error("operator_preview_writer_forbidden"); })();

  const expectedCurrentStateHash = hashSpiritFlixAdminState(resolved.state);
  const expectedResultContractHash = hashSpiritFlixAdminState({
    action: resolved.action,
    mutation: resolved.mutation,
    target: resolved.target,
    writer,
  });
  return {
    action: resolved.action,
    target: resolved.target,
    plan: {
      schema: SPIRITFLIX_ADMIN_MUTATION_PLAN_SCHEMA,
      writer,
      mutation: resolved.mutation,
      expected_current_state_hash: expectedCurrentStateHash,
      expected_result_contract_hash: expectedResultContractHash,
    },
  };
}
