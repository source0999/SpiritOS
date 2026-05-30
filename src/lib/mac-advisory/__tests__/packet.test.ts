/// <reference types="vitest/globals" />

import { buildMacAdvisoryPacket, validateMacAdvisoryPacket } from "../packet";
import { runMacAdvisoryJob } from "../one-shot";

describe("Mac advisory packet contract", () => {
  it("builds the required packet fields with no repo write authority", () => {
    const packet = buildMacAdvisoryPacket({
      citations_or_evidence: ["ssh://spirit-mac-mini one-shot evidence"],
      input_summary: "Summarize a bounded doc packet.",
      job_id: "mac-test-1",
      job_type: "docs_summary_packet",
      mac_host: "spirit-mac-mini",
      result: "Summary complete.",
      status: "completed",
    });

    expect(validateMacAdvisoryPacket(packet)).toEqual([]);
    expect(packet).toMatchObject({
      job_id: "mac-test-1",
      job_type: "docs_summary_packet",
      input_summary: "Summarize a bounded doc packet.",
      mac_host: "spirit-mac-mini",
      status: "completed",
      result: "Summary complete.",
      repo_write_authority: false,
    });
    expect(packet.safety_boundary).toContain("one-shot");
    expect(packet.safety_boundary).toContain("no repo write");
  });

  it("blocks unsupported jobs without starting a runner", async () => {
    let runnerCalled = false;
    const packet = await runMacAdvisoryJob(
      {
        input_summary: "Try unsupported work.",
        job_id: "mac-test-blocked",
        job_type: "apply_packet",
      },
      {
        runner: async () => {
          runnerCalled = true;
          return { stderr: "", stdout: "" };
        },
      },
    );

    expect(runnerCalled).toBe(false);
    expect(packet.status).toBe("blocked");
    expect(packet.repo_write_authority).toBe(false);
    expect(packet.result).toContain("unsupported");
  });

  it("runs an injected one-shot command and returns evidence", async () => {
    const packet = await runMacAdvisoryJob(
      {
        input_summary: "Draft test notes for a bounded UI trial.",
        job_id: "mac-test-scribe",
        job_type: "test_scribe_packet",
      },
      {
        macHost: "spirit-mac-mini",
        runner: async (command) => ({
          stderr: "",
          stdout: JSON.stringify({
            command_included_python: command.includes("python3"),
            safe: "no_repo_write",
          }),
        }),
      },
    );

    expect(packet.status).toBe("completed");
    expect(packet.job_type).toBe("test_scribe_packet");
    expect(packet.repo_write_authority).toBe(false);
    expect(packet.citations_or_evidence[0]).toContain("no_repo_write");
  });
});

