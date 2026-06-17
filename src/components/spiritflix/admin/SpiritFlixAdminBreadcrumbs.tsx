"use client";

import { SPIRITFLIX_DATA_ROOT, SPIRITFLIX_MEDIA_ROOT } from "@/lib/spiritflix/admin/constants";

interface SpiritFlixAdminBreadcrumbsProps {
  path: string;
  onBrowsePath: (path: string) => void;
}

function normalizePath(value: string): string {
  return value.replace(/\\/g, "/").replace(/\/+$/, "");
}

export function buildAdminBreadcrumbSegments(path: string): Array<{ name: string; path: string }> {
  const normalized = normalizePath(path);
  const dataRoot = SPIRITFLIX_DATA_ROOT;
  const crumbs: Array<{ name: string; path: string }> = [
    { name: "Root", path: SPIRITFLIX_MEDIA_ROOT },
    { name: "DATA", path: SPIRITFLIX_MEDIA_ROOT },
  ];

  if (!normalized.startsWith(dataRoot)) {
    const tail = normalized.split("/").filter(Boolean).at(-1);
    if (tail) crumbs.push({ name: tail, path: normalized });
    return crumbs;
  }

  const relative = normalized.slice(dataRoot.length).replace(/^\/+/, "");
  if (!relative) return crumbs;

  const parts = relative.split("/").filter(Boolean);
  let accumulated = dataRoot;
  for (const part of parts) {
    accumulated = `${accumulated}/${part}`;
    crumbs.push({ name: part, path: accumulated });
  }

  return crumbs;
}

export function SpiritFlixAdminBreadcrumbs({ path, onBrowsePath }: SpiritFlixAdminBreadcrumbsProps) {
  const paths = buildAdminBreadcrumbSegments(path);

  return (
    <nav className="spiritflix-admin-breadcrumbs" aria-label="Folder breadcrumbs">
      {paths.map((crumb, index) => (
        <button key={`${crumb.path}-${index}`} type="button" onClick={() => onBrowsePath(crumb.path)}>
          {crumb.name}
        </button>
      ))}
    </nav>
  );
}
