export type DesignStudioCriticInput = {
  anti_template_verdict?: string;
  anti_template_verdict_id?: string;
  desktop_screenshot_hash?: string;
  mobile_screenshot_hash?: string;
  template_signal_count?: number;
  trace_id?: string;
};

export function runDesignStudioCritic(input: DesignStudioCriticInput) {
  const blockers = [
    input.desktop_screenshot_hash ? null : "missing_desktop_screenshot_hash",
    input.mobile_screenshot_hash ? null : "missing_mobile_screenshot_hash",
    input.anti_template_verdict_id ? null : "missing_anti_template_verdict_id",
    input.trace_id ? null : "missing_trace_id",
  ].filter(Boolean);

  const criticVerdictId = `critic-${(input.trace_id ?? "missing-trace").replace(/[^a-z0-9._-]+/gi, "-")}`;
  if (blockers.length > 0) {
    return {
      blockers,
      critic_verdict: "DESIGN_CRITIC_BLOCKED",
      critic_verdict_id: criticVerdictId,
      references: {
        anti_template_verdict_id: input.anti_template_verdict_id ?? null,
        desktop_screenshot_hash: input.desktop_screenshot_hash ?? null,
        mobile_screenshot_hash: input.mobile_screenshot_hash ?? null,
        trace_id: input.trace_id ?? null,
      },
    };
  }

  const needsRepair =
    input.anti_template_verdict === "GENERIC_TEMPLATE_REJECT" ||
    input.anti_template_verdict === "GENERIC_TEMPLATE_REPAIR_REQUIRED" ||
    (input.template_signal_count ?? 0) >= 2;

  return {
    blockers: [],
    critic_verdict: needsRepair ? "DESIGN_CRITIC_REPAIR_REQUIRED" : "DESIGN_CRITIC_APPROVED_PREVIEW",
    critic_verdict_id: criticVerdictId,
    references: {
      anti_template_verdict_id: input.anti_template_verdict_id,
      desktop_screenshot_hash: input.desktop_screenshot_hash,
      mobile_screenshot_hash: input.mobile_screenshot_hash,
      trace_id: input.trace_id,
    },
    repair_required: needsRepair,
  };
}
