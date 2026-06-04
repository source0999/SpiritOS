import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("reversible suite diagnostics builder", () => {
  it("does not reference result in the suite header before the per_prompt loop", () => {
    const source = readFileSync(
      resolve(process.cwd(), "src/components/coding/CodingCockpitShell.tsx"),
      "utf8",
    );
    const match = source.match(
      /function reversibleSuiteDiagnosticsText[\s\S]*?for \(const result of state\.results\)/,
    );
    expect(match, "reversibleSuiteDiagnosticsText must exist with a results loop").toBeTruthy();
    const header = match![0];
    expect(header).not.toMatch(/\$\{result\./);
    expect(header).not.toMatch(/`prompt_id: \$\{result/);
  });

  it("keeps model-proof failures as prompt diagnostics instead of suite-fatal aborts", () => {
    const source = readFileSync(
      resolve(process.cwd(), "src/components/coding/CodingCockpitShell.tsx"),
      "utf8",
    );
    const abortMatch = source.match(
      /function reversibleSuiteAbortForResult[\s\S]*?function trialProviderCallMadeFromPayload/,
    );
    expect(abortMatch, "reversibleSuiteAbortForResult must be present").toBeTruthy();
    const abortBody = abortMatch![0];

    expect(abortBody).not.toContain("dummy_trial_model_call_failed");
    expect(abortBody).not.toContain("realistic_trial_model_call_failed");
    expect(abortBody).not.toContain("Live trial proof could not confirm a coder model call");
    expect(source).toContain("phase=model_proof");
    expect(source).toContain("trialModelProofFailureSummary");
  });
});
