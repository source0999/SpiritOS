export type TrialListItem = {
  id: string;
  label: string;
};

export function selectedItemAfterRefresh(
  items: TrialListItem[],
  selectedId: string | null,
): TrialListItem | null {
  if (!items.length) return null;
  const foundItem = items.find(item => item.id === selectedId);
  return foundItem || items[0];
}
