"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { isSpiritFlixAdminTrashPath } from "@/lib/spiritflix/admin/path-rules";
import type {
  SpiritFlixAdminActionName,
  SpiritFlixAdminActionResponse,
  SpiritFlixAdminItem,
  SpiritFlixAdminMetadataSidecar,
  SpiritFlixAdminReceipt,
} from "@/lib/spiritflix/admin/types";

interface SpiritFlixAdminActionDialogProps {
  item: SpiritFlixAdminItem | null;
  currentPath: string;
  initialAction?: SpiritFlixAdminActionName;
  onClose: () => void;
  onComplete: (message: string, receipt?: SpiritFlixAdminReceipt) => void;
}

type PendingAction = {
  action: SpiritFlixAdminActionName;
  label: string;
  buildRequest: () => Record<string, unknown>;
};

const AUTO_PREVIEW_ACTIONS = new Set<SpiritFlixAdminActionName>([
  "softDelete",
  "restore",
  "rename",
  "move",
  "writeMetadata",
]);

async function runAction(body: Record<string, unknown>): Promise<SpiritFlixAdminActionResponse> {
  const response = await fetch("/api/spiritflix/admin/actions", {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  let payload: SpiritFlixAdminActionResponse & { error?: string };
  try {
    payload = (await response.json()) as SpiritFlixAdminActionResponse & { error?: string };
  } catch {
    throw new Error(`Action API returned a non-JSON response (HTTP ${response.status}).`);
  }
  if (!response.ok && !payload.previewId) {
    throw new Error(payload.error ?? payload.message ?? `Action failed (HTTP ${response.status}).`);
  }
  return payload;
}

function shouldAutoPreview(action: SpiritFlixAdminActionName | undefined, item: SpiritFlixAdminItem | null): boolean {
  return Boolean(action && AUTO_PREVIEW_ACTIONS.has(action) && item?.path);
}

export function SpiritFlixAdminActionDialog({ item, currentPath, initialAction, onClose, onComplete }: SpiritFlixAdminActionDialogProps) {
  const [pending, setPending] = useState<PendingAction | null>(null);
  const [preview, setPreview] = useState<SpiritFlixAdminActionResponse | null>(null);
  const [resultReceipt, setResultReceipt] = useState<SpiritFlixAdminReceipt | null>(null);
  const [folderName, setFolderName] = useState("");
  const [newName, setNewName] = useState(item?.name ?? "");
  const [targetFolder, setTargetFolder] = useState(item?.parentPath ?? currentPath);
  const [displayTitle, setDisplayTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(() => shouldAutoPreview(initialAction, item));
  const [previewError, setPreviewError] = useState<string | null>(null);

  const isTrashItem = useMemo(() => Boolean(item?.path && isSpiritFlixAdminTrashPath(item.path)), [item?.path]);
  const contextLabel = item?.name ?? currentPath.split("/").filter(Boolean).pop() ?? "current folder";
  const parentPath = item?.parentPath ?? currentPath;
  const focusedAction = initialAction ?? null;
  const showAllActions = !focusedAction;
  const isFocusedDestructive = focusedAction === "softDelete" || focusedAction === "restore";

  function actionVisible(action: SpiritFlixAdminActionName): boolean {
    return showAllActions || focusedAction === action;
  }

  const dialogTitle = focusedAction
    ? `${focusedAction === "writeMetadata" ? "Edit metadata" : focusedAction === "createFolder" ? "New folder" : focusedAction === "softDelete" ? "Soft delete" : focusedAction.charAt(0).toUpperCase() + focusedAction.slice(1)}: ${contextLabel}`
    : `Manage: ${contextLabel}`;

  const buildActionConfig = useCallback(
    (action: SpiritFlixAdminActionName): PendingAction | null => {
      switch (action) {
        case "createFolder":
          if (!folderName.trim()) return null;
          return {
            action: "createFolder",
            label: "Create folder",
            buildRequest: () => ({ action: "createFolder", parentPath, name: folderName }),
          };
        case "rename":
          if (!item?.path || !newName.trim()) return null;
          return {
            action: "rename",
            label: "Rename",
            buildRequest: () => ({ action: "rename", sourcePath: item.path, name: newName }),
          };
        case "move":
          if (!item?.path) return null;
          return {
            action: "move",
            label: "Move",
            buildRequest: () => ({ action: "move", sourcePath: item.path, targetPath: targetFolder }),
          };
        case "softDelete":
          if (!item?.path) return null;
          return {
            action: "softDelete",
            label: "Soft delete",
            buildRequest: () => ({ action: "softDelete", sourcePath: item.path }),
          };
        case "writeMetadata":
          if (!item?.path) return null;
          return {
            action: "writeMetadata",
            label: "Edit metadata",
            buildRequest: () => ({
              action: "writeMetadata",
              sourcePath: item.path,
              metadata: {
                ...(displayTitle ? { displayTitle } : {}),
                ...(notes ? { notes } : {}),
              },
            }),
          };
        case "restore":
          if (!item?.path) return null;
          return {
            action: "restore",
            label: "Restore",
            buildRequest: () => ({ action: "restore", sourcePath: item.path }),
          };
        default:
          return null;
      }
    },
    [displayTitle, folderName, item?.path, newName, notes, parentPath, targetFolder],
  );

  const startAction = useCallback(async (config: PendingAction) => {
    setPending(config);
    setMessage("");
    setPreviewError(null);
    setResultReceipt(null);
    setBusy(true);
    try {
      const result = await runAction({ ...config.buildRequest(), mode: "preview" });
      setPreview(result);
      setMessage(result.message);
      if (!result.allowed) {
        setPreviewError(result.message || "Preview was blocked.");
      }
    } catch (error) {
      const text = error instanceof Error ? error.message : "Preview failed.";
      setMessage(text);
      setPreviewError(text);
      setPreview(null);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (!initialAction) return;
    const config = buildActionConfig(initialAction);
    if (!config) {
      if (AUTO_PREVIEW_ACTIONS.has(initialAction) && !item?.path) {
        setPreviewError("Cannot preview this action — the selected item has no filesystem path.");
      }
      setBusy(false);
      return;
    }
    void startAction(config);
    // Only auto-preview when the dialog opens for a specific item/action — not when rename/move fields change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialAction, item?.id, item?.path]);

  async function confirmAction() {
    if (!pending || !preview?.previewId || !preview.allowed) return;
    setBusy(true);
    try {
      const result = await runAction({
        ...pending.buildRequest(),
        mode: "execute",
        confirmToken: preview.previewId,
      });
      setMessage(result.message);
      if (result.receipt) setResultReceipt(result.receipt);
      if (result.allowed) {
        onComplete(result.message, result.receipt);
        onClose();
        return;
      }
      setPreviewError(result.message || "Execute was blocked.");
    } catch (error) {
      const text = error instanceof Error ? error.message : "Execute failed.";
      setMessage(text);
      setPreviewError(text);
    } finally {
      setBusy(false);
    }
  }

  const metadataPayload: SpiritFlixAdminMetadataSidecar = {
    ...(displayTitle ? { displayTitle } : {}),
    ...(notes ? { notes } : {}),
  };

  const affectedPaths = preview?.preview?.affectedPaths ?? preview?.receipt?.affectedPaths ?? [];
  const showPreviewButtons =
    showAllActions ||
    focusedAction === "createFolder" ||
    focusedAction === "rename" ||
    focusedAction === "move" ||
    focusedAction === "writeMetadata";

  const confirmLabel =
    pending?.action === "softDelete"
      ? "Confirm — move to trash"
      : pending?.action === "restore"
        ? "Confirm — restore from trash"
        : "Confirm execute";

  const panel = (
    <div
      className="spiritflix-admin-action-dialog"
      role="dialog"
      aria-label="SpiritFlix admin actions"
      aria-modal="true"
      onMouseDown={(event) => event.stopPropagation()}
    >
      <button className="spiritflix-admin-action-dialog__backdrop" type="button" aria-label="Close dialog" onClick={onClose} />
      <div className="spiritflix-admin-action-dialog__panel" onClick={(event) => event.stopPropagation()}>
        <h3>{dialogTitle}</h3>
        <p className="spiritflix-admin-action-dialog__hint">
          Every write action requires preview and confirmation. Soft delete moves items to SpiritFlix trash — not permanent delete.
        </p>

        {item?.path ? (
          <p className="spiritflix-admin-action-dialog__source">
            <strong>Source:</strong> {item.path}
          </p>
        ) : null}

        {busy && !preview ? (
          <p className="spiritflix-admin-action-dialog__status" role="status">
            Loading preview…
          </p>
        ) : null}

        {previewError ? (
          <p className="spiritflix-admin-action-dialog__error" role="alert">
            {previewError}
          </p>
        ) : null}

        {preview ? (
          <div className="spiritflix-admin-action-dialog__preview">
            <p>
              <strong>{pending?.label ?? "Preview"}:</strong> {message}
            </p>
            {preview.riskLevel ? <p>Risk level: {preview.riskLevel}</p> : null}
            {preview.preview?.reversible === false ? (
              <p className="spiritflix-admin-action-dialog__warning">This action is not reversible.</p>
            ) : null}
            <ul>
              {(preview.preview?.warnings ?? []).map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
            <p className="spiritflix-admin-action-dialog__paths">
              <strong>Affected paths:</strong>
            </p>
            <ul className="spiritflix-admin-action-dialog__path-list">
              {affectedPaths.length ? (
                affectedPaths.map((affectedPath) => <li key={affectedPath}>{affectedPath}</li>)
              ) : (
                <li>No paths returned by preview.</li>
              )}
            </ul>
          </div>
        ) : null}

        <div className="spiritflix-admin-action-dialog__fields">
          {actionVisible("createFolder") ? (
            <label>
              New folder name
              <input value={folderName} onChange={(event) => setFolderName(event.target.value)} placeholder="folder-name" />
            </label>
          ) : null}
          {item && actionVisible("rename") ? (
            <label>
              Rename to
              <input value={newName} onChange={(event) => setNewName(event.target.value)} />
            </label>
          ) : null}
          {item && actionVisible("move") ? (
            <label>
              Move to parent folder
              <input value={targetFolder} onChange={(event) => setTargetFolder(event.target.value)} />
            </label>
          ) : null}
          {item && actionVisible("writeMetadata") ? (
            <>
              <label>
                Display title (metadata)
                <input value={displayTitle} onChange={(event) => setDisplayTitle(event.target.value)} placeholder="Optional sidecar title" />
              </label>
              <label>
                Notes (metadata)
                <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={2} placeholder="SpiritFlix-only notes" />
              </label>
            </>
          ) : null}
        </div>

        {showPreviewButtons ? (
          <div className="spiritflix-admin-action-dialog__buttons">
            {actionVisible("createFolder") ? (
              <button
                type="button"
                disabled={busy || !folderName.trim()}
                onClick={() =>
                  void startAction({
                    action: "createFolder",
                    label: "Create folder",
                    buildRequest: () => ({ action: "createFolder", parentPath, name: folderName }),
                  })
                }
              >
                Preview new folder
              </button>
            ) : null}

            {item && !isTrashItem && actionVisible("rename") ? (
              <button
                type="button"
                disabled={busy || !newName.trim()}
                onClick={() =>
                  void startAction({
                    action: "rename",
                    label: "Rename",
                    buildRequest: () => ({ action: "rename", sourcePath: item.path, name: newName }),
                  })
                }
              >
                Preview rename
              </button>
            ) : null}
            {item && !isTrashItem && actionVisible("move") ? (
              <button
                type="button"
                disabled={busy || !item.path}
                onClick={() =>
                  void startAction({
                    action: "move",
                    label: "Move",
                    buildRequest: () => ({ action: "move", sourcePath: item.path, targetPath: targetFolder }),
                  })
                }
              >
                Preview move
              </button>
            ) : null}
            {item && !isTrashItem && actionVisible("softDelete") ? (
              <button
                type="button"
                disabled={busy || !item.path}
                onClick={() =>
                  void startAction({
                    action: "softDelete",
                    label: "Soft delete",
                    buildRequest: () => ({ action: "softDelete", sourcePath: item.path }),
                  })
                }
              >
                Preview soft delete
              </button>
            ) : null}
            {item && !isTrashItem && actionVisible("writeMetadata") ? (
              <button
                type="button"
                disabled={busy || !item.path}
                onClick={() =>
                  void startAction({
                    action: "writeMetadata",
                    label: "Edit metadata",
                    buildRequest: () => ({ action: "writeMetadata", sourcePath: item.path, metadata: metadataPayload }),
                  })
                }
              >
                Preview metadata
              </button>
            ) : null}

            {item && isTrashItem && actionVisible("restore") ? (
              <button
                type="button"
                disabled={busy || !item.path}
                onClick={() =>
                  void startAction({
                    action: "restore",
                    label: "Restore",
                    buildRequest: () => ({ action: "restore", sourcePath: item.path }),
                  })
                }
              >
                Preview restore
              </button>
            ) : null}

            {showAllActions ? (
              <>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    void startAction({
                      action: "saveOrder",
                      label: "Save order",
                      buildRequest: () => ({
                        action: "saveOrder",
                        order: {
                          version: 1,
                          updatedAt: new Date().toISOString(),
                          groups: [
                            {
                              id: "smoke",
                              name: "Smoke shelf",
                              itemKeys: ["path:0000000000000000000000000000000000000000000000000000000000000000"],
                            },
                          ],
                        },
                      }),
                    })
                  }
                >
                  Preview save order
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    void startAction({
                      action: "requestJellyfinRescan",
                      label: "Rescan",
                      buildRequest: () => ({ action: "requestJellyfinRescan", rescanPath: currentPath }),
                    })
                  }
                >
                  Preview Jellyfin rescan
                </button>
              </>
            ) : null}
          </div>
        ) : null}

        {!preview && message && !previewError ? <p className="spiritflix-admin-action-dialog__status">{message}</p> : null}

        {resultReceipt ? (
          <div className="spiritflix-admin-action-dialog__receipt">
            <p>
              <strong>Receipt:</strong> {resultReceipt.id}
            </p>
            <p>Status: {resultReceipt.status}</p>
            {resultReceipt.targetPath ? <p>Target: {resultReceipt.targetPath}</p> : null}
          </div>
        ) : null}

        <div className="spiritflix-admin-action-dialog__footer">
          {isFocusedDestructive && !preview && !busy ? (
            <button
              type="button"
              className="spiritflix-admin-action-dialog__primary"
              disabled={!item?.path}
              onClick={() => {
                const config = buildActionConfig(focusedAction);
                if (config) void startAction(config);
              }}
            >
              Run preview
            </button>
          ) : null}
          {preview ? (
            <button
              type="button"
              className="spiritflix-admin-action-dialog__primary is-confirm"
              disabled={busy || !preview.allowed}
              onClick={() => void confirmAction()}
            >
              {confirmLabel}
            </button>
          ) : null}
          {previewError && isFocusedDestructive ? (
            <button
              type="button"
              className="spiritflix-admin-action-dialog__primary"
              disabled={busy || !item?.path}
              onClick={() => {
                const config = buildActionConfig(focusedAction);
                if (config) void startAction(config);
              }}
            >
              Retry preview
            </button>
          ) : null}
          <button type="button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );

  if (typeof document === "undefined") return null;
  return createPortal(panel, document.body);
}
