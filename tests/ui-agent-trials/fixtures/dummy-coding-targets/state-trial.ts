export type TrialListItem = {
  id: string;
  label: string;
};

export function selectedItemAfterRefresh(
  items: TrialListItem[],
  selectedId: string | null,
): TrialListItem | null {
  if (!items.length) return null;
  return items[0];
}
