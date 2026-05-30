import {
  formatHermesUsedForRunStatus,
  type CodingProviderModelTruth,
} from "@/lib/coding/model-provider-status";
import { formatChangedFilesDiagnosticsLines, type ChangedFilesDiagnostics } from "@/lib/coding/changed-files-diagnostics";

export function providerModelDiagnosticLines(truth: CodingProviderModelTruth): string[] {
  return [
    `provider: ${truth.providerLabel}`,
    `model: ${truth.modelLabel}`,
    `configured_model: ${truth.configuredModel}`,
    `runtime_route_model: ${truth.runtimeRouteModel}`,
    `provider_model_source: ${truth.source}`,
    `provider_model_status: ${truth.status}`,
    `provider_model_probe_ok: ${
      truth.providerModelProbeOk === null || truth.providerModelProbeOk === undefined
        ? "unknown"
        : truth.providerModelProbeOk
    }`,
    `provider_model_selected_via: ${truth.providerModelSelectedVia ?? "unknown"}`,
    `provider_call_made: ${truth.providerCallMade}`,
    `provider_call_authorized: ${truth.providerCallAuthorized}`,
    `model_called_for_generation: ${truth.modelCalledForGeneration ?? "none"}`,
    `hermes_lane_available: ${truth.hermesLaneAvailable}`,
    `configured_local_model_is_hermes: ${
      truth.configuredModelIsHermes === null
        ? "unknown"
        : truth.configuredModelIsHermes
          ? "yes"
          : "no"
    }`,
    `hermes_used_for_this_run: ${formatHermesUsedForRunStatus(truth)}`,
    truth.providerCallMade
      ? "provider_call_note: live provider route was used for this run"
      : "provider_call_note: deterministic preview path; no Hermes generation call was required",
  ];
}

export function providerAndChangedFilesDiagnosticLines(
  truth: CodingProviderModelTruth,
  changedFiles: ChangedFilesDiagnostics,
): string[] {
  return [...providerModelDiagnosticLines(truth), ...formatChangedFilesDiagnosticsLines(changedFiles)];
}
