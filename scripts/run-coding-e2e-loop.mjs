#!/usr/bin/env node

import { spawn, spawnSync } from "node:child_process";
import {
  createWriteStream,
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { createServer } from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  E2E_LOOP_SCHEMA_VERSION,
  buildAuthoritativeFinalTruth,
  repoRootsMatch,
} from "./coding-e2e-loop-contract.mjs";
import { buildOperatorE2ERunnerEnv, loadOperatorE2ESecret, operatorE2EPreflight } from "./operator-e2e-secret.mjs";

process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "..");
const tmpRoot = path.join(repoRoot, "tmp", "e2e-loop");
const evidenceRoot = path.join(repoRoot, "docs", "evidence", "e2e-loop");
const fixtureRoot = path.join(repoRoot, "tests", "ui-agent-trials", "fixtures", "dummy-product-site");
const fixtureResetRoute = "/v1/coding/dummy-product-site-preview/reset";
const promptOneTargetPlugin = {
  schema_version: "spiritos-target-plugin/v1",
  id: "lumacart",
  repository_id: "spiritos-campaign-2",
  worktree_id: "spiritos-campaign-2-20260716",
  fixture_root: "tests/ui-agent-trials/fixtures/dummy-product-site/",
  selected_prompt_id: "coder-001-init-dummy-product-site",
  selected_context_id: "init-storefront",
  execution_profile: "coder-10",
};
const fixtureRequiredRelativePaths = [
  "README.md",
  "package.json",
  "index.html",
  "src/main.js",
  "src/products.js",
  "src/styles.css",
];
const defaultSpec = "tests/e2e-loop/coding-p1-fresh-create.spec.ts";
const terminalStatuses = new Set(["applied", "blocked", "complete", "error", "timeout"]);
const proxyHealthTimeoutMs = envTimeoutMs("E2E_PROXY_HEALTH_TIMEOUT_MS", 75_000);
const frontendHealthTimeoutMs = envTimeoutMs("E2E_FRONTEND_HEALTH_TIMEOUT_MS", 180_000);

const args = parseArgs(process.argv.slice(2));

const loadedEnv = loadEnvLocal();
process.env.SPIRIT_CODING_USE_PROXY = "true";
mkdirSync(tmpRoot, { recursive: true });
mkdirSync(evidenceRoot, { recursive: true });

main().catch((error) => {
  console.error(`E2E loop crashed: ${error instanceof Error ? error.stack ?? error.message : String(error)}`);
  process.exitCode = 1;
});

async function main() {
  logLoadedEnv(loadedEnv);
  if (args.watch) {
    await watchLoop();
    return;
  }

  const result = await runOnce();
  process.exit(result.ok ? 0 : 1);
}

