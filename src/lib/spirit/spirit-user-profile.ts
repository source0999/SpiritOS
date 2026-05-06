// ── spirit-user-profile - local-only editable prefs (Prompt 10A, no server memory) ─
// > Full learning/RAG/sync are later prompts - this is transparent localStorage.

import type { ModelProfileId } from "@/lib/spirit/model-profile.types";

export const SPIRIT_USER_PROFILE_LS = "spirit:userProfile:v1";
export const PERSONALIZATION_SUMMARY_MAX_CLIENT = 1200;

export type SpiritUserPreferenceConfidence = "low" | "medium" | "high";
export type SpiritPreferenceCategory =
  | "communication"
  | "workflow"
  | "research"
  | "mode"
  | "ui"
  | "other";

export type SpiritResearchSettingsV1 = {
  webSearchDefaultResearcher: boolean;
  preferredSourceAge: "5y" | "any";
  preferredSourceTypes: string[];
  requireCitationsResearcher: boolean;
  includeFullSourceList: boolean;
  warnOnSearchFailure: boolean;
  planFirstDeepResearchLater: boolean;
};

export function defaultResearchSettings(): SpiritResearchSettingsV1 {
  return {
    webSearchDefaultResearcher: true,
    preferredSourceAge: "5y",
    preferredSourceTypes: [
      "academic",
      "professional",
      "government",
      "primary sources",
      "credible news",
    ],
    requireCitationsResearcher: true,
    includeFullSourceList: true,
    warnOnSearchFailure: true,
    planFirstDeepResearchLater: false,
  };
}

export type SpiritUserPreferenceSource = "manual" | "inferred" | "default";

export type SpiritUserPreferenceRow = {
  id: string;
  label: string;
  value: string;
  source?: SpiritUserPreferenceSource;
  wrongPerspective?: boolean;
  confidence?: SpiritUserPreferenceConfidence;
  category?: SpiritPreferenceCategory;
};

export type SpiritUserProfileV1 = {
  version: 1;
  /** When false, client skips personalizationSummary on /api/spirit */
  sendPersonalizationToServer: boolean;
  preferences: SpiritUserPreferenceRow[];
  researchSettings?: SpiritResearchSettingsV1;
};

