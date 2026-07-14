import { createHash, createHmac, randomBytes, timingSafeEqual } from "node:crypto";
import { mkdir, open, readFile, rename, stat, writeFile } from "node:fs/promises";
import path from "node:path";

const OPERATOR_ID = "spiritos-local-operator";
const OPERATOR_ROLE = "approval-issuer";
const COOKIE_NAME = "spiritos_operator_approval";
const SECRET_PATH = "/home/source/.config/spiritos/secrets/operator-approval.env";
const STATE_PATH = "/home/source/.local/state/spiritos/operator-approval-sessions.json";
const MAX_SESSION_SECONDS = 30 * 60;

type Session = { csrf_hash: string; expires_at: string; id: string; revoked_at?: string };
type Audit = { action: string; at: string; operator: string; origin: string; preview_id?: string; session_fingerprint: string };
type State = { audit: Audit[]; sessions: Record<string, Session> };

function modeIs(expected: number, value: number) { return (value & 0o777) === expected; }
function fingerprint(value: string) { return createHash("sha256").update(value).digest("hex").slice(0, 16); }
function cookieValue(request: Request, name: string) {
  return request.headers.get("cookie")?.split(";").map((part) => part.trim()).find((part) => part.startsWith(`${name}=`))?.slice(name.length + 1) ?? "";
}
function allowedOrigins() { return (process.env.SPIRITOS_OPERATOR_ALLOWED_ORIGINS ?? "").split(",").map((value) => value.trim()).filter(Boolean); }
function e2eMode() { return process.env.SPIRITOS_OPERATOR_E2E_MODE === "true"; }
function secretPath() { return e2eMode() ? process.env.SPIRITOS_OPERATOR_E2E_SECRET_PATH ?? SECRET_PATH : SECRET_PATH; }
function statePath() { return e2eMode() ? process.env.SPIRITOS_OPERATOR_E2E_STATE_PATH ?? STATE_PATH : STATE_PATH; }

export function operatorCookieName() { return COOKIE_NAME; }

export function assertTrustedOperatorOrigin(request: Request): { origin: string } {
  const origin = request.headers.get("origin") ?? "";
  const host = request.headers.get("host") ?? "";
  const allowed = allowedOrigins();
  if (!origin || allowed.length === 0 || !allowed.includes(origin)) throw new Error("operator_origin_untrusted");
  let originHost = "";
  try { originHost = new URL(origin).host; } catch { throw new Error("operator_origin_untrusted"); }
  if (!host || host !== originHost) throw new Error("operator_host_mismatch");
  return { origin };
}

async function ensureDirectory(directory: string) {
  await mkdir(directory, { recursive: true, mode: 0o700 });
  const details = await stat(directory);
  if (!modeIs(0o700, details.mode)) throw new Error("operator_unsafe_directory_permissions");
}

async function operatorSecret() {
  const testSecret = e2eMode() ? process.env.SPIRITOS_OPERATOR_E2E_SECRET : "";
  if (testSecret) return testSecret;
  const location = secretPath();
  const directory = path.dirname(location);
  await ensureDirectory(directory);
  try {
    const details = await stat(location);
    if (!modeIs(0o600, details.mode)) throw new Error("operator_unsafe_secret_permissions");
    const value = (await readFile(location, "utf8")).trim();
    if (!value.startsWith("SPIRITOS_OPERATOR_CREDENTIAL=")) throw new Error("operator_secret_malformed");
    return value.slice("SPIRITOS_OPERATOR_CREDENTIAL=".length);
  } catch (error) {
    if (!(error instanceof Error) || !("code" in error) || error.code !== "ENOENT") throw error;
  }
  const credential = randomBytes(48).toString("base64url");
  const handle = await open(location, "wx", 0o600);
  await handle.writeFile(`SPIRITOS_OPERATOR_CREDENTIAL=${credential}\n`, "utf8");
  await handle.close();
  return credential;
}