async function runOnce() {
  const startedAt = new Date();
  const timestamp = startedAt.toISOString().replace(/[:.]/g, "-");
  const evidenceDir = path.join(evidenceRoot, timestamp);
  mkdirSync(evidenceDir, { recursive: true });

  const spawned = [];
  const stepResults = [];
  const proxyBasesToUse = proxyBases();
  const frontendBaseUrl = trimTrailingSlash(process.env.PLAYWRIGHT_BASE_URL || "https://localhost:3000");
  const managedLaneValidation = validateManagedLane({
    frontendBaseUrl,
    proxyBaseUrl: proxyBasesToUse[0],
  });
  if (!managedLaneValidation.ok) {
    const result = immediateFailureResult({
      evidenceDir,
      fixtureState: args.fixtureState,
      reason: "managed_lane_mismatch",
      startedAt,
      details: managedLaneValidation,
    });
    printRunSummary(result, "");
    return result;
  }
  let proxyHealth = await probeProxyHealth(proxyBasesToUse);
  let frontendHealth = await probeFrontendHealth(frontendBaseUrl);

  try {
    stepResults.push(step("env_loaded", process.env.SPIRIT_CODING_USE_PROXY === "true", {
      loaded_keys: loadedEnv.map((entry) => entry.key),
      SPIRIT_CODING_USE_PROXY: process.env.SPIRIT_CODING_USE_PROXY,
    }));

    if (!proxyHealth.healthy) {
      const result = immediateFailureResult({
        evidenceDir,
        fixtureState: args.fixtureState,
        reason: "managed_proxy_unhealthy_no_fallback",
        startedAt,
        details: {
          expected_backend_port: "8787",
          attempted_backend: proxyBasesToUse,
          fallback_backend_port: "8877",
          fallback_allowed: false,
          proxy_health: proxyHealth,
        },
      });
      printRunSummary(result, "");
      return result;
    }
    stepResults.push(step("proxy_health", proxyHealth.healthy, proxyHealth));

    if (!frontendHealth.healthy) {
      const result = immediateFailureResult({
        evidenceDir,
        fixtureState: args.fixtureState,
        reason: "managed_frontend_unhealthy_no_fallback",
        startedAt,
        details: {
          expected_frontend_port: "3000",
          attempted_frontend: frontendBaseUrl,
          fallback_frontend_port: "3100",
          fallback_allowed: false,
          frontend_health: frontendHealth,
        },
      });
      printRunSummary(result, "");
      return result;
    }
    stepResults.push(step("frontend_health", frontendHealth.healthy, frontendHealth));

    const fixtureReset = await resetFixtureThroughProduct(frontendHealth.baseUrl, args.fixtureState);
    stepResults.push(step("product_fixture_reset", fixtureReset.ok, fixtureReset));
    if (!fixtureReset.ok) {
      const result = immediateFailureResult({
        evidenceDir,
        fixtureState: args.fixtureState,
        reason: "product_fixture_reset_not_verified",
        startedAt,
        details: fixtureReset,
        frontend: frontendHealth,
        proxy: proxyHealth,
        steps: stepResults,
      });
      printRunSummary(result, readTextIfExists(result.diagnostics_path));
      return result;
    }

    if (args.fixtureState === "missing") {
      stepResults.push(step("fixture_seed_setup", true, {
        fixture_state: args.fixtureState,
        proof_scope: "not_applicable: product reset already established the missing-fixture precondition",
        status: "not_required",
      }));
    } else {
      seedFixtureState(args.fixtureState);
      stepResults.push(step("fixture_seed_setup", true, {
        fixture_state: args.fixtureState,
        fixture_root: fixtureRoot,
        proof_scope: "test_precondition_only_not_product_reset_proof",
        status: "seeded_after_verified_product_reset",
      }));
    }

    const operatorSecret = loadOperatorE2ESecret();
    if (!operatorSecret.ok) {
      const result = immediateFailureResult({ evidenceDir, fixtureState: args.fixtureState, reason: operatorSecret.reason, startedAt, details: { secret_source: "canonical_secret_file" }, frontend: frontendHealth, proxy: proxyHealth, steps: stepResults });
      printRunSummary(result, "");
      return result;
    }
    const runnerEnvironment = buildOperatorE2ERunnerEnv({ secret: operatorSecret.secret });
    const operatorPreflight = operatorE2EPreflight({ origin: frontendHealth.baseUrl, runnerEnv: runnerEnvironment.env });
    stepResults.push(step("operator_e2e_preflight", operatorPreflight.ready === true, operatorPreflight));
    if (!runnerEnvironment.ok || operatorPreflight.ready !== true) {
      const result = immediateFailureResult({ evidenceDir, fixtureState: args.fixtureState, reason: runnerEnvironment.reason ?? operatorPreflight.reason, startedAt, details: operatorPreflight, frontend: frontendHealth, proxy: proxyHealth, steps: stepResults });
      printRunSummary(result, "");
      return result;
    }
    const diagnosticsPath = path.join(evidenceDir, "diagnostics.txt");
    const capturePath = path.join(evidenceDir, "capture.json");
    const playwrightReportPath = path.join(evidenceDir, "playwright-report.json");
    const playwrightStderrPath = path.join(evidenceDir, "playwright-stderr.txt");
    const play = runPlaywright({
      capturePath,
      diagnosticsPath,
      frontendBaseUrl: frontendHealth.baseUrl,
      proxyBaseUrl: proxyHealth.baseUrl ?? proxyBasesToUse[0],
      spec: args.spec,
      runnerEnvironment: runnerEnvironment.env,
    });
    writeFileSync(playwrightReportPath, play.stdout ?? "", "utf8");
    writeFileSync(playwrightStderrPath, play.stderr ?? String(play.error?.message ?? ""), "utf8");

    const playwrightJson = parsePlaywrightJson(play.stdout ?? "");
    const capture = readJsonFile(capturePath);
    const diagnostics = readTextIfExists(diagnosticsPath);
    const antiCheat = evaluateAntiCheatInvariant(diagnostics);
    const playwrightOk = play.status === 0;
    stepResults.push(step("playwright_run", playwrightOk, {
      exit_code: play.status,
      signal: play.signal,
      spec: args.spec,
    }));
    stepResults.push(step("anti_cheat_invariant", antiCheat.ok, antiCheat));
    stepResults.push(step(
      "evidence_schema",
      capture?.schema_version === E2E_LOOP_SCHEMA_VERSION,
      {
        expected_schema_version: E2E_LOOP_SCHEMA_VERSION,
        observed_schema_version: capture?.schema_version ?? "missing",
      },
    ));

    const authoritativeFinalTruth = buildAuthoritativeFinalTruth({ capture, steps: stepResults });
    stepResults.push(step(
      "authoritative_final_truth",
      authoritativeFinalTruth.truth_status === "GO",
      authoritativeFinalTruth,
    ));

    const result = {
      schema_version: E2E_LOOP_SCHEMA_VERSION,
      ok: authoritativeFinalTruth.truth_status === "GO",
      authoritative_final_truth: authoritativeFinalTruth,
      anti_cheat_invariant: antiCheat,
      capture,
      diagnostics_path: diagnosticsPath,
      evidence_dir: evidenceDir,
      fixture_state: args.fixtureState,
      frontend: frontendHealth,
      http_events: Array.isArray(capture?.http_events) ? capture.http_events : [],
      play_exit_code: play.status,
      playwright_report_path: playwrightReportPath,
      playwright_summary: summarizePlaywright(playwrightJson),
      proxy: proxyHealth,
      result_path: path.join(evidenceDir, "result.json"),
      spec: args.spec,
      started_at: startedAt.toISOString(),
      steps: stepResults,
    };
    writeFileSync(result.result_path, `${JSON.stringify(result, null, 2)}\n`, "utf8");
    if (!existsSync(diagnosticsPath)) {
      writeFileSync(diagnosticsPath, diagnostics || "", "utf8");
    }
    printRunSummary(result, diagnostics);
    return result;
  } finally {
    await stopSpawned(spawned);
  }
}

