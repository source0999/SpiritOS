#!/usr/bin/env node
import assert from "node:assert/strict";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { validateReceiptFile } from "./validate-design-studio-receipts.mjs";

const fixturesDir = join(dirname(fileURLToPath(import.meta.url)), "__tests__", "fixtures");

function assertFixtureRejects(fileName, expectedError) {
  const result = validateReceiptFile(join(fixturesDir, fileName), { baseDir: fixturesDir });
  assert.equal(result.ok, false, `${fileName} should be rejected`);
  assert.ok(
    result.errors.includes(expectedError),
    `${fileName} should include ${expectedError}; saw ${result.errors.join(", ")}`,
  );
}

const cases = [
  [
    "forged-artifact-hash.json",
    "artifact_hash_mismatch:design_packet:artifact-chain/design-packet.txt",
  ],
  [
    "broken-trace-link-chain.json",
    "chain_link_hash_mismatch:sandbox_apply->screenshot",
  ],
  [
    "screenshot-missing-sandbox-apply.json",
    "screenshot_missing_sandbox_apply_receipt_id",
  ],
  ["screenshot-missing-diff-hash.json", "screenshot_missing_diff_hash"],
  ["critic-missing-screenshot-hash.json", "critic_missing_screenshot_hash"],
  ["writeback-missing-approval-hash.json", "writeback_missing_approval_id_hash"],
  ["writeback-trace-mismatch.json", "writeback_trace_mismatch"],
  ["missing-required-field.json", "missing_required_field:branch"],
  [
    "missing-artifact-path.json",
    "artifact_path_missing:desktop_screenshot:artifact-chain/missing-screenshot.txt",
  ],
];

for (const [fileName, expectedError] of cases) {
  assertFixtureRejects(fileName, expectedError);
}

console.log(
  JSON.stringify(
    {
      cases: cases.length,
      ok: true,
      suite: "design-studio-receipt-validator-negative-fixtures",
    },
    null,
    2,
  ),
);
