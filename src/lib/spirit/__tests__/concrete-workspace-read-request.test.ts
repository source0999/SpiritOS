import { describe, expect, it } from "vitest";

import {
  isConcreteWorkspaceReadRequest,
  pathFragmentLooksConcrete,
} from "../concrete-workspace-read-request";

describe("isConcreteWorkspaceReadRequest", () => {
  it("returns true for list/show/read/tail with concrete paths", () => {
    expect(isConcreteWorkspaceReadRequest("List the files in src/lib/spirit")).toBe(true);
    expect(isConcreteWorkspaceReadRequest("show files in src/app")).toBe(true);
    expect(isConcreteWorkspaceReadRequest("list directory src/lib")).toBe(true);
    expect(isConcreteWorkspaceReadRequest("read package.json")).toBe(true);
    expect(isConcreteWorkspaceReadRequest("open src/lib/spirit/model-runtime.ts")).toBe(true);
    expect(isConcreteWorkspaceReadRequest("show contents of src/lib/spirit/system-state.ts")).toBe(
      true,
    );
    expect(isConcreteWorkspaceReadRequest("tail nohup.out")).toBe(true);
    expect(isConcreteWorkspaceReadRequest("show last 50 lines of app.log")).toBe(true);
  });

  it("returns false for vague capability questions", () => {
    expect(isConcreteWorkspaceReadRequest("Can you browse files?")).toBe(false);
    expect(isConcreteWorkspaceReadRequest("Do you have file access?")).toBe(false);
    expect(isConcreteWorkspaceReadRequest("Can you read my files?")).toBe(false);
    expect(isConcreteWorkspaceReadRequest("Can you edit files?")).toBe(false);
    expect(isConcreteWorkspaceReadRequest("What tools do you have?")).toBe(false);
    expect(isConcreteWorkspaceReadRequest("Can you control my desktop?")).toBe(false);
    expect(isConcreteWorkspaceReadRequest("Can you run commands?")).toBe(false);
  });

  it("returns false for command / package-manager asks", () => {
    expect(isConcreteWorkspaceReadRequest("Run npm test")).toBe(false);
    expect(isConcreteWorkspaceReadRequest("npm install lodash")).toBe(false);
  });

  it("treats read .env.local as concrete (tool layer blocks unsafe paths)", () => {
    expect(isConcreteWorkspaceReadRequest("Read .env.local")).toBe(true);
  });
});

describe("pathFragmentLooksConcrete", () => {
  it("rejects vague fragments", () => {
    expect(pathFragmentLooksConcrete("my")).toBe(false);
    expect(pathFragmentLooksConcrete("files")).toBe(false);
  });
});
