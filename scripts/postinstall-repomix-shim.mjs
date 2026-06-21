#!/usr/bin/env node
import { chmodSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = resolve(fileURLToPath(import.meta.url), "..", "..");
const binPath = resolve(repoRoot, "node_modules", ".bin", "repomix");
const shimPath = resolve(repoRoot, "scripts", "repomix-llm.mjs");
const shim = `#!/usr/bin/env sh
exec node "${shimPath}" "$@"
`;

writeFileSync(binPath, shim);
chmodSync(binPath, 0o755);
