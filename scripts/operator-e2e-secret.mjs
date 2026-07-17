import { createHash } from "node:crypto";
import { readFileSync, statSync } from "node:fs";

export const OPERATOR_E2E_SECRET_FILE = "/home/source/.config/spiritos/secrets/operator-approval.env";

function fingerprint(value) {
  return createHash("sha256").update(value).digest("hex").slice(0, 16);
}

function safeOrigin(origin) {
  try {
    const parsed = new URL(origin);
    return parsed.protocol === "https:" && ["localhost", "127.0.0.1"].includes(parsed.hostname) && Boolean(parsed.port);
  } catch {
    return false;
  }
}

/** Read the server-managed credential without ever returning it in a receipt. */
export function loadOperatorE2ESecret({ secretFile = OPERATOR_E2E_SECRET_FILE } = {}) {
  let details;
  try {
    details = statSync(secretFile);
  } catch (error) {
    return { ok: false, reason: "operator_e2e_secret_missing" };
  }
  if ((details.mode & 0o777) !== 0o600) return { ok: false, reason: "operator_e2e_secret_permissions_unsafe" };
  if (typeof process.getuid === "function" && details.uid !== process.getuid()) {
    return { ok: false, reason: "operator_e2e_secret_permissions_unsafe" };
  }
  let value;
  try {
    value = readFileSync(secretFile, "utf8").trim();
  } catch {
    return { ok: false, reason: "operator_e2e_secret_missing" };
  }
  const prefix = "SPIRITOS_OPERATOR_CREDENTIAL=";
  if (!value.startsWith(prefix) || !value.slice(prefix.length)) return { ok: false, reason: "operator_e2e_secret_missing" };
  const secret = value.slice(prefix.length);
  return {
    ok: true,
    secret,
    receipt: {
      source: "canonical_secret_file",
      secret_fingerprint: fingerprint(secret),
      secret_file_permission_verdict: "safe_0600_owner_current_user",
    },
  };
}

/** Minimum environment for the Playwright subprocess; it deliberately does not clone process.env. */
export function buildOperatorE2ERunnerEnv({ baseEnv = process.env, secret, extra = {} }) {
  if (!secret) return { ok: false, reason: "operator_e2e_secret_not_forwarded" };
  const env = {};
  for (const key of ["HOME", "PATH", "TMPDIR", "TEMP", "TMP", "NODE_PATH", "PLAYWRIGHT_BROWSERS_PATH"]) {
    if (baseEnv[key]) env[key] = baseEnv[key];
  }
  for (const [key, value] of Object.entries(baseEnv)) {
    if (key.startsWith("SOURCE_PROXY_") || key.startsWith("PLAYWRIGHT_")) env[key] = value;
  }
  Object.assign(env, extra, {
    NODE_TLS_REJECT_UNAUTHORIZED: "0",
    SPIRIT_CODING_USE_PROXY: "true",
    SPIRITOS_OPERATOR_E2E_SECRET: secret,
  });
  return { ok: true, env };
}

export function operatorE2EPreflight({ secretFile = OPERATOR_E2E_SECRET_FILE, origin = "", runnerEnv } = {}) {
  const loaded = loadOperatorE2ESecret({ secretFile });
  if (!loaded.ok) return { schema: "spiritos-operator-e2e-preflight/v1", ready: false, reason: loaded.reason };
  if (!safeOrigin(origin)) return { schema: "spiritos-operator-e2e-preflight/v1", ready: false, reason: "operator_e2e_origin_untrusted", ...loaded.receipt };
  if (!runnerEnv || runnerEnv.SPIRITOS_OPERATOR_E2E_SECRET !== loaded.secret) {
    return { schema: "spiritos-operator-e2e-preflight/v1", ready: false, reason: "operator_e2e_secret_not_forwarded", ...loaded.receipt };
  }
  return {
    schema: "spiritos-operator-e2e-preflight/v1",
    ready: true,
    ...loaded.receipt,
    runner_environment_binding: "explicit_child_env_only",
    operator_session_route_readiness: "canonical_route_required",
    trusted_origin: origin,
    target_browser_profile: "playwright-chromium",
  };
}
