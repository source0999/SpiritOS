const APPROVAL_TOKEN_ENDPOINT = "/v1/cartographer/approval-token/validate";
const APPROVAL_TOKEN_CONSUME_PREVIEW_ENDPOINT =
  "/v1/cartographer/approval-token/consume-preview";

export type CartographerApprovalTokenStatus = {
  available: boolean;
  runtimeStatus: string;
  approvalState: "valid" | "invalid" | "stale" | "missing";
  validationStatus: "accepted" | "rejected";
  validationOnly: boolean;
  accepted: boolean;
  laneId: string;
  requestedLaneId: string;
  singleAction: boolean;
  issuedByHuman: boolean;
  reasons: string[];
  reasonCodes: string[];
  reasonDetails: { code: string; message: string }[];
  authorityGranted: boolean;
  writeAuthorityGranted: boolean;
  commandAuthorityGranted: boolean;
  workflowAuthorityGranted: boolean;
  queueAuthorityGranted: boolean;
  gitAuthorityGranted: boolean;
  selfApprovalAllowed: boolean;
  selfApprovalBlocked: boolean;
  safeNextAction: string;
  detail: string;
  consumptionStatus: "eligible" | "blocked";
  consumptionPreviewOnly: boolean;
  consumptionEligible: boolean;
  consumptionReasons: string[];
  consumptionReasonDetails: { code: string; message: string }[];
  eventPreviewType: string;
};

const unavailableApprovalTokenStatus: CartographerApprovalTokenStatus = {
  available: false,
  runtimeStatus: "unavailable",
  approvalState: "missing",
  validationStatus: "rejected",
  validationOnly: true,
  accepted: false,
  laneId: "unknown",
  requestedLaneId: "unknown",
  singleAction: false,
  issuedByHuman: false,
  reasons: ["approval_token_validation_unavailable"],
  reasonCodes: [
    "approval_token_validation_unavailable",
    "approval_token_consumption_preview_unavailable",
  ],
  reasonDetails: [
    {
      code: "approval_token_validation_unavailable",
      message: "Approval-token validation status could not be read.",
    },
  ],
  authorityGranted: false,
  writeAuthorityGranted: false,
  commandAuthorityGranted: false,
  workflowAuthorityGranted: false,
  queueAuthorityGranted: false,
  gitAuthorityGranted: false,
  selfApprovalAllowed: false,
  selfApprovalBlocked: true,
  safeNextAction:
    "Stop and manually verify approval-token validation before any later authority expansion.",
  detail: "Approval-token validation status could not be read.",
  consumptionStatus: "blocked",
  consumptionPreviewOnly: true,
  consumptionEligible: false,
  consumptionReasons: ["approval_token_consumption_preview_unavailable"],
  consumptionReasonDetails: [
    {
      code: "approval_token_consumption_preview_unavailable",
      message: "Approval-token consumption preview status could not be read.",
    },
  ],
  eventPreviewType: "unavailable",
};

export async function getCartographerApprovalTokenStatus(
  origin: string | null,
): Promise<CartographerApprovalTokenStatus> {
  if (!origin) {
    return {
      ...unavailableApprovalTokenStatus,
      detail:
        "Request origin was unavailable, so approval-token validation was not fetched.",
    };
  }

  try {
    const [response, consumptionResponse] = await Promise.all([
      fetch(`${origin}${APPROVAL_TOKEN_ENDPOINT}`, {
        method: "GET",
        cache: "no-store",
      }),
      fetch(`${origin}${APPROVAL_TOKEN_CONSUME_PREVIEW_ENDPOINT}`, {
        method: "GET",
        cache: "no-store",
      }),
    ]);

    if (!response.ok) {
      return {
        ...unavailableApprovalTokenStatus,
        detail: `Approval-token validation endpoint returned HTTP ${response.status}.`,
      };
    }

    const payload: unknown = await response.json();
    const consumptionPayload: unknown = consumptionResponse.ok
      ? await consumptionResponse.json()
      : null;
    return normalizeApprovalTokenStatus(payload, consumptionPayload);
  } catch (error) {
    return {
      ...unavailableApprovalTokenStatus,
      detail:
        error instanceof Error
          ? `Approval-token validation request failed: ${error.message}`
          : "Approval-token validation request failed.",
    };
  }
}