function parseArgs(argv) {
  const parsed = {
    fixtureState: "missing",
    spec: defaultSpec,
    watch: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--watch") {
      parsed.watch = true;
      continue;
    }
    if (arg.startsWith("--fixture-state=")) {
      parsed.fixtureState = arg.slice("--fixture-state=".length);
      continue;
    }
    if (arg === "--fixture-state") {
      parsed.fixtureState = argv[index + 1] ?? parsed.fixtureState;
      index += 1;
      continue;
    }
    if (arg.startsWith("--spec=")) {
      parsed.spec = arg.slice("--spec=".length);
      continue;
    }
    if (arg === "--spec") {
      parsed.spec = argv[index + 1] ?? parsed.spec;
      index += 1;
    }
  }
  if (!["bare", "missing", "rendering"].includes(parsed.fixtureState)) {
    throw new Error(`Unsupported --fixture-state=${parsed.fixtureState}. Use missing, bare, or rendering.`);
  }
  return parsed;
}

function validateManagedLane({ frontendBaseUrl, proxyBaseUrl }) {
  const proxy = urlDetails(proxyBaseUrl);
  const frontend = urlDetails(frontendBaseUrl);
  const isolatedCandidate = process.env.E2E_LOOP_ISOLATED_CANDIDATE === "true";
  const errors = [];
  if (isolatedCandidate) {
    if (proxy.protocol !== "https:" || proxy.hostname !== "127.0.0.1" || !proxy.port || proxy.port === "8787") {
      errors.push({ reason: "isolated_candidate_backend_must_use_nonproduction_loopback_https" });
    }
    if (frontend.protocol !== "https:" || !["localhost", "127.0.0.1"].includes(frontend.hostname) || !frontend.port || frontend.port === "3000") {
      errors.push({ reason: "isolated_candidate_frontend_must_use_nonproduction_loopback_https" });
    }
    return {
      ok: errors.length === 0,
      errors,
      expected_backend_port: "nonproduction-loopback",
      expected_frontend_port: "nonproduction-loopback",
      expected_repo_root: repoRoot,
      attempted_backend_url: proxyBaseUrl,
      attempted_frontend_url: frontendBaseUrl,
      fallback_backend_port: "none",
      fallback_frontend_port: "none",
      fallback_allowed: false,
      lane_mode: "explicit_isolated_campaign_candidate",
    };
  }
  if (proxy.protocol !== "https:" || proxy.hostname !== "127.0.0.1") {
    errors.push({
      expected_backend_origin: "https://127.0.0.1:8787",
      actual_attempted_url: proxyBaseUrl,
      reason: "source_proxy_backend_must_use_managed_loopback_https_origin",
    });
  }
  if (proxy.port !== "8787") {
    errors.push({
      expected_backend_port: "8787",
      actual_attempted_port: proxy.port || "missing",
      actual_attempted_url: proxyBaseUrl,
      reason: "source_proxy_backend_must_use_managed_8787_lane",
    });
  }
  if (frontend.protocol !== "https:" || !["localhost", "127.0.0.1"].includes(frontend.hostname)) {
    errors.push({
      expected_frontend_origins: ["https://localhost:3000", "https://127.0.0.1:3000"],
      actual_attempted_url: frontendBaseUrl,
      reason: "coding_frontend_must_use_managed_loopback_https_origin",
    });
  }
  if (frontend.port !== "3000") {
    errors.push({
      expected_frontend_port: "3000",
      actual_attempted_port: frontend.port || "missing",
      actual_attempted_url: frontendBaseUrl,
      reason: "coding_frontend_must_use_managed_3000_lane",
    });
  }
  return {
    ok: errors.length === 0,
    errors,
    expected_backend_port: "8787",
    expected_frontend_port: "3000",
    expected_repo_root: repoRoot,
    attempted_backend_url: proxyBaseUrl,
    attempted_frontend_url: frontendBaseUrl,
    fallback_backend_port: "8877",
    fallback_frontend_port: "3100",
    fallback_allowed: false,
  };
}

function urlDetails(value) {
  try {
    const parsed = new URL(value);
    return { host: parsed.host, hostname: parsed.hostname, port: parsed.port, protocol: parsed.protocol };
  } catch {
    return { host: "", hostname: "", port: "", protocol: "", invalid: true };
  }
}

