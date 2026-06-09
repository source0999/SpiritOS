import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

export const gateDir = path.resolve(".gate");
export const gateStatePath = path.join(gateDir, "state.json");

const validStatuses = new Set([
  "WAITING_FOR_HUMAN",
  "APPROVED_INCREMENT",
  "RUNNING_INCREMENT",
  "BLOCKED",
]);

export function readGateState() {
  let raw;
  try {
    raw = fs.readFileSync(gateStatePath, "utf8");
  } catch (error) {
    throw new Error(`Gate state is missing at ${gateStatePath}: ${error.message}`);
  }

  let state;
  try {
    state = JSON.parse(raw);
  } catch (error) {
    throw new Error(`Gate state is malformed JSON: ${error.message}`);
  }

  validateGateState(state);
  return state;
}

export function writeGateState(nextState) {
  validateGateState(nextState);
  fs.mkdirSync(gateDir, { recursive: true });
  fs.writeFileSync(gateStatePath, `${JSON.stringify(nextState, null, 2)}\n`);
}

export function validateGateState(state) {
  if (!state || typeof state !== "object" || Array.isArray(state)) {
    throw new Error("Gate state must be a JSON object.");
  }

  if (!validStatuses.has(state.status)) {
    throw new Error(`Gate status is invalid: ${String(state.status)}`);
  }

  for (const key of [
    "approved_increment",
    "last_completed_increment",
    "approval_token",
    "updated_at",
    "notes",
  ]) {
    if (!(key in state)) {
      throw new Error(`Gate state is missing required field: ${key}`);
    }
  }

  if (
    state.approved_increment !== null &&
    typeof state.approved_increment !== "string"
  ) {
    throw new Error("approved_increment must be null or a string.");
  }

  if (
    state.last_completed_increment !== null &&
    typeof state.last_completed_increment !== "string"
  ) {
    throw new Error("last_completed_increment must be null or a string.");
  }

  if (state.approval_token !== null && typeof state.approval_token !== "string") {
    throw new Error("approval_token must be null or a string.");
  }

  if (state.updated_at !== null && typeof state.updated_at !== "string") {
    throw new Error("updated_at must be null or an ISO timestamp string.");
  }

  if (typeof state.notes !== "string") {
    throw new Error("notes must be a string.");
  }
}

export function requireIncrement(value) {
  if (!value || typeof value !== "string" || value.trim() !== value) {
    throw new Error("Increment id is required and must not have surrounding whitespace.");
  }

  if (!/^[0-9]+(?:\.[0-9]+)+$/.test(value)) {
    throw new Error(`Increment id must look like 1.1 or 2.3: ${value}`);
  }

  return value;
}

export function nowIso() {
  return new Date().toISOString();
}

export function newApprovalToken(increment) {
  const tokenBody = crypto.randomBytes(12).toString("hex");
  return `${increment}:${tokenBody}`;
}

export function printState(state) {
  console.log(JSON.stringify(state, null, 2));
}

export function fail(error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
