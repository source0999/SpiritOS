export type CodingShellStatus = "active" | "legacy" | "experimental";

export type CodingShellRegistryEntry = {
  id: string;
  status: CodingShellStatus;
  route: string | null;
  component: string;
  ownerDecision: "canonical" | "alternate" | "undecided";
  rollback: string;
};

// Owns the /coding shell decision record. Alternate shells can stay available
// for review, but this registry is the place that prevents experiments from
// silently becoming canonical or being deleted without approval.
export const codingShellRegistry = [
  {
    id: "coding-cockpit-shell",
    status: "active",
    route: "/coding",
    component: "src/components/coding/CodingCockpitShell.tsx",
    ownerDecision: "canonical",
    rollback: "Revert /coding/page.tsx to direct CodingCockpitShell import only.",
  },
  {
    id: "coding-command-center-shell",
    status: "experimental",
    route: null,
    component: "src/components/coding/CodingCommandCenterShell.tsx",
    ownerDecision: "undecided",
    rollback: "Leave alternate shell unmounted; do not delete without Britton approval.",
  },
] as const satisfies readonly CodingShellRegistryEntry[];

export const activeCodingShell = codingShellRegistry.find(
  (shell) => shell.status === "active" && shell.route === "/coding",
) ?? codingShellRegistry[0];

export function codingShellById(id: string): CodingShellRegistryEntry | undefined {
  return codingShellRegistry.find((shell) => shell.id === id);
}

export function codingShellsByStatus(status: CodingShellStatus): CodingShellRegistryEntry[] {
  return codingShellRegistry.filter((shell) => shell.status === status);
}
