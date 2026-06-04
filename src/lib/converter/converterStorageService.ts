import crypto from "crypto";
import fs from "fs/promises";
import path from "path";

import { CONVERTER_ROOTS, type ConverterOutputKey } from "@/lib/converter/converterTypes";

export type ConverterRootMap = Record<keyof typeof CONVERTER_ROOTS, string>;

const SECRET_PATTERNS: RegExp[] = [
  /(authorization|cookie|token|api[_-]?key|secret|password)=([^&\s]+)/gi,
  /(Bearer\s+)[A-Za-z0-9._~+/=-]+/gi,
  /(--cookies(?:-from-browser)?\s+)(\S+)/gi,
];

export function sanitizeFilename(input: string, fallback = "untitled"): string {
  const sanitized = input
    .normalize("NFKD")
    .replace(/[^\w.\- ]+/g, "")
    .replace(/\s+/g, "-")
    .replace(/\.+/g, ".")
    .replace(/^-+|-+$/g, "")
    .slice(0, 120);

  if (!sanitized || sanitized === "." || sanitized === "..") {
    return fallback;
  }

  return sanitized;
}

export function assertUnderRoot(root: string, targetPath: string): string {
  const resolvedRoot = path.resolve(root);
  const resolvedTarget = path.resolve(targetPath);
  const relative = path.relative(resolvedRoot, resolvedTarget);

  if (relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative))) {
    return resolvedTarget;
  }

  throw new Error(`Output path escapes converter root: ${targetPath}`);
}

export function converterPath(
  roots: ConverterRootMap,
  rootKey: ConverterOutputKey,
  jobId: string,
  fileName: string,
): string {
  const safeJobId = sanitizeFilename(jobId, "job");
  const safeFileName = sanitizeFilename(fileName, "artifact");
  return assertUnderRoot(roots[rootKey], path.join(roots[rootKey], safeJobId, safeFileName));
}

export function redactDiagnostics(input: string): string {
  return SECRET_PATTERNS.reduce(
    (text, pattern) =>
      text.replace(pattern, (_match, prefix) => `${prefix}[REDACTED]`),
    input,
  );
}

export async function ensureConverterRoots(roots: ConverterRootMap = CONVERTER_ROOTS): Promise<void> {
  await Promise.all(Object.values(roots).map((root) => fs.mkdir(root, { recursive: true })));
}

export async function writeJsonFile(targetPath: string, value: unknown): Promise<void> {
  await fs.mkdir(path.dirname(targetPath), { recursive: true });
  await fs.writeFile(targetPath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

export async function writeTextFile(targetPath: string, value: string): Promise<void> {
  await fs.mkdir(path.dirname(targetPath), { recursive: true });
  await fs.writeFile(targetPath, value, "utf8");
}

export async function sha256File(filePath: string): Promise<string> {
  const buffer = await fs.readFile(filePath);
  return crypto.createHash("sha256").update(buffer).digest("hex");
}