function uid(): string {
  try {
    if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  } catch {
    /* ignore */
  }
  return `pref_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

export const DEFAULT_SPIRIT_USER_PREFERENCES: SpiritUserPreferenceRow[] = [
  {
    id: "tone",
    label: "Communication style",
    value: "Casual, conversational; no customer-service glaze.",
    source: "default",
  },
  {
    id: "length",
    label: "Response length preference",
    value: "Concise by default; expand only when I ask for depth or a report.",
    source: "default",
  },
  {
    id: "writing",
    label: "Writing / formatting",
    value: "Avoid em dashes; prefer hyphen or comma.",
    source: "default",
  },
  {
    id: "workflow",
    label: "Work style",
    value: "Practical plans, senior-dev analysis, mobile-first with desktop still testable.",
    source: "default",
  },
  {
    id: "priorities",
    label: "Current build priorities",
    value: "Transparent status signals; local AI / homelab workflows; AI-native coding.",
    source: "default",
  },
  {
    id: "interests",
    label: "Interests / recurring themes",
    value: "ARPA-style planning before big Cursor dumps; SpiritOS chat workspace polish.",
    source: "default",
  },
  {
    id: "dislikes",
    label: "Frustration triggers / dislikes",
    value: "Bland support-agent replies; overlong casual answers; hidden chain-of-thought cosplay.",
    source: "default",
  },
  {
    id: "research",
    label: "Research expectations",
    value: "Clinical / psychedelic topics handled professionally; citations required in Researcher mode.",
    source: "default",
  },
  {
    id: "confidence",
    label: "Confidence level (self-reported)",
    value: "Medium - prefers receipts and sources for factual claims.",
    source: "default",
  },
];

export function defaultSpiritUserProfile(): SpiritUserProfileV1 {
  return {
    version: 1,
    sendPersonalizationToServer: true,
    preferences: DEFAULT_SPIRIT_USER_PREFERENCES.map((p) => ({ ...p, id: p.id || uid() })),
    researchSettings: defaultResearchSettings(),
  };
}

export function loadSpiritUserProfile(): SpiritUserProfileV1 {
  if (typeof window === "undefined") return defaultSpiritUserProfile();
  try {
    const raw = window.localStorage.getItem(SPIRIT_USER_PROFILE_LS);
    if (!raw) return defaultSpiritUserProfile();
    const parsed = JSON.parse(raw) as Partial<SpiritUserProfileV1>;
    if (parsed?.version !== 1 || !Array.isArray(parsed.preferences)) {
      return defaultSpiritUserProfile();
    }
    const prefs: SpiritUserPreferenceRow[] = [];
    for (const row of parsed.preferences) {
      if (!row || typeof row !== "object") continue;
      const r = row as Record<string, unknown>;
      const label = typeof r.label === "string" ? r.label.trim() : "";
      const value = typeof r.value === "string" ? r.value.trim() : "";
      const id = typeof r.id === "string" && r.id.trim() ? r.id.trim() : uid();
      if (!label || !value) continue;
      const srcRaw = typeof r.source === "string" ? r.source.trim().toLowerCase() : "";
      const source: SpiritUserPreferenceSource =
        srcRaw === "manual" || srcRaw === "inferred" || srcRaw === "default" ? srcRaw : "default";
      const wrongPerspective = r.wrongPerspective === true;
      const rowOut: SpiritUserPreferenceRow = { id, label, value, source };
      if (wrongPerspective) rowOut.wrongPerspective = true;
      const confRaw = typeof r.confidence === "string" ? r.confidence.trim().toLowerCase() : "";
      if (confRaw === "low" || confRaw === "medium" || confRaw === "high") {
        rowOut.confidence = confRaw;
      }
      const catRaw = typeof r.category === "string" ? r.category.trim().toLowerCase() : "";
      const cats: SpiritPreferenceCategory[] = [
        "communication",
        "workflow",
        "research",
        "mode",
        "ui",
        "other",
      ];
      if (cats.includes(catRaw as SpiritPreferenceCategory)) {
        rowOut.category = catRaw as SpiritPreferenceCategory;
      }
      prefs.push(rowOut);
    }
    const rsIn = parsed.researchSettings;
    let researchSettings: SpiritResearchSettingsV1 = defaultResearchSettings();
    if (rsIn && typeof rsIn === "object") {
      const rs = rsIn as Record<string, unknown>;
      const base = defaultResearchSettings();
      researchSettings = {
        ...base,
        webSearchDefaultResearcher:
          rs.webSearchDefaultResearcher === false ? false : base.webSearchDefaultResearcher,
        preferredSourceAge: rs.preferredSourceAge === "any" ? "any" : base.preferredSourceAge,
        preferredSourceTypes: Array.isArray(rs.preferredSourceTypes)
          ? (rs.preferredSourceTypes as unknown[]).filter((x) => typeof x === "string") as string[]
          : base.preferredSourceTypes,
        requireCitationsResearcher: rs.requireCitationsResearcher === false ? false : true,
        includeFullSourceList: rs.includeFullSourceList === false ? false : true,
        warnOnSearchFailure: rs.warnOnSearchFailure === false ? false : true,
        planFirstDeepResearchLater: rs.planFirstDeepResearchLater === true,
      };
    }
    return {
      version: 1,
      sendPersonalizationToServer: parsed.sendPersonalizationToServer !== false,
      preferences: prefs.length ? prefs : defaultSpiritUserProfile().preferences,
      researchSettings,
    };
  } catch {
    return defaultSpiritUserProfile();
  }
}

export function saveSpiritUserProfile(profile: SpiritUserProfileV1): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(SPIRIT_USER_PROFILE_LS, JSON.stringify(profile));
  } catch {
    /* quota / private mode */
  }
}

/** Compact bullet list for system prompt injection (server-truncated separately). */
export function buildPersonalizationSummary(profile: SpiritUserProfileV1): string {
  if (!profile.sendPersonalizationToServer) return "";
  const lines = profile.preferences
    .filter((p) => !p.wrongPerspective)
    .map((p) => {
      const src = p.source ?? "default";
      return `- ${p.label} (${src}): ${p.value}`.trim();
    })
    .filter(Boolean);
  const body = lines.join("\n");
  if (!body) return "";
  if (body.length <= PERSONALIZATION_SUMMARY_MAX_CLIENT) return body;
  return `${body.slice(0, PERSONALIZATION_SUMMARY_MAX_CLIENT - 1)}…`;
}

/** Mode-aware slice appended for /api/spirit (Researcher gets research settings block). */
export function buildModeAwarePersonalizationSummary(
  profile: SpiritUserProfileV1,
  mode: ModelProfileId,
): string {
  let out = buildPersonalizationSummary(profile);
  const rs = profile.researchSettings ?? defaultResearchSettings();
  if (mode === "researcher") {
    const block = [
      "---",
      "Research settings (local):",
      `- Web search default (Researcher): ${rs.webSearchDefaultResearcher ? "ON" : "OFF"}`,
      `- Preferred source age: ${rs.preferredSourceAge}`,
      `- Preferred source types: ${rs.preferredSourceTypes.join(", ")}`,
      `- Require citations in Researcher: ${rs.requireCitationsResearcher ? "yes" : "no"}`,
      `- Include full source list: ${rs.includeFullSourceList ? "yes" : "no"}`,
      `- Warn when search fails: ${rs.warnOnSearchFailure ? "yes" : "no"}`,
      `- Plan-first deep research: ${rs.planFirstDeepResearchLater ? "stub on" : "later"}`,
    ].join("\n");
    out = out ? `${out}\n${block}` : block;
  }
  const trimmed = out.trim();
  if (!trimmed) return "";
  if (trimmed.length <= PERSONALIZATION_SUMMARY_MAX_CLIENT) return trimmed;
  return `${trimmed.slice(0, PERSONALIZATION_SUMMARY_MAX_CLIENT - 1)}…`;
}
