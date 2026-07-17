#!/usr/bin/env node
import { buildOperatorE2ERunnerEnv, loadOperatorE2ESecret, operatorE2EPreflight } from "./operator-e2e-secret.mjs";

const origin = process.env.PLAYWRIGHT_BASE_URL ?? "";
const loaded = loadOperatorE2ESecret();
const runner = loaded.ok ? buildOperatorE2ERunnerEnv({ secret: loaded.secret }) : null;
const payload = operatorE2EPreflight({ origin, runnerEnv: runner?.env });
process.stdout.write(`${JSON.stringify(payload)}\n`);
process.exitCode = payload.ready ? 0 : 1;
