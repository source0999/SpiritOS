export const cartographerStopControlStatus = {
  killSwitchState: "unknown-fail-closed",
  backendEndpointAvailable: false,
  controlsPreviewOnly: true,
  executableControlsAvailable: false,
  durableWriteAvailable: false,
  workflowExecutionAuthorityGranted: false,
  queueAuthorityGranted: false,
  commandAuthorityGranted: false,
  writeAuthorityGranted: false,
  gitMutationAuthorityGranted: false,
  safeNextAction:
    "Treat kill switch state as blocking until an approved backend stop-control endpoint exists.",
  controls: [
    {
      id: "pause",
      label: "Pause",
      modeledTarget: "blocked",
      status: "preview-only",
      blockedReason: "No approved /map pause endpoint is available.",
    },
    {
      id: "cancel",
      label: "Cancel",
      modeledTarget: "cancelled",
      status: "preview-only",
      blockedReason: "No approved /map cancel endpoint is available.",
    },
    {
      id: "timeout",
      label: "Timeout",
      modeledTarget: "failed",
      status: "preview-only",
      blockedReason: "No approved /map timeout endpoint is available.",
    },
    {
      id: "retry",
      label: "Retry",
      modeledTarget: "running",
      status: "preview-only",
      blockedReason: "No approved /map retry endpoint is available.",
    },
  ],
} as const;
