import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const blueprintsDir = path.join(root, "_blueprints");
const indexPath = path.join(blueprintsDir, "INDEX.md");

const requiredDirectories = [
  "_schema",
  "current",
  "components",
  "runbooks",
  "history",
  "proposals",
];

const allowedTopLevelDirectories = new Set([...requiredDirectories, "sandbox"]);
const allowedTopLevelFiles = new Set(["INDEX.md"]);

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

const allowedDocTypes = new Set([
  "current_state",
  "component_blueprint",
  "component_roadmap",
  "runbook",
  "phase_receipt",
  "visual_sandbox",
  "proposal_queue",
  "schema",
  "index",
]);

const allowedWritePolicies = new Set([
  "proposal_only_until_dashboard_approved",
  "historical_read_only",
  "sandbox_proposal_only",
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

async function validateLayout(errors) {
  const entries = await readdir(blueprintsDir, { withFileTypes: true });
  const seenDirectories = new Set();

  for (const entry of entries) {
    if (entry.isDirectory()) {
      seenDirectories.add(entry.name);
      if (!allowedTopLevelDirectories.has(entry.name)) {
        errors.push(`_blueprints/: unmanaged top-level directory '${entry.name}'`);
      }
    } else if (entry.isFile() && !allowedTopLevelFiles.has(entry.name)) {
      errors.push(`_blueprints/: unmanaged top-level file '${entry.name}'`);
    }
  }

  for (const dir of requiredDirectories) {
    if (!seenDirectories.has(dir)) {
      errors.push(`_blueprints/: missing required directory '${dir}/'`);
    }
  }
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
  let currentKey = null;
  for (const line of match[1].split(/\r?\n/)) {
    const fieldMatch = line.match(/^([A-Za-z0-9_]+):(?:\s*(.*))?$/);
    if (fieldMatch) {
      const value = fieldMatch[2] ?? "";
      fields.set(fieldMatch[1], value === "[]" ? [] : value);
      currentKey = fieldMatch[1];
      continue;
    }

    const listMatch = line.match(/^\s*-\s*(.+?)\s*$/);
    if (listMatch && currentKey) {
      const existing = fields.get(currentKey);
      const values = Array.isArray(existing) ? existing : [];
      values.push(listMatch[1]);
      fields.set(currentKey, values);
    }
  }

  return fields;
}

function stringValue(value) {
  return Array.isArray(value) ? "" : (value ?? "").trim();
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

  const blueprintId = stringValue(fields.get("blueprint_id"));
  if (blueprintId && !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(blueprintId)) {
    errors.push(`${relPath}: blueprint_id must be stable kebab-case`);
  }

  const docType = stringValue(fields.get("doc_type"));
  if (docType && !allowedDocTypes.has(docType)) {
    errors.push(`${relPath}: invalid doc_type '${docType}'`);
  }

  const status = stringValue(fields.get("status"));
  if (status && !allowedStatuses.has(status)) {
    errors.push(`${relPath}: invalid status '${status}'`);
  }

  const writePolicy = stringValue(fields.get("write_policy"));
  if (writePolicy && !allowedWritePolicies.has(writePolicy)) {
    errors.push(`${relPath}: invalid write_policy '${writePolicy}'`);
  }

  const sourceOfTruth = parseBoolean(stringValue(fields.get("source_of_truth")));
  if (sourceOfTruth === null) {
    errors.push(`${relPath}: source_of_truth must be true or false`);
  } else if (sourceOfTruth && !isSourceOfTruthAllowed(relPath)) {
    errors.push(`${relPath}: source_of_truth true is only allowed for canonical current/component/schema docs or INDEX.md`);
  }

  const lastVerified = stringValue(fields.get("last_verified"));
  if (lastVerified && !/^\d{4}-\d{2}-\d{2}$/.test(lastVerified)) {
    errors.push(`${relPath}: last_verified must use YYYY-MM-DD`);
  }
  if (sourceOfTruth === true && !lastVerified) {
    errors.push(`${relPath}: source_of_truth documents must have last_verified`);
  }

  const codePaths = fields.get("code_paths");
  if (status === "active" && (!Array.isArray(codePaths) || codePaths.length === 0)) {
    errors.push(`${relPath}: active blueprints must list at least one code_paths entry`);
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

await validateLayout(errors);

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
    blueprintId: stringValue(fields.get("blueprint_id")),
    status: stringValue(fields.get("status")),
    docType: stringValue(fields.get("doc_type")),
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