function immediateFailureResult({
  evidenceDir,
  fixtureState,
  reason,
  startedAt,
  details,
  frontend = null,
  proxy = null,
  steps = [],
}) {
  const diagnosticsPath = path.join(evidenceDir, "diagnostics.txt");
  const resultPath = path.join(evidenceDir, "result.json");
  const diagnostics = [
    `managed_lane_status: failed`,
    `reason_code: ${reason}`,
    `expected_backend_port: ${details.expected_backend_port ?? "8787"}`,
    `expected_frontend_port: ${details.expected_frontend_port ?? "3000"}`,
    `attempted_backend: ${JSON.stringify(details.attempted_backend ?? details.attempted_backend_url ?? "")}`,
    `attempted_frontend: ${JSON.stringify(details.attempted_frontend ?? details.attempted_frontend_url ?? "")}`,
    `fallback_backend_port: ${details.fallback_backend_port ?? "8877"}`,
    `fallback_frontend_port: ${details.fallback_frontend_port ?? "3100"}`,
    `fallback_allowed: false`,
  ].join("\n");
  writeFileSync(diagnosticsPath, `${diagnostics}\n`, "utf8");
  const resultSteps = steps.length > 0 ? steps : [step(reason, false, details)];
  const authoritativeFinalTruth = buildAuthoritativeFinalTruth({ capture: null, steps: resultSteps });
  const result = {
    schema_version: E2E_LOOP_SCHEMA_VERSION,
    ok: false,
    authoritative_final_truth: authoritativeFinalTruth,
    anti_cheat_invariant: { ok: false, reason },
    capture: null,
    diagnostics_path: diagnosticsPath,
    evidence_dir: evidenceDir,
    failure_details: details,
    fixture_state: fixtureState,
    frontend: frontend ?? { healthy: false, baseUrl: details.attempted_frontend_url ?? "" },
    http_events: [],
    play_exit_code: null,
    playwright_report_path: path.join(evidenceDir, "playwright-report.json"),
    playwright_summary: { parsed: false },
    proxy: proxy ?? { healthy: false, baseUrl: details.attempted_backend_url ?? "" },
    result_path: resultPath,
    spec: args.spec,
    started_at: startedAt.toISOString(),
    steps: resultSteps,
  };
  writeFileSync(resultPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  return result;
}

function envTimeoutMs(name, fallback) {
  const parsed = Number(process.env[name] || "");
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback;
  return parsed;
}

function loadEnvLocal() {
  const envPath = path.join(repoRoot, ".env.local");
  if (!existsSync(envPath)) return [];
  const loaded = [];
  for (const [key, value] of parseEnvFile(readFileSync(envPath, "utf8"))) {
    // An explicit invocation is authoritative.  In particular, an isolated
    // Campaign candidate must not be silently redirected to a protected lane
    // by a developer-local .env.local value.
    process.env[key] ??= value;
    if (key === "SPIRIT_CODING_USE_PROXY" || key.startsWith("SOURCE_PROXY_")) {
      loaded.push({ key, value });
    }
  }
  return loaded;
}

function parseEnvFile(contents) {
  const values = [];
  for (const rawLine of contents.split(/\r?\n/u)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const withoutExport = line.startsWith("export ") ? line.slice("export ".length).trim() : line;
    const equalsIndex = withoutExport.indexOf("=");
    if (equalsIndex <= 0) continue;
    const key = withoutExport.slice(0, equalsIndex).trim();
    const rawValue = withoutExport.slice(equalsIndex + 1).trim();
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/u.test(key)) continue;
    values.push([key, unquoteEnvValue(rawValue)]);
  }
  return values;
}

function unquoteEnvValue(value) {
  if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
    return value.slice(1, -1);
  }
  return value;
}

function logLoadedEnv(entries) {
  console.log("Loaded .env.local keys for coding loop:");
  for (const entry of entries) {
    console.log(`- ${entry.key}=${maskEnvValue(entry.key, entry.value)}`);
  }
  console.log(`- SPIRIT_CODING_USE_PROXY=${process.env.SPIRIT_CODING_USE_PROXY}`);
}

function maskEnvValue(key, value) {
  return /KEY|TOKEN|SECRET/u.test(key) ? "[masked]" : value;
}

function startChild(label, command, commandArgs, logPath, extraEnv = {}) {
  const log = createWriteStream(logPath, { flags: "a" });
  log.write(`\n[${new Date().toISOString()}] starting ${label}: ${command} ${commandArgs.join(" ")}\n`);
  const child = spawn(command, commandArgs, {
    cwd: repoRoot,
    detached: process.platform !== "win32",
    env: childEnv(extraEnv),
    shell: process.platform === "win32",
    stdio: ["ignore", "pipe", "pipe"],
  });
  pipeTimestamped(child.stdout, log, label, "stdout");
  pipeTimestamped(child.stderr, log, label, "stderr");
  child.on("exit", (code, signal) => {
    log.write(`[${new Date().toISOString()}] ${label} exited code=${code ?? "null"} signal=${signal ?? "null"}\n`);
    log.end();
  });
  return { child, label, logPath };
}

function pipeTimestamped(stream, log, label, streamName) {
  let buffer = "";
  stream.on("data", (chunk) => {
    buffer += chunk.toString();
    let newlineIndex = buffer.indexOf("\n");
    while (newlineIndex >= 0) {
      const line = buffer.slice(0, newlineIndex).replace(/\r$/u, "");
      buffer = buffer.slice(newlineIndex + 1);
      log.write(`[${new Date().toISOString()}] [${label}:${streamName}] ${line}\n`);
      newlineIndex = buffer.indexOf("\n");
    }
  });
  stream.on("end", () => {
    if (buffer) {
      log.write(`[${new Date().toISOString()}] [${label}:${streamName}] ${buffer.replace(/\r$/u, "")}\n`);
    }
  });
}

