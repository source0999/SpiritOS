import path from "node:path";

import { SPIRITFLIX_MEDIA_ROOT } from "../constants";
import { getSpiritFlixAdminAllowedRoots } from "../paths";

function isSubPath(parent: string, child: string): boolean {
  const relative = path.relative(parent, child);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

export function resolveSpiritFlixSmartMediaRoot(targetPath: string): string {
  const allowedRoots = getSpiritFlixAdminAllowedRoots();
  const match = [...allowedRoots]
    .sort((left, right) => right.length - left.length)
    .find((root) => isSubPath(root, targetPath));
  if (!match) return SPIRITFLIX_MEDIA_ROOT;

  let current = path.resolve(match);
  while (true) {
    if (path.basename(current) === "media") return current;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return match;
}
