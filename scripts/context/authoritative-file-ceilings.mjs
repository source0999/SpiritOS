import { existsSync, readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";

const repoRoot = resolve(import.meta.dirname, "../..");
const AUTHORITATIVE_FILES_CONFIG = resolve(repoRoot, "config", "context-authoritative-files.json");

export function assertAuthoritativeFileCeilings(options = {}) {
  const configPath = options.configPath || AUTHORITATIVE_FILES_CONFIG;
  const configured = JSON.parse(readFileSync(configPath, "utf8"));
  const override = Number(options.maxBytesOverride || process.env.SPIRIT_CONTEXT_AUTHORITATIVE_MAX_BYTES || 0);
  const violations = (configured.files || []).flatMap((entry) => {
    const absolutePath = resolve(repoRoot, entry.path);
    if (!existsSync(absolutePath)) return [`missing ${entry.path}`];
    const maxBytes = override > 0 ? override : Number(entry.max_bytes);
    const size = statSync(absolutePath).size;
    return size > maxBytes ? [`${entry.path} is ${size} bytes (ceiling ${maxBytes} bytes)`] : [];
  });

  if (violations.length) {
    throw new Error(
      `AUTHORITATIVE_FILE_SIZE_CEILING_EXCEEDED\n${violations.map((violation) => `- ${violation}`).join("\n")}`,
    );
  }
}