async function stopSpawned(spawned) {
  for (const item of spawned.reverse()) {
    if (!item?.child || item.child.exitCode !== null || item.child.signalCode) continue;
    console.log(`Stopping spawned ${item.label} (log: ${relative(item.logPath)})`);
    terminateChildTree(item.child, "SIGTERM");
    await new Promise((resolve) => {
      const timeout = setTimeout(() => {
        if (item.child.exitCode === null && !item.child.signalCode) terminateChildTree(item.child, "SIGKILL");
        resolve();
      }, 5_000);
      item.child.once("exit", () => {
        clearTimeout(timeout);
        resolve();
      });
    });
  }
}

function terminateChildTree(child, signal) {
  if (!child.pid) return;
  try {
    if (process.platform === "win32") {
      child.kill(signal);
      return;
    }
    process.kill(-child.pid, signal);
  } catch {
    try {
      child.kill(signal);
    } catch {
      // Process already exited.
    }
  }
}

async function waitForHealth(label, probe, timeoutMs) {
  const started = Date.now();
  let last = null;
  while (Date.now() - started < timeoutMs) {
    last = await probe();
    if (last.healthy) return last;
    await sleep(1_000);
  }
  return { ...(last ?? {}), healthy: false, reason: `${label}_health_timeout_${timeoutMs}ms` };
}

async function probeFrontendHealth(baseUrl = trimTrailingSlash(process.env.PLAYWRIGHT_BASE_URL || "https://localhost:3000")) {
  const url = `${baseUrl}/coding`;
  try {
    const response = await fetchWithTimeout(url, 5_000);
    const workspaceProbe = await fetchWithTimeout(`${baseUrl}/v1/coding/workspace-read`, 5_000, {
      body: JSON.stringify({ path: "scripts/run-coding-e2e-loop.mjs" }),
      headers: { "content-type": "application/json" },
      method: "POST",
    }).catch((error) => ({ error }));
    const workspaceStatus = workspaceProbe && "status" in workspaceProbe ? workspaceProbe.status : 0;
    const workspacePayload = workspaceProbe && "json" in workspaceProbe
      ? await workspaceProbe.json().catch(() => null)
      : null;
    const reportedRoot = workspacePayload && typeof workspacePayload === "object"
      ? workspacePayload.root
      : null;
    const workspaceMatchesRepo =
      workspaceProbe &&
      "ok" in workspaceProbe &&
      workspaceProbe.ok === true &&
      repoRootsMatch(repoRoot, reportedRoot);
    return {
      baseUrl,
      healthy: response.ok && workspaceMatchesRepo,
      reason: response.ok && !workspaceMatchesRepo ? "frontend_wrong_or_stale_worktree" : undefined,
      expected_repo_root: repoRoot,
      reported_repo_root: typeof reportedRoot === "string" ? reportedRoot : "missing",
      status: response.status,
      workspace_probe_status: workspaceStatus,
      url,
    };
  } catch (error) {
    return { baseUrl, healthy: false, reason: errorMessage(error), url };
  }
}

async function probeProxyHealth(bases = proxyBases()) {
  const attempts = [];
  for (const base of bases) {
    const url = `${base}/v1/self/status`;
    try {
      const response = await fetchWithTimeout(url, 5_000);
      const payload = await response.json().catch(() => null);
      const laneActivationStatus = payload && typeof payload === "object"
        ? payload.lane_activation_status ?? payload.laneActivationStatus
        : null;
      const configuredRoots = payload && typeof payload === "object" && Array.isArray(payload.configured_roots)
        ? payload.configured_roots
        : [];
      const repoRootConfigured = configuredRoots.some((root) => {
        return root && typeof root === "object" && repoRootsMatch(repoRoot, root.path);
      });
      const serviceIdentity = payload && typeof payload === "object" ? payload.service : null;
      const healthy = response.ok && serviceIdentity === "source-proxy" && repoRootConfigured;
      attempts.push({
        base,
        expected_repo_root: repoRoot,
        lane_activation_status: laneActivationStatus,
        repo_root_configured: repoRootConfigured,
        reported_configured_roots: configuredRoots
          .map((root) => root && typeof root === "object" ? root.path : null)
          .filter((root) => typeof root === "string"),
        service_identity: serviceIdentity,
        status: response.status,
        url,
      });
      if (healthy) {
        return {
          attempts,
          baseUrl: base,
          expected_repo_root: repoRoot,
          healthy: true,
          lane_activation_status: laneActivationStatus,
          repo_root_configured: repoRootConfigured,
          status: response.status,
        };
      }
    } catch (error) {
      attempts.push({ base, error: errorMessage(error), url });
    }
  }
  return { attempts, baseUrl: bases[0], healthy: false, reason: "proxy_self_status_unhealthy" };
}

function proxyBases() {
  const explicit = process.env.SOURCE_PROXY_ORIGIN?.trim();
  if (explicit) return [trimTrailingSlash(explicit)];
  const port = process.env.SOURCE_PROXY_PORT || "8787";
  return [`https://127.0.0.1:${port}`];
}

