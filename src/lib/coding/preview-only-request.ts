export function taskRequestsPreviewOnly(value: string): boolean {
  const text = value.toLowerCase();
  return (
    /\bpreview[- ]only\b/.test(text) ||
    /\bpreview\s+diff\s+only\b/.test(text) ||
    /\bpreview\b[^.\n]{0,48}\bonly\b/.test(text) ||
    /\bno\s+apply\b/.test(text) ||
    /\bdo\s+not\s+apply\b/.test(text) ||
    /\bdon't\s+apply\b/.test(text)
  );
}
