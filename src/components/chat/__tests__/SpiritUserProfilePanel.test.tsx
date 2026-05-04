import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { SpiritUserProfilePanel } from "@/components/chat/SpiritUserProfilePanel";

vi.mock("@/lib/spirit/spirit-user-profile", () => ({
  SPIRIT_USER_PROFILE_LS: "spirit:userProfile:v1",
  PERSONALIZATION_SUMMARY_MAX_CLIENT: 1200,
  defaultResearchSettings: () => ({
    webSearchDefaultResearcher: true,
    preferredSourceAge: "5y" as const,
    preferredSourceTypes: [],
    requireCitationsResearcher: true,
    includeFullSourceList: true,
    warnOnSearchFailure: true,
    planFirstDeepResearchLater: false,
  }),
  defaultSpiritUserProfile: () => ({
    version: 1,
    sendPersonalizationToServer: true,
    preferences: [{ id: "a", label: "L", value: "V", source: "default" as const }],
    researchSettings: {
      webSearchDefaultResearcher: true,
      preferredSourceAge: "5y" as const,
      preferredSourceTypes: [],
      requireCitationsResearcher: true,
      includeFullSourceList: true,
      warnOnSearchFailure: true,
      planFirstDeepResearchLater: false,
    },
  }),
  loadSpiritUserProfile: () => ({
    version: 1,
    sendPersonalizationToServer: true,
    preferences: [{ id: "a", label: "L", value: "V", source: "default" as const }],
    researchSettings: {
      webSearchDefaultResearcher: true,
      preferredSourceAge: "5y" as const,
      preferredSourceTypes: [],
      requireCitationsResearcher: true,
      includeFullSourceList: true,
      warnOnSearchFailure: true,
      planFirstDeepResearchLater: false,
    },
  }),
  saveSpiritUserProfile: vi.fn(),
  buildPersonalizationSummary: () => "summary",
  buildModeAwarePersonalizationSummary: () => "mode-aware-summary",
}));

describe("SpiritUserProfilePanel", () => {
  it("renders six tab buttons and switches panels", () => {
    render(
      <SpiritUserProfilePanel
        open
        onClose={() => {}}
        variant="popover"
        activeModelProfileId="teacher"
      />,
    );
    expect(screen.getByTestId("spirit-profile-tab-overview")).toBeInTheDocument();
    expect(screen.getByTestId("spirit-profile-tab-personality")).toBeInTheDocument();
    expect(screen.getByTestId("spirit-profile-tab-modes")).toBeInTheDocument();
    expect(screen.getByTestId("spirit-profile-tab-research")).toBeInTheDocument();
    expect(screen.getByTestId("spirit-profile-tab-memory")).toBeInTheDocument();
    expect(screen.getByTestId("spirit-profile-tab-server")).toBeInTheDocument();
    expect(screen.getByTestId("spirit-profile-tab-panel-overview")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("spirit-profile-tab-personality"));
    expect(screen.getByTestId("spirit-profile-tab-panel-personality")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("spirit-profile-tab-server"));
    expect(screen.getByTestId("spirit-profile-tab-panel-server")).toBeInTheDocument();
    expect(screen.getByTestId("spirit-profile-server-char-count")).toHaveTextContent(
      "mode-aware-summary".length.toString(),
    );
  });
});