function normalizeApprovalTokenStatus(
  payload: unknown,
  consumptionPayload: unknown,
): CartographerApprovalTokenStatus {
  if (!isRecord(payload)) {
    return {
      ...unavailableApprovalTokenStatus,
      detail: "Approval-token validation endpoint returned an unexpected payload shape.",
    };
  }

  const runtime = isRecord(payload.runtime) ? payload.runtime : {};
  const validation = isRecord(payload.validation) ? payload.validation : {};
  const consumptionRoot = isRecord(consumptionPayload) ? consumptionPayload : {};
  const consumptionRuntime = isRecord(consumptionRoot.runtime)
    ? consumptionRoot.runtime
    : {};
  const consumptionPreview = isRecord(consumptionRoot.preview)
    ? consumptionRoot.preview
    : {};
  const reasons = stringArray(validation.reasons);
  const consumptionReasons = stringArray(consumptionPreview.reasons);
  const reasonDetails = reasonDetailArray(validation.reason_details);
  const consumptionReasonDetails = reasonDetailArray(consumptionPreview.reason_details);
  const validationStatus =
    stringValue(validation.status) === "accepted" ? "accepted" : "rejected";
  const consumptionStatus =
    stringValue(consumptionPreview.status) === "eligible" ? "eligible" : "blocked";
  const reasonCodes = dedupeStrings([...reasons, ...consumptionReasons]);
  const approvalState = approvalStateFromReasons(
    validationStatus,
    reasonCodes,
  );
  const eventPreview = isRecord(consumptionPreview.approval_event_preview)
    ? consumptionPreview.approval_event_preview
    : {};
  const validationOnly =
    booleanValue(runtime.validation_only) ?? booleanValue(validation.validation_only) ?? true;
  const authorityGranted =
    booleanValue(validation.authority_granted) ??
    booleanValue(runtime.authority_granted) ??
    false;
  const commandAuthorityGranted =
    booleanValue(validation.command_authority_granted) ??
    booleanValue(runtime.command_authority_granted) ??
    false;

  return {
    available: true,
    runtimeStatus: stringValue(runtime.status) ?? "validation-only",
    approvalState,
    validationStatus,
    validationOnly,
    accepted: booleanValue(validation.accepted) ?? validationStatus === "accepted",
    laneId: stringValue(validation.lane_id) ?? "unknown",
    requestedLaneId: stringValue(validation.requested_lane_id) ?? "unknown",
    singleAction: booleanValue(validation.single_action) ?? false,
    issuedByHuman: booleanValue(validation.issued_by_human) ?? false,
    reasons,
    reasonCodes,
    reasonDetails,
    authorityGranted,
    writeAuthorityGranted:
      booleanValue(validation.write_authority_granted) ??
      booleanValue(runtime.write_authority_granted) ??
      false,
    commandAuthorityGranted,
    workflowAuthorityGranted:
      booleanValue(validation.workflow_authority_granted) ??
      booleanValue(runtime.workflow_authority_granted) ??
      false,
    queueAuthorityGranted:
      booleanValue(validation.queue_authority_granted) ??
      booleanValue(runtime.queue_authority_granted) ??
      false,
    gitAuthorityGranted:
      booleanValue(validation.git_authority_granted) ??
      booleanValue(runtime.git_authority_granted) ??
      false,
    selfApprovalAllowed: booleanValue(runtime.self_approval_allowed) ?? false,
    selfApprovalBlocked:
      reasons.includes("self_approval_rejected") ||
      booleanValue(runtime.self_approval_allowed) === false,
    safeNextAction:
      stringValue(consumptionPreview.safe_next_action) ??
      stringValue(validation.safe_next_action) ??
      "Keep approval-token runtime validation-only and require human review.",
    detail:
      validationStatus === "accepted"
        ? "Approval-token validation accepted a payload but grants no authority."
        : "Approval-token validation is fail-closed; the preview rejection is display-only.",
    consumptionStatus,
    consumptionPreviewOnly:
      booleanValue(consumptionPreview.preview_only) ??
      booleanValue(consumptionRuntime.preview_only) ??
      true,
    consumptionEligible:
      booleanValue(consumptionPreview.eligible) ?? consumptionStatus === "eligible",
    consumptionReasons,
    consumptionReasonDetails,
    eventPreviewType: stringValue(eventPreview.event_type) ?? "not-reported",
  };
}

function approvalStateFromReasons(
  validationStatus: "accepted" | "rejected",
  reasonCodes: readonly string[],
): CartographerApprovalTokenStatus["approvalState"] {
  if (validationStatus === "accepted") {
    return "valid";
  }

  if (
    reasonCodes.some((reason) =>
      [
        "approval_token_validation_unavailable",
        "malformed_payload",
      ].includes(reason) || reason.startsWith("missing_required_field:")
    )
  ) {
    return "missing";
  }

  if (
    reasonCodes.some((reason) =>
      [
        "token_expired",
        "token_stale",
        "stale_head",
        "stale_dirty_tree",
        "token_validation:token_expired",
        "token_validation:token_stale",
        "token_validation:stale_head",
        "token_validation:stale_dirty_tree",
      ].includes(reason)
    )
  ) {
    return "stale";
  }

  return "invalid";
}

function booleanValue(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function stringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string");
}

function reasonDetailArray(value: unknown): { code: string; message: string }[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((item) => {
    if (!isRecord(item)) {
      return [];
    }

    const code = stringValue(item.code);
    const message = stringValue(item.message);
    if (!code || !message) {
      return [];
    }

    return [{ code, message }];
  });
}

function dedupeStrings(values: readonly string[]): string[] {
  return Array.from(new Set(values));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
