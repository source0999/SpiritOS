import "server-only";

import fs from "node:fs/promises";
import path from "node:path";

const MAX_SNAPSHOT_FILE_BYTES = 16 * 1024 * 1024;

export type SpiritFlixFileMutationSnapshot = {
  files: Array<{ content: Buffer | null; mode: number | null; path: string }>;
};

export async function captureSpiritFlixFiles(
  candidates: Array<string | null | undefined>,
): Promise<SpiritFlixFileMutationSnapshot> {
  const paths = [...new Set(candidates.filter((candidate): candidate is string => Boolean(candidate)).map((candidate) => path.resolve(candidate)))];
  const files = await Promise.all(paths.map(async (candidate) => {
    try {
      const details = await fs.lstat(candidate);
      if (details.isSymbolicLink() || !details.isFile()) throw new Error("spiritflix_admin_snapshot_target_invalid");
      if (details.size > MAX_SNAPSHOT_FILE_BYTES) throw new Error("spiritflix_admin_snapshot_too_large");
      return { content: await fs.readFile(candidate), mode: details.mode, path: candidate };
    } catch (error) {
      if (error instanceof Error && "code" in error && error.code === "ENOENT") {
        return { content: null, mode: null, path: candidate };
      }
      throw error;
    }
  }));
  return { files };
}

export async function restoreSpiritFlixFiles(snapshot: SpiritFlixFileMutationSnapshot): Promise<void> {
  for (const file of snapshot.files) {
    if (file.content === null) {
      await fs.unlink(file.path).catch((error: NodeJS.ErrnoException) => {
        if (error.code !== "ENOENT") throw error;
      });
      continue;
    }
    await fs.mkdir(path.dirname(file.path), { recursive: true });
    const temporary = `${file.path}.rollback-${process.pid}-${Date.now()}`;
    await fs.writeFile(temporary, file.content, file.mode === null ? undefined : { mode: file.mode });
    await fs.rename(temporary, file.path);
  }
}
