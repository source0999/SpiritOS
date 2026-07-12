#!/usr/bin/env node
import { createHash } from "node:crypto";
import { existsSync, readFileSync, statSync } from "node:fs";

const DEFAULT_SECRET_FILE = "/home/source/.config/spiritos/secrets/spiritflix-e2e.env";
const secretFile = process.env.SPIRITFLIX_E2E_SECRET_FILE || DEFAULT_SECRET_FILE;
const source = process.env.SPIRITFLIX_E2E_USERNAME && process.env.SPIRITFLIX_E2E_PASSWORD ? "environment" : existsSync(secretFile) ? "secret_file" : "missing";
function parseEnv(text) { return Object.fromEntries(text.split(/\r?\n/).map((line) => line.trim()).filter((line) => line && !line.startsWith("#")).map((line) => { const index = line.indexOf("="); return index < 0 ? [line, ""] : [line.slice(0, index).trim(), line.slice(index + 1).trim()]; })); }
function result(payload) { process.stdout.write(JSON.stringify({ schema: "spiritflix-e2e-auth-preflight/v1", ...payload }) + "\n"); }
let values = {};
if (source === "environment") values = process.env;
if (source === "secret_file") { const mode = statSync(secretFile).mode & 0o777; if ((mode & 0o077) !== 0) { result({ ready: false, source, reason: "secret_file_permissions_too_open", targetServer: null }); process.exitCode = 2; } else values = parseEnv(readFileSync(secretFile, "utf8")); }
const username = values.SPIRITFLIX_E2E_USERNAME?.trim();
const password = values.SPIRITFLIX_E2E_PASSWORD;
const serverUrl = (values.SPIRITFLIX_E2E_SERVER_URL || "http://127.0.0.1:8096").replace(/\/+$/, "");
if (!username || !password || process.exitCode) { if (!process.exitCode) { result({ ready: false, source, reason: "dedicated_e2e_secret_not_configured", targetServer: source === "missing" ? null : serverUrl }); process.exitCode = 2; } } else {
  const response = await fetch(serverUrl + "/Users/AuthenticateByName", { method: "POST", headers: { "Content-Type": "application/json", "X-Emby-Authorization": 'MediaBrowser Client="SpiritOS E2E", Device="Campaign 1", DeviceId="spiritos-campaign-1-e2e", Version="1.0"' }, body: JSON.stringify({ Username: username, Pw: password }) });
  if (!response.ok) { result({ ready: false, source, reason: "dedicated_e2e_authentication_rejected", targetServer: serverUrl, status: response.status }); process.exitCode = 3; } else {
    const auth = await response.json(); const policy = auth.User?.Policy ?? {}; const accountFingerprint = createHash("sha256").update(username).digest("hex").slice(0, 16);
    result({ ready: policy.IsAdministrator !== true, source, targetServer: serverUrl, accountIdentifier: accountFingerprint, isAdministrator: policy.IsAdministrator === true, secretFingerprint: createHash("sha256").update(username + ":" + password).digest("hex").slice(0, 16), verdict: policy.IsAdministrator === true ? "rejected_admin_identity" : "dedicated_e2e_identity_ready" });
    if (policy.IsAdministrator === true) process.exitCode = 4;
  }
}