async function fetchWithTimeout(url, timeoutMs, init = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

async function resetFixtureThroughProduct(frontendBaseUrl, requestedFixtureState) {
  const url = `${frontendBaseUrl}${fixtureResetRoute}`;
  try {
    const response = await fetchWithTimeout(url, 30_000, {
      body: JSON.stringify({
        fixture_state: "missing",
        reason: "managed_coding_e2e_precondition",
        requested_fixture_state: requestedFixtureState,
        selected_prompt_id: promptOneTargetPlugin.selected_prompt_id,
        target_plugin: promptOneTargetPlugin,
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    const payload = await response.json().catch(() => null);
    const responseStatus = payload && typeof payload === "object" ? payload.status : null;
    const cleanVerified = payload && typeof payload === "object" ? payload.clean_verified === true : false;
    const filesystemCleanVerified = fixtureRequiredRelativePaths.every((relativePath) => {
      return !existsSync(path.join(fixtureRoot, relativePath));
    });
    const ok = response.ok && responseStatus === "reset_verified" && cleanVerified && filesystemCleanVerified;
    return {
      ok,
      clean_verified: cleanVerified,
      expected_repo_root: repoRoot,
      filesystem_clean_verified: filesystemCleanVerified,
      fixture_root: fixtureRoot,
      http_status: response.status,
      requested_fixture_state: requestedFixtureState,
      response_status: typeof responseStatus === "string" ? responseStatus : "missing",
      route: fixtureResetRoute,
      url,
    };
  } catch (error) {
    return {
      ok: false,
      clean_verified: false,
      error: errorMessage(error),
      expected_repo_root: repoRoot,
      filesystem_clean_verified: false,
      fixture_root: fixtureRoot,
      requested_fixture_state: requestedFixtureState,
      response_status: "request_failed",
      route: fixtureResetRoute,
      url,
    };
  }
}

function seedFixtureState(state) {
  if (state === "missing") {
    throw new Error("The missing fixture state must come from the verified product reset, not direct filesystem setup.");
  }
  mkdirSync(path.join(fixtureRoot, "src"), { recursive: true });
  writeFixtureFiles(state);
}

function writeFixtureFiles(state) {
  writeFileSync(
    path.join(fixtureRoot, "README.md"),
    "# LumaCart\n\nIsolated dummy product storefront fixture for Source Proxy coder trials.\n",
    "utf8",
  );
  writeFileSync(
    path.join(fixtureRoot, "package.json"),
    `${JSON.stringify({ private: true, scripts: { start: "vite --host 127.0.0.1" } }, null, 2)}\n`,
    "utf8",
  );
  writeFileSync(path.join(fixtureRoot, "src", "products.js"), productsModule(), "utf8");
  writeFileSync(path.join(fixtureRoot, "src", "styles.css"), stylesCss(), "utf8");
  if (state === "bare") {
    writeFileSync(
      path.join(fixtureRoot, "index.html"),
      [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="utf-8">',
        "  <title>LumaCart</title>",
        '  <link rel="stylesheet" href="src/styles.css">',
        "</head>",
        "<body>",
        "  <h1>LumaCart</h1>",
        '  <main id="product-list"></main>',
        '  <script src="src/main.js"></script>',
        "</body>",
        "</html>",
        "",
      ].join("\n"),
      "utf8",
    );
    writeFileSync(
      path.join(fixtureRoot, "src", "main.js"),
      "console.log('LumaCart fixture loaded without rendering products.');\n",
      "utf8",
    );
    return;
  }

  writeFileSync(
    path.join(fixtureRoot, "index.html"),
    [
      "<!doctype html>",
      '<html lang="en">',
      "<head>",
      '  <meta charset="utf-8">',
      "  <title>LumaCart</title>",
      '  <link rel="stylesheet" href="src/styles.css">',
      "</head>",
      "<body>",
      "  <h1>LumaCart</h1>",
      '  <main id="product-list" aria-label="Products"></main>',
      '  <script type="module" src="src/main.js"></script>',
      "</body>",
      "</html>",
      "",
    ].join("\n"),
    "utf8",
  );
  writeFileSync(
    path.join(fixtureRoot, "src", "main.js"),
    [
      "import products from './products.js';",
      "",
      "const list = document.querySelector('#product-list');",
      "",
      "products.forEach((product) => {",
      "  const card = document.createElement('article');",
      "  card.className = 'product-card';",
      "  const name = document.createElement('h2');",
      "  name.textContent = product.name;",
      "  const price = document.createElement('p');",
      "  price.className = 'price';",
      "  price.textContent = `$${product.price}`;",
      "  const category = document.createElement('p');",
      "  category.className = 'category';",
      "  category.textContent = product.category;",
      "  const description = document.createElement('p');",
      "  description.className = 'description';",
      "  description.textContent = product.description;",
      "  card.appendChild(name);",
      "  card.appendChild(price);",
      "  card.appendChild(category);",
      "  card.appendChild(description);",
      "  list.appendChild(card);",
      "});",
      "",
    ].join("\n"),
    "utf8",
  );
}

function productsModule() {
  return [
    "const products = [",
    "  { id: 'desk-lamp', name: 'Desk Lamp', price: 32, category: 'Home', description: 'Warm light for a desk.' },",
    "  { id: 'coffee-maker', name: 'Coffee Maker', price: 58, category: 'Kitchen', description: 'Small brewer for mornings.' },",
    "  { id: 'water-bottle', name: 'Water Bottle', price: 18, category: 'Outdoor', description: 'Steel bottle for day trips.' },",
    "  { id: 'wireless-mouse', name: 'Wireless Mouse', price: 24, category: 'Office', description: 'Compact mouse for laptops.' },",
    "  { id: 'canvas-tote', name: 'Canvas Tote', price: 16, category: 'Everyday', description: 'Reusable carry bag.' },",
    "  { id: 'notebook-set', name: 'Notebook Set', price: 12, category: 'Office', description: 'Three soft-cover notebooks.' },",
    "];",
    "",
    "export default products;",
    "",
  ].join("\n");
}

function stylesCss() {
  return [
    "body { font-family: system-ui, sans-serif; margin: 2rem; }",
    "#product-list { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr)); }",
    ".product-card { border: 1px solid #ddd; border-radius: 0.5rem; padding: 1rem; }",
    ".price, .category { font-weight: 700; }",
    "",
  ].join("\n");
}

function runPlaywright({ capturePath, diagnosticsPath, frontendBaseUrl, proxyBaseUrl, spec, runnerEnvironment }) {
  console.log(`Running Playwright spec: ${spec}`);
  const command = process.env.PLAYWRIGHT_CLI || "npx";
  const commandArgs =
    command === "npx"
      ? ["playwright", "test", spec, "--project=chromium", "--reporter=json"]
      : ["test", spec, "--project=chromium", "--reporter=json"];
  return spawnSync(
    command,
    commandArgs,
    {
      cwd: repoRoot,
      encoding: "utf8",
      env: {
        ...runnerEnvironment,
        E2E_LOOP_CAPTURE_PATH: capturePath,
        E2E_LOOP_DIAGNOSTICS_PATH: diagnosticsPath,
        E2E_LOOP_FIXTURE_STATE: args.fixtureState,
        E2E_LOOP_PRODUCT_RESET_VERIFIED: "true",
        E2E_LOOP_SCHEMA_VERSION,
        PLAYWRIGHT_BASE_URL: frontendBaseUrl,
        SOURCE_PROXY_ORIGIN: proxyBaseUrl,
        SOURCE_PROXY_PORT: new URL(proxyBaseUrl).port,
      },
      maxBuffer: 1024 * 1024 * 100,
      shell: process.platform === "win32",
    },
  );
}

function evaluateAntiCheatInvariant(diagnostics) {
  if (!diagnostics.trim()) {
    return { ok: false, reason: "diagnostics_missing" };
  }
  if (/error_text:\s*SPIRIT_CODING_USE_PROXY is not true/u.test(diagnostics)) {
    return { ok: false, reason: "silent_env_409_persisted" };
  }
  const antiCheatStatuses = diagnosticValues(diagnostics, "anti_cheat_status");
  const antiCheatStatus = antiCheatStatuses.at(-1) ?? "";
  const hardFailIds = diagnosticValue(diagnostics, "anti_cheat_hard_fail_ids");
  const trustStatus = diagnosticValue(diagnostics, "trial_result_trust_status");
  const normalizedStatuses = antiCheatStatuses.map((status) => status.trim().toLowerCase());
  if (normalizedStatuses.some((status) => status === "not graded" || status === "not_run")) {
    return { ok: false, reason: "anti_cheat_not_evaluated", antiCheatStatuses };
  }
  if (normalizedStatuses.some((status) => ["blocked", "fail", "failed"].includes(status))) {
    return { ok: false, reason: "anti_cheat_failed", antiCheatStatuses, hardFailIds, trustStatus };
  }
  if (antiCheatStatus !== "passed") {
    return { ok: false, reason: "anti_cheat_not_passed", antiCheatStatuses, hardFailIds, trustStatus };
  }
  if (!trustStatus || trustStatus === "none" || /^(missing|blocked|not[_ ]run)/iu.test(trustStatus)) {
    return { ok: false, reason: "anti_cheat_passed_without_trust_status", antiCheatStatus, trustStatus };
  }
  return { ok: true, antiCheatStatus, antiCheatStatuses, trustStatus };
}

function diagnosticValue(diagnostics, key) {
  return diagnosticValues(diagnostics, key).at(-1) ?? "";
}

function diagnosticValues(diagnostics, key) {
  const pattern = new RegExp(`^${escapeRegExp(key)}:\\s*(.*)$`, "gmu");
  const matches = [...diagnostics.matchAll(pattern)];
  return matches.map((match) => match[1]?.trim() ?? "").filter(Boolean);
}

function parsePlaywrightJson(stdout) {
  if (!stdout.trim()) return null;
  try {
    return JSON.parse(stdout);
  } catch {
    const start = stdout.indexOf("{");
    const end = stdout.lastIndexOf("}");
    if (start >= 0 && end > start) {
      try {
        return JSON.parse(stdout.slice(start, end + 1));
      } catch {
        return null;
      }
    }
    return null;
  }
}

function summarizePlaywright(payload) {
  if (!payload || typeof payload !== "object") return { parsed: false };
  const stats = payload.stats && typeof payload.stats === "object" ? payload.stats : {};
  return {
    expected: stats.expected ?? null,
    failed: stats.unexpected ?? stats.failed ?? null,
    flaky: stats.flaky ?? null,
    parsed: true,
    skipped: stats.skipped ?? null,
  };
}

function printRunSummary(result, diagnostics) {
  console.log("");
  console.log("E2E_LOOP_SUMMARY");
  console.log(`schema_version: ${result.schema_version ?? "missing"}`);
  console.log(`overall: ${result.ok ? "PASS" : "FAIL"}`);
  console.log(`authoritative_truth_status: ${result.authoritative_final_truth?.truth_status ?? "NO_GO"}`);
  console.log(`commit_safe: ${String(result.authoritative_final_truth?.commit_safe === true)}`);
  console.log(`fixture_state: ${result.fixture_state}`);
  console.log(`spec: ${result.spec}`);
  console.log(`proxy: ${result.proxy.healthy ? "healthy" : "unhealthy"} ${result.proxy.baseUrl ?? ""}`);
  console.log(`frontend: ${result.frontend.healthy ? "healthy" : "unhealthy"} ${result.frontend.baseUrl ?? ""}`);
  console.log(`result_json: ${relative(result.result_path)}`);
  console.log(`diagnostics_txt: ${relative(result.diagnostics_path)}`);
  console.log("steps:");
  for (const item of result.steps) {
    console.log(`- ${item.name}: ${item.ok ? "PASS" : "FAIL"} ${item.reason ?? ""}`.trimEnd());
  }
  if (result.http_events.length > 0) {
    console.log("http_events:");
    for (const event of result.http_events) {
      console.log(`- ${event.method ?? "GET"} ${event.url} -> ${event.status}`);
    }
  }
  console.log(`anti_cheat_invariant: ${result.anti_cheat_invariant.ok ? "PASS" : "FAIL"} ${result.anti_cheat_invariant.reason ?? ""}`.trimEnd());
  const failedRequirements = result.authoritative_final_truth?.failed_requirements ?? [];
  if (failedRequirements.length > 0) {
    console.log(`failed_requirements: ${failedRequirements.join(", ")}`);
  }
  console.log("");
  console.log("DIAGNOSTICS_DUMP_BEGIN");
  console.log(diagnostics.trim() || "(not captured)");
  console.log("DIAGNOSTICS_DUMP_END");
  console.log("");
}

function step(name, ok, details = {}) {
  return { name, ok: Boolean(ok), ...details };
}

function readJsonFile(filePath) {
  if (!existsSync(filePath)) return null;
  try {
    return JSON.parse(readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function readTextIfExists(filePath) {
  return existsSync(filePath) ? readFileSync(filePath, "utf8") : "";
}

async function findAvailablePort(startPort) {
  for (let port = startPort; port < startPort + 100; port += 1) {
    if (await canListen(port)) return port;
  }
  throw new Error(`No available port found from ${startPort} to ${startPort + 99}.`);
}

function canListen(port) {
  return new Promise((resolve) => {
    const server = createServer();
    server.once("error", () => resolve(false));
    server.once("listening", () => {
      server.close(() => resolve(true));
    });
    server.listen(port, "127.0.0.1");
  });
}

async function watchLoop() {
  console.log("Watch mode enabled. Re-running after changes in src/, source_proxy/, and tests/ui-agent-trials/fixtures/.");
  let running = false;
  let queued = false;
  let lastSignature = watchedSignature();

  const execute = async () => {
    if (running) {
      queued = true;
      return;
    }
    running = true;
    try {
      await runOnce();
    } finally {
      running = false;
      if (queued) {
        queued = false;
        setTimeout(() => void execute(), 500);
      }
    }
  };

  await execute();
  setInterval(() => {
    const nextSignature = watchedSignature();
    if (nextSignature === lastSignature) return;
    lastSignature = nextSignature;
    setTimeout(() => void execute(), 500);
  }, 500);
}

function watchedSignature() {
  const roots = [
    path.join(repoRoot, "src"),
    path.join(repoRoot, "source_proxy"),
    path.join(repoRoot, "tests", "ui-agent-trials", "fixtures"),
  ];
  let signature = "";
  for (const root of roots) {
    signature += scanMtimes(root);
  }
  return signature;
}

function scanMtimes(root) {
  if (!existsSync(root)) return "";
  let output = "";
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const fullPath = path.join(root, entry.name);
    if (entry.name === "node_modules" || entry.name === ".git") continue;
    if (entry.isDirectory()) {
      output += scanMtimes(fullPath);
    } else if (entry.isFile()) {
      const stat = statSync(fullPath);
      output += `${relative(fullPath)}:${stat.mtimeMs}:${stat.size};`;
    }
  }
  return output;
}

function trimTrailingSlash(value) {
  return value.replace(/\/+$/u, "");
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function relative(filePath) {
  return path.relative(repoRoot, filePath).replace(/\\/g, "/");
}

function errorMessage(error) {
  if (error instanceof Error) return error.message;
  return String(error);
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
