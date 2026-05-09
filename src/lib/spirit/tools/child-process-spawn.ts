// ── child-process-spawn - test-mockable spawn facade (shell always false at call site) ─
import "server-only";

import { spawn as nodeSpawn, type SpawnOptionsWithoutStdio } from "child_process";

/** Spawn without shell; isolated so Vitest can mock this module. */
export function spawnNoShell(
  command: string,
  args: readonly string[],
  options: SpawnOptionsWithoutStdio,
): ReturnType<typeof nodeSpawn> {
  return nodeSpawn(command, [...args], { ...options, shell: false });
}
