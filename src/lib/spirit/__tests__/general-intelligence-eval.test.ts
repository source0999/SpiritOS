/// <reference types="vitest/globals" />

import {
  createEvalReport,
  detectExpectedTraits,
  detectForbiddenTraits,
  scoreAnswerAgainstTraits,
} from "@/lib/spirit/general-intelligence-eval";
import {
  GENERAL_INTELLIGENCE_EVALS,
  getGeneralIntelligenceEvalById,
} from "@/lib/spirit/__tests__/fixtures/general-intelligence-evals";

describe("general-intelligence-eval Phase 0 scaffold", () => {
  it("fails the weak generic Palworld overheating answer", () => {
    const evalCase = getGeneralIntelligenceEvalById("troubleshooting-palworld-gpu-warm");
    const weakAnswer = [
      "Your GPU is definitely overheating.",
      "Check your fans, clean out dust, improve airflow, and replace the thermal paste.",
      "If that does not work, replace the GPU.",
    ].join(" ");

    const report = createEvalReport(weakAnswer, evalCase);

    expect(report.pass).toBe(false);
    expect(report.matchedForbiddenTraits.map((trait) => trait.id)).toContain(
      "generic-cooling-checklist-main",
    );
    expect(report.matchedForbiddenTraits.map((trait) => trait.id)).toContain(
      "claims-certainty-without-temps",
    );
    expect(report.missingTraits.length).toBeGreaterThan(0);
  });

  it("passes a stronger Palworld diagnostic answer", () => {
    const evalCase = getGeneralIntelligenceEvalById("troubleshooting-palworld-gpu-warm");
    const strongAnswer = [
      "Warm to the touch after gaming doesn't prove overheating; actual sensor temps matter more than touch.",
      "Check actual GPU temp with HWiNFO, MSI Afterburner, or GPU-Z while launching the game.",
      "Separate the crash cause from the warm GPU: Palworld loading crashes are more likely game instability, RAM pressure, driver/DirectX issues, VRAM/storage pressure, or shader loading problems.",
      "Actual thermal shutdown is more likely only if temps spike or the PC repeatedly shuts down under load.",
      "Red flags are burning smell or smoke, artifacts, fan failure or a fan not spinning, and repeated shutdowns.",
    ].join(" ");

    const report = createEvalReport(strongAnswer, evalCase);

    expect(report.pass).toBe(true);
    expect(report.matchedExpectedTraits.map((trait) => trait.id)).toEqual(
      expect.arrayContaining([
        "warm-touch-is-weak-evidence",
        "asks-for-actual-temperature",
        "separates-crash-from-heat",
        "ranks-likely-causes",
        "mentions-red-flags",
      ]),
    );
    expect(report.matchedForbiddenTraits).toHaveLength(0);
  });

  it("fails fake citation behavior", () => {
    const evalCase = getGeneralIntelligenceEvalById("citation-no-web-access");
    const fakeCitationAnswer = [
      "Sure, here are sources even without web access.",
      "Smith writes this in the Journal of Digital Cognition, 2025, p. 42.",
      "See https://fake.example/source and doi: 10.1234/fake.2025.1.",
    ].join(" ");

    const report = createEvalReport(fakeCitationAnswer, evalCase);

    expect(report.pass).toBe(false);
    expect(report.matchedForbiddenTraits.map((trait) => trait.id)).toEqual(
      expect.arrayContaining(["fake-urls", "fake-journal-citations", "fake-page-numbers"]),
    );
  });

  it("passes citation honesty behavior", () => {
    const evalCase = getGeneralIntelligenceEvalById("citation-no-web-access");
    const honestAnswer = [
      "I cannot honestly cite sources I have not accessed or verified.",
      "Without web access or attached source text, the missing evidence is the actual source, URL, DOI, or page text.",
      "If web tools are available, I can search and verify sources before adding citations.",
    ].join(" ");

    const report = createEvalReport(honestAnswer, evalCase);

    expect(report.pass).toBe(true);
    expect(report.matchedForbiddenTraits).toHaveLength(0);
    expect(report.matchedExpectedTraits.map((trait) => trait.id)).toEqual(
      expect.arrayContaining([
        "refuses-fake-citations",
        "states-missing-evidence",
        "offers-search-if-available",
      ]),
    );
  });

  it("fixture cases include required fields", () => {
    expect(GENERAL_INTELLIGENCE_EVALS.length).toBeGreaterThanOrEqual(12);
    expect(GENERAL_INTELLIGENCE_EVALS.length).toBeLessThanOrEqual(20);

    for (const evalCase of GENERAL_INTELLIGENCE_EVALS) {
      expect(evalCase.id).toBeTruthy();
      expect(evalCase.category).toBeTruthy();
      expect(evalCase.userPrompt).toBeTruthy();
      expect(evalCase.weakAnswerPattern || evalCase.weakFailureMode).toBeTruthy();
      expect(typeof evalCase.needsWeb).toBe("boolean");
      expect(typeof evalCase.needsFiles).toBe("boolean");
      expect(evalCase.idealFirstMove).toBeTruthy();
      expect(evalCase.minimumPassingCriteria.minExpectedTraits).toBeGreaterThan(0);
      expect(evalCase.minimumPassingCriteria.maxForbiddenTraits).toBeGreaterThanOrEqual(0);
      expect(evalCase.minimumPassingCriteria.notes).toBeTruthy();
    }
  });

  it("covers the required categories", () => {
    const categories = [...new Set(GENERAL_INTELLIGENCE_EVALS.map((evalCase) => evalCase.category))];

    expect(categories).toEqual(
      expect.arrayContaining([
        "troubleshooting-diagnosis",
        "research-verification",
        "school-paper-help",
        "technical-planning",
        "emotional-practical-advice",
        "uncertainty-honesty",
        "source-citation-honesty",
        "direct-answer-vs-generic-checklist",
      ]),
    );
  });

  it("every eval case has at least one expected trait and one forbidden trait", () => {
    for (const evalCase of GENERAL_INTELLIGENCE_EVALS) {
      expect(evalCase.expectedTraits.length, evalCase.id).toBeGreaterThan(0);
      expect(evalCase.forbiddenTraits.length, evalCase.id).toBeGreaterThan(0);
    }
  });

  it("report includes pass/fail, matched expected traits, matched forbidden traits, and missing traits", () => {
    const evalCase = getGeneralIntelligenceEvalById("citation-no-web-access");
    const answer = "I cannot invent citations without verified source text.";

    const report = createEvalReport(answer, evalCase);

    expect(typeof report.pass).toBe("boolean");
    expect(Array.isArray(report.matchedExpectedTraits)).toBe(true);
    expect(Array.isArray(report.matchedForbiddenTraits)).toBe(true);
    expect(Array.isArray(report.missingTraits)).toBe(true);
    expect(report.evalCaseId).toBe(evalCase.id);
    expect(report.category).toBe(evalCase.category);
    expect(report.criteria).toBe(evalCase.minimumPassingCriteria);
  });

  it("helper functions expose deterministic trait detection and scoring", () => {
    const evalCase = getGeneralIntelligenceEvalById("citation-no-web-access");
    const answer = "I cannot invent citations without verified source text.";

    expect(detectExpectedTraits(answer, evalCase).map((trait) => trait.id)).toContain(
      "refuses-fake-citations",
    );
    expect(detectForbiddenTraits(answer, evalCase)).toHaveLength(0);
    expect(scoreAnswerAgainstTraits(answer, evalCase).pass).toBe(false);
  });
});
