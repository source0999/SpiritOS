import { describe, expect, it } from "vitest";

import {
  detectCapabilityIntent,
  isCapabilityIntent,
  normalizeForCapabilityIntent,
} from "../capability-intent";

describe("normalizeForCapabilityIntent", () => {
  it("fixes common capability typos", () => {
    expect(normalizeForCapabilityIntent("what are your capabilites?")).toContain(
      "what are your capabilities",
    );
  });
});

describe("detectCapabilityIntent", () => {
  it("classifies dev_commands", () => {
    expect(detectCapabilityIntent("Run npm test")).toBe("dev_commands");
    expect(detectCapabilityIntent("check git status")).toBe("dev_commands");
    expect(detectCapabilityIntent("npm run typecheck")).toBe("dev_commands");
    expect(detectCapabilityIntent("check types")).toBe("dev_commands");
  });

  it("classifies capability overview questions (including typos)", () => {
    expect(detectCapabilityIntent("what are your capabilities?")).toBe("general_capabilities");
    expect(detectCapabilityIntent("what are your capabilites?")).toBe("general_capabilities");
    expect(detectCapabilityIntent("what can you do?")).toBe("general_capabilities");
    expect(detectCapabilityIntent("what access do you have?")).toBe("general_capabilities");
  });

  it("classifies tools explicitly", () => {
    expect(detectCapabilityIntent("what tools do you have?")).toBe("tool_inventory");
  });

  it("classifies file_access", () => {
    expect(detectCapabilityIntent("Can you browse or list my C drive yet?")).toBe("file_access");
  });

  it("classifies hardware_summary", () => {
    expect(detectCapabilityIntent("What hardware can you see right now?")).toBe("hardware_summary");
  });

  it("classifies ai_runtime", () => {
    expect(detectCapabilityIntent("Are you running Hermes?")).toBe("ai_runtime");
  });

  it("classifies desktop_control", () => {
    expect(detectCapabilityIntent("Can you control my desktop?")).toBe("desktop_control");
    expect(detectCapabilityIntent("Can you SSH into my desktop?")).toBe("desktop_control");
  });

  it("classifies node_status", () => {
    expect(detectCapabilityIntent("What nodes are online?")).toBe("node_status");
  });

  it("classifies storage_status", () => {
    expect(detectCapabilityIntent("What storage can you see?")).toBe("storage_status");
    expect(detectCapabilityIntent("can you see my C drive?")).toBe("storage_status");
    expect(detectCapabilityIntent("do you see C:?")).toBe("storage_status");
    expect(detectCapabilityIntent("can you see my drives?")).toBe("storage_status");
  });

  it("classifies see-drive vs file ops", () => {
    expect(detectCapabilityIntent("can you browse my C drive?")).toBe("file_access");
    expect(detectCapabilityIntent("can you list files on my C drive?")).toBe("file_access");
    expect(detectCapabilityIntent("can you read files on C:?")).toBe("file_access");
  });

  it("does not hijack normal chat", () => {
    expect(detectCapabilityIntent("Hello, how was your day?")).toBeNull();
    expect(detectCapabilityIntent("Explain React useEffect in two sentences.")).toBeNull();
    expect(detectCapabilityIntent("can you help me write a prompt")).toBeNull();
  });

  it("does not fire on CPU shopping questions without telemetry context", () => {
    expect(detectCapabilityIntent("What's the best CPU for gaming in 2026?")).toBeNull();
  });
});

describe("isCapabilityIntent", () => {
  it("mirrors detectCapabilityIntent non-null", () => {
    expect(isCapabilityIntent("What hardware can you see?")).toBe(true);
    expect(isCapabilityIntent("Hello")).toBe(false);
  });
});