async function loadState(): Promise<State> {
  const location = statePath();
  await ensureDirectory(path.dirname(location));
  try {
    const details = await stat(location);
    if (!modeIs(0o600, details.mode)) throw new Error("operator_unsafe_state_permissions");
    const parsed = JSON.parse(await readFile(location, "utf8")) as Partial<State>;
    return { audit: Array.isArray(parsed.audit) ? parsed.audit.slice(-200) as Audit[] : [], sessions: parsed.sessions ?? {} };
  } catch (error) {
    if (error instanceof Error && "code" in error && error.code === "ENOENT") return { audit: [], sessions: {} };
    throw error;
  }
}

async function saveState(state: State) {
  const location = statePath();
  const temporary = `${location}.${randomBytes(8).toString("hex")}.tmp`;
  await writeFile(temporary, JSON.stringify(state), { encoding: "utf8", mode: 0o600 });
  await rename(temporary, location);
}

function credentialMatches(actual: string, expected: string) {
  const actualBytes = Buffer.from(actual);
  const expectedBytes = Buffer.from(expected);
  return actualBytes.length === expectedBytes.length && timingSafeEqual(actualBytes, expectedBytes);
}

export async function createOperatorSession(request: Request, credential: string) {
  const { origin } = assertTrustedOperatorOrigin(request);
  if (!credentialMatches(credential, await operatorSecret())) throw new Error("operator_credential_invalid");
  const state = await loadState();
  const id = randomBytes(32).toString("base64url");
  const csrf = randomBytes(32).toString("base64url");
  const expires_at = new Date(Date.now() + MAX_SESSION_SECONDS * 1000).toISOString();
  state.sessions[id] = { csrf_hash: fingerprint(csrf), expires_at, id };
  state.audit.push({ action: "session_created", at: new Date().toISOString(), operator: OPERATOR_ID, origin, session_fingerprint: fingerprint(id) });
  await saveState(state);
  return { csrf, expires_at, id, max_age_seconds: MAX_SESSION_SECONDS, operator: OPERATOR_ID, role: OPERATOR_ROLE };
}

export async function requireOperatorSession(request: Request, requireCsrf = true) {
  const { origin } = assertTrustedOperatorOrigin(request);
  const id = cookieValue(request, COOKIE_NAME);
  if (!id) throw new Error("operator_session_missing");
  const state = await loadState();
  const session = state.sessions[id];
  if (!session) throw new Error("operator_session_invalid");
  if (session.revoked_at) throw new Error("operator_session_revoked");
  if (Date.parse(session.expires_at) <= Date.now()) throw new Error("operator_session_expired");
  if (requireCsrf && fingerprint(request.headers.get("x-spiritos-csrf") ?? "") !== session.csrf_hash) throw new Error("operator_csrf_invalid");
  return { id, origin, operator: OPERATOR_ID, role: OPERATOR_ROLE };
}

export async function revokeOperatorSession(session: Awaited<ReturnType<typeof requireOperatorSession>>) {
  const state = await loadState();
  const record = state.sessions[session.id];
  if (!record) throw new Error("operator_session_invalid");
  record.revoked_at = new Date().toISOString();
  state.audit.push({ action: "session_revoked", at: record.revoked_at, operator: session.operator, origin: session.origin, session_fingerprint: fingerprint(session.id) });
  await saveState(state);
}

export async function createOperatorApprovalAssertion(
  session: Awaited<ReturnType<typeof requireOperatorSession>>,
  input: { action: "approve" | "reject"; generation: number; preview_id: string; task_id: string },
) {
  const expires_at = new Date(Date.now() + 60_000).toISOString();
  const payload = JSON.stringify({ action: input.action, expires_at, generation: input.generation, operator: session.operator, preview_id: input.preview_id, role: session.role, session_id: session.id, task_id: input.task_id });
  const encoded = Buffer.from(payload, "utf8").toString("base64url");
  const signature = createHmac("sha256", await operatorSecret()).update(encoded).digest("base64url");
  return `${encoded}.${signature}`;
}

export async function auditOperatorAction(session: Awaited<ReturnType<typeof requireOperatorSession>>, action: "approve" | "reject", previewId: string) {
  const state = await loadState();
  state.audit.push({ action, at: new Date().toISOString(), operator: session.operator, origin: session.origin, preview_id: previewId, session_fingerprint: fingerprint(session.id) });
  await saveState(state);
}
