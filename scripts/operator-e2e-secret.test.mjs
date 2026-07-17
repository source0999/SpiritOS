import assert from "node:assert/strict";
import { chmodSync, mkdtempSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { buildOperatorE2ERunnerEnv, loadOperatorE2ESecret, operatorE2EPreflight } from "./operator-e2e-secret.mjs";

function fixture(mode = 0o600) {
  const file = path.join(mkdtempSync(path.join(os.tmpdir(), "operator-e2e-secret-")), "operator.env");
  writeFileSync(file, "SPIRITOS_OPERATOR_CREDENTIAL=test-only-secret\n", { mode });
  chmodSync(file, mode);
  return file;
}

test("missing and unsafe secret files fail closed", () => {
  assert.equal(loadOperatorE2ESecret({ secretFile: "/tmp/does-not-exist-operator-secret" }).reason, "operator_e2e_secret_missing");
  assert.equal(loadOperatorE2ESecret({ secretFile: fixture(0o644) }).reason, "operator_e2e_secret_permissions_unsafe");
});

test("canonical launcher forwards the secret only in its child environment", () => {
  const loaded = loadOperatorE2ESecret({ secretFile: fixture() });
  assert.equal(loaded.ok, true);
  const runner = buildOperatorE2ERunnerEnv({ baseEnv: { HOME: "/home/source", PATH: "/usr/bin", UNRELATED_SECRET: "must-not-pass" }, secret: loaded.secret });
  assert.equal(runner.ok, true);
  assert.equal(runner.env.SPIRITOS_OPERATOR_E2E_SECRET, "test-only-secret");
  assert.equal(runner.env.UNRELATED_SECRET, undefined);
  assert.equal(operatorE2EPreflight({ secretFile: fixture(), origin: "https://localhost:3104", runnerEnv: {} }).reason, "operator_e2e_secret_not_forwarded");
});

test("preflight is redacted and does not expose the credential", () => {
  const file = fixture();
  const loaded = loadOperatorE2ESecret({ secretFile: file });
  const runner = buildOperatorE2ERunnerEnv({ secret: loaded.secret });
  const receipt = operatorE2EPreflight({ secretFile: file, origin: "https://localhost:3104", runnerEnv: runner.env });
  assert.equal(receipt.ready, true);
  assert.equal(JSON.stringify(receipt).includes("test-only-secret"), false);
  assert.equal(receipt.secret_fingerprint.length, 16);
});
