import { describe, expect, it } from "vitest";

import { MODEL_PROFILES } from "@/lib/spirit/model-profiles";
import {
  buildResponseBudgetInstruction,
  isLikelyCasualShortMessage,
  mentionsCodeOrBuild,
  resolveSpiritMaxOutputTokens,
  wantsTeacherWebStudyAids,
} from "@/lib/spirit/response-budget";

describe("response-budget", () => {
  it("detects casual short message", () => {
    expect(isLikelyCasualShortMessage("I'm bored")).toBe(true);
  });

  it("mentionsCodeOrBuild true when dev keywords present", () => {
    expect(mentionsCodeOrBuild("fix this bug in the repo")).toBe(true);
  });

  it("Peer budget instructs not to default to coding", () => {
    const s = buildResponseBudgetInstruction(MODEL_PROFILES["normal-peer"], "yo", {});
    expect(s).toContain("do not slide into repo");
  });

  it("Researcher budget mentions citations and search honesty", () => {
    const s = buildResponseBudgetInstruction(MODEL_PROFILES.researcher, "compare studies on X", {});
    expect(s).toContain("Citations");
    expect(s).toContain("Search used");
  });

  it("Researcher budget mandates markdown source links when digestHasVerifiedUrls", () => {
    const s = buildResponseBudgetInstruction(MODEL_PROFILES.researcher, "hi there", {
      digestHasVerifiedUrls: true,
    });
    expect(s).toContain("Verified URLs are attached");
    expect(s).toContain("## Sources");
    expect(s).not.toContain("does not obviously require live web data");
  });

  it("Researcher budget allows shallow-web line only when no digest URLs", () => {
    const s = buildResponseBudgetInstruction(MODEL_PROFILES.researcher, "hi there", {
      digestHasVerifiedUrls: false,
    });
    expect(s).toContain("does not obviously require live web data");
  });

  it("Teacher budget mentions study aids footer", () => {
    const s = buildResponseBudgetInstruction(MODEL_PROFILES.teacher, "what is gravity", {});
    expect(s).toContain("Study aids");
  });

  it("wantsTeacherWebStudyAids true for sensory / autism topics without explicit explain", () => {
    expect(wantsTeacherWebStudyAids("Sensory overload vs tantrums in toddlers")).toBe(true);
    expect(wantsTeacherWebStudyAids("Stimulus over-selectivity in ASD")).toBe(true);
  });

  it("Teacher budget prioritizes digest links when digestHasVerifiedUrls", () => {
    const s = buildResponseBudgetInstruction(MODEL_PROFILES.teacher, "explain ABA", {
      digestHasVerifiedUrls: true,
    });
    expect(s).toContain("markdown link");
    expect(s).not.toContain("mnemonic / trap / flashcard");
  });

  it("Sassy budget stays small (punchy sentences)", () => {
    const s = buildResponseBudgetInstruction(MODEL_PROFILES["sassy-chaotic"], "hi", {});
    expect(s).toContain("1–3 short sentences");
  });

  it("Brutal budget stays short", () => {
    const s = buildResponseBudgetInstruction(MODEL_PROFILES.brutal, "hi", {});
    expect(s).toContain("short, sharp");
  });

  it("Sassy casual max tokens stay low", () => {
    expect(
      resolveSpiritMaxOutputTokens({
        profileId: "sassy-chaotic",
        profileMax: 1536,
        lastUserMessage: "hi",
        deepThinkEnabled: false,
      }),
    ).toBeLessThanOrEqual(220);
  });

  it("Deep Think does not explode Sassy casual cap", () => {
    const shallow = resolveSpiritMaxOutputTokens({
      profileId: "sassy-chaotic",
      profileMax: 1536,
      lastUserMessage: "hi",
      deepThinkEnabled: false,
    });
    const deep = resolveSpiritMaxOutputTokens({
      profileId: "sassy-chaotic",
      profileMax: 1536,
      lastUserMessage: "hi",
      deepThinkEnabled: true,
    });
    expect(deep).toBeLessThanOrEqual(520);
    expect(deep).toBeGreaterThanOrEqual(shallow);
  });

  it("Brutal casual max tokens stay bounded", () => {
    expect(
      resolveSpiritMaxOutputTokens({
        profileId: "brutal",
        profileMax: 1400,
        lastUserMessage: "hi",
        deepThinkEnabled: false,
      }),
    ).toBeLessThanOrEqual(320);
  });

  it("Oracle surface adds voice response budget block", () => {
    const s = buildResponseBudgetInstruction(MODEL_PROFILES["normal-peer"], "yo", { runtimeSurface: "oracle" });
    expect(s).toContain("Oracle voice response budget");
    expect(s).toContain("90 words");
  });

  it("Chat surface does not add Oracle voice budget block", () => {
    const s = buildResponseBudgetInstruction(MODEL_PROFILES["normal-peer"], "yo", { runtimeSurface: "chat" });
    expect(s).not.toContain("Oracle voice response budget");
  });

  it("Oracle Peer caps casual tokens tighter than chat Peer", () => {
    const chatCap = resolveSpiritMaxOutputTokens({
      profileId: "normal-peer",
      profileMax: 1536,
      lastUserMessage: "hi",
      deepThinkEnabled: false,
      runtimeSurface: "chat",
    });
    const oracleCap = resolveSpiritMaxOutputTokens({
      profileId: "normal-peer",
      profileMax: 1536,
      lastUserMessage: "hi",
      deepThinkEnabled: false,
      runtimeSurface: "oracle",
    });
    expect(chatCap).toBeGreaterThan(oracleCap);
    expect(oracleCap).toBeLessThanOrEqual(280);
  });

  it("resolveSpiritMaxOutputTokens chat researcher unchanged vs oracle researcher without URLs", () => {
    const chatCap = resolveSpiritMaxOutputTokens({
      profileId: "researcher",
      profileMax: 3072,
      lastUserMessage: "compare papers on X thoroughly",
      deepThinkEnabled: false,
      runtimeSurface: "chat",
    });
    const oracleCap = resolveSpiritMaxOutputTokens({
      profileId: "researcher",
      profileMax: 3072,
      lastUserMessage: "compare papers on X thoroughly",
      deepThinkEnabled: false,
      runtimeSurface: "oracle",
      webVerifiedUrlCount: 0,
    });
    expect(chatCap).toBeGreaterThanOrEqual(oracleCap);
  });
});
