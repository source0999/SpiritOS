import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const blueprintsDir = path.join(root, "_blueprints");
const indexPath = path.join(blueprintsDir, "INDEX.md");

const requiredFields = [
  "blueprint_id",
  "title",
  "project",
  "component",
  "doc_type",
  "status",
  "source_of_truth",
  "owner",
  "code_paths",
  "related_blueprints",
  "write_policy",
  "last_verified",
];

const allowedStatuses = new Set([
  "active",
  "planned",
  "runbook",
  "historical",
  "sandbox",
  "deprecated",
]);

const sourceOfTruthPrefixes = ["current/", "components/", "_schema/"];

async function listMarkdownFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await listMarkdownFiles(fullPath)));
    } else if (entry.isFile() && entry.name.endsWith(".md")) {
      files.push(fullPath);
    }
  }

  return files;
}

function toBlueprintPath(filePath) {
  return path.relative(blueprintsDir, filePath).split(path.sep).join("/");
}

function parseFrontmatter(content) {
  if (!content.startsWith("---\n") && !content.startsWith("---\r\n")) {
    return null;
  }

  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  if (!match) {
    return null;
  }

  const fields = new Map();
  for (const line of match[1].split(/\r?\n/)) {
    const fieldMatch = line.match(/^([A-Za-z0-9_]+):(?:\s*(.*))?$/);
    if (fieldMatch) {
      fields.set(fieldMatch[1], fieldMatch[2] ?? "");
    }
  }

  return fields;
}

function parseBoolean(value) {
  if (value === "true") return true;
  if (value === "false") return false;
  return null;
}

function isSourceOfTruthAllowed(relPath) {
  return (
    relPath === "INDEX.md" ||
    sourceOfTruthPrefixes.some((prefix) => relPath.startsWith(prefix))
  );
}

function validateFrontmatter(relPath, fields, errors) {
  for (const field of requiredFields) {
    if (!fields.has(field)) {
      errors.push(`${relPath}: missing required frontmatter field '${field}'`);
    }
  }

  const status = fields.get("status")?.trim();
  if (status && !allowedStatuses.has(status)) {
    errors.push(`${relPath}: invalid status '${status}'`);
  }

  const sourceOfTruth = parseBoolean(fields.get("source_of_truth")?.trim());
  if (sourceOfTruth === null) {
    errors.push(`${relPath}: source_of_truth must be true or false`);
  } else if (sourceOfTruth && !isSourceOfTruthAllowed(relPath)) {
    errors.push(`${relPath}: source_of_truth true is only allowed for canonical current/component/schema docs or INDEX.md`);
  }

  const lastVerified = fields.get("last_verified")?.trim();
  if (lastVerified && !/^\d{4}-\d{2}-\d{2}$/.test(lastVerified)) {
    errors.push(`${relPath}: last_verified must use YYYY-MM-DD`);
  }
}

function extractIndexedPaths(indexContent) {
  return new Set(
    [...indexContent.matchAll(/`([^`]+\.md)`/g)].map((match) => match[1])
  );
}

const files = (await listMarkdownFiles(blueprintsDir)).sort();
const errors = [];
const records = [];

for (const file of files) {
  const relPath = toBlueprintPath(file);
  const content = await readFile(file, "utf8");
  const fields = parseFrontmatter(content);

  if (!fields) {
    errors.push(`${relPath}: missing YAML frontmatter block at top of file`);
    continue;
  }

  validateFrontmatter(relPath, fields, errors);
  records.push({
    relPath,
    blueprintId: fields.get("blueprint_id")?.trim(),
    status: fields.get("status")?.trim(),
    docType: fields.get("doc_type")?.trim(),
  });
}

const blueprintIds = new Map();
for (const record of records) {
  if (!record.blueprintId) continue;
  const existing = blueprintIds.get(record.blueprintId);
  if (existing) {
    errors.push(`${record.relPath}: duplicate blueprint_id '${record.blueprintId}' also used by ${existing}`);
  } else {
    blueprintIds.set(record.blueprintId, record.relPath);
  }
}

const indexContent = await readFile(indexPath, "utf8");
const indexedPaths = extractIndexedPaths(indexContent);
const expectedIndexedPaths = records
  .map((record) => record.relPath)
  .filter((relPath) => relPath !== "INDEX.md");

for (const relPath of expectedIndexedPaths) {
  if (!indexedPaths.has(relPath)) {
    errors.push(`INDEX.md: missing indexed document '${relPath}'`);
  }
}

for (const relPath of indexedPaths) {
  if (!expectedIndexedPaths.includes(relPath)) {
    errors.push(`INDEX.md: references missing or unmanaged document '${relPath}'`);
  }
}

if (errors.length > 0) {
  console.error("Blueprint index invalid");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

const activeCount = records.filter((record) => record.status === "active").length;
const runbookCount = records.filter((record) => record.status === "runbook").length;
const historicalCount = records.filter((record) => record.status === "historical").length;

console.log("Blueprint index valid");
console.log(`Active blueprints: ${activeCount}`);
console.log(`Runbooks: ${runbookCount}`);
console.log(`Historical docs: ${historicalCount}`);
console.log("No missing required metadata");
