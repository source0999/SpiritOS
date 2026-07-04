#!/usr/bin/env tsx
import { writeFile } from "node:fs/promises";
import { runSpiritFlixJobWorkerOnce } from "../src/lib/spiritflix/admin/jobs";

const pollMs = Math.max(250, Number.parseInt(process.env.SPIRITFLIX_WORKER_POLL_MS ?? "5000", 10) || 5000);
const once = process.argv.includes("--once");
const workerId = process.env.SPIRITFLIX_WORKER_ID ?? `spiritflix-worker-${process.pid}`;
const pidfile = process.env.SPIRITFLIX_WORKER_PIDFILE ?? ".spiritflix-worker.pid";

async function tick() {
  return runSpiritFlixJobWorkerOnce({
    workerId,
    mediaRoot: process.env.SPIRITFLIX_WORKER_MEDIA_ROOT,
    conversionMode: process.env.SPIRITFLIX_CONVERSION_MODE === "execute" ? "execute" : "enqueue",
    autoMove: process.env.SPIRITFLIX_AUTO_MOVE === "1",
    autoEnroll: process.env.SPIRITFLIX_AUTO_ENROLL === "1",
  });
}

async function main() {
  await writeFile(pidfile, `${process.pid}
`, "utf8");
  do {
    const result = await tick();
    console.log(JSON.stringify({ at: new Date().toISOString(), ...result }));
    if (once) break;
    await new Promise((resolve) => setTimeout(resolve, pollMs));
  } while (true);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
