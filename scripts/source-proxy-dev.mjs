import { existsSync, readFileSync } from "node:fs";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "..");
const args = new Set(process.argv.slice(2));

loadEnvFiles();

const isHttps = args.has("--https");
const isLan = args.has("--lan");
const host = process.env.SOURCE_PROXY_HOST ?? (isLan ? "0.0.0.0" : "127.0.0.1");
const port = process.env.SOURCE_PROXY_PORT ?? "8787";
const certFile = process.env.SOURCE_PROXY_TLS_CERT ?? "certificates/spirit-dev.pem";
const keyFile = process.env.SOURCE_PROXY_TLS_KEY ?? "certificates/spirit-dev-key.pem";

const python = resolvePython();
const uvicornArgs = [
  "-m",
  "uvicorn",
  "source_proxy.main:app",
  "--host",
  host,
  "--port",
  port,
];

if (isHttps) {
  const certPath = path.resolve(repoRoot, certFile);
  const keyPath = path.resolve(repoRoot, keyFile);

  if (!existsSync(certPath) || !existsSync(keyPath)) {
    console.error(
      [
        "Source proxy TLS certificate files are missing.",
        `Expected cert: ${certPath}`,
        `Expected key:  ${keyPath}`,
        "Generate them with: bash ./scripts/gen-dev-cert.sh",
      ].join("\n"),
    );
    process.exit(1);
  }

  uvicornArgs.push("--ssl-certfile", certPath, "--ssl-keyfile", keyPath);
}

console.log(`Source proxy: ${isHttps ? "https" : "http"}://${host}:${port}`);
const child = spawn(python, uvicornArgs, {
  cwd: repoRoot,
  stdio: ["inherit", "inherit", "pipe"],
  env: process.env,
});

child.stderr.on("data", (chunk) => {
  const text = chunk.toString();
  process.stderr.write(text);

  if (text.includes("No module named uvicorn")) {
    process.stderr.write(
      [
        "",
        "Source proxy Python dependencies are not installed for this host.",
        "Run: npm run proxy:bootstrap",
        "Then retry: npm run proxy:https:lan",
        "",
      ].join("\n"),
    );
  }
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});

function resolvePython() {
  if (process.env.SOURCE_PROXY_PYTHON) {
    return process.env.SOURCE_PROXY_PYTHON;
  }

  const candidates =
    process.platform === "win32"
      ? [
          path.join(repoRoot, ".venv-source-proxy-windows", "Scripts", "python.exe"),
          path.join(repoRoot, ".venv-source-proxy", "Scripts", "python.exe"),
          "python",
        ]
      : [
          path.join(repoRoot, ".venv-source-proxy", "bin", "python"),
          "python3",
          "python",
        ];

  return candidates.find((candidate) => {
    return path.isAbsolute(candidate) ? existsSync(candidate) : true;
  });
}

function loadEnvFiles() {
  for (const envFile of [
    ".env",
    ".env.local",
    "config/source-proxy.env",
  ]) {
    const envPath = path.resolve(repoRoot, envFile);
    if (!existsSync(envPath)) {
      continue;
    }

    for (const [key, value] of parseEnvFile(readFileSync(envPath, "utf8"))) {
      process.env[key] ??= value;
    }
  }
}

function parseEnvFile(contents) {
  const values = [];
  for (const rawLine of contents.split(/\r?\n/u)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || line.startsWith("export ")) {
      continue;
    }

    const equalsIndex = line.indexOf("=");
    if (equalsIndex <= 0) {
      continue;
    }

    const key = line.slice(0, equalsIndex).trim();
    const rawValue = line.slice(equalsIndex + 1).trim();
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/u.test(key)) {
      continue;
    }

    values.push([key, unquoteEnvValue(rawValue)]);
  }
  return values;
}

function unquoteEnvValue(value) {
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  return value;
}
