import { spawnSync } from "node:child_process";

const isWindows = process.platform === "win32";
const command = isWindows ? "powershell" : "bash";
const args = isWindows
  ? ["-ExecutionPolicy", "Bypass", "-File", "./scripts/source-proxy-bootstrap.ps1"]
  : ["./scripts/source-proxy-bootstrap.sh"];

const result = spawnSync(command, args, {
  stdio: "inherit",
  shell: false,
});

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 0);
