import appliedRunReceiptSchema from "../../../packages/contracts/schemas/shared/applied-run-receipt.schema.json";

type JsonSchema = {
  enum?: unknown[];
  minLength?: number;
  properties?: Record<string, JsonSchema>;
  required?: string[];
  type?: string;
};

function matchesSchema(value: unknown, schema: JsonSchema): boolean {
  if (schema.type === "string" && typeof value !== "string") return false;
  if (schema.type === "array" && !Array.isArray(value)) return false;
  if (schema.type === "boolean" && typeof value !== "boolean") return false;
  if (schema.type === "object" && (!value || typeof value !== "object" || Array.isArray(value))) return false;
  if (typeof value === "string" && schema.minLength && value.length < schema.minLength) return false;
  if (schema.enum && !schema.enum.includes(value)) return false;
  return true;
}

export function isSharedAppliedRunReceipt(value: unknown): value is Record<string, unknown> {
  if (!matchesSchema(value, appliedRunReceiptSchema)) return false;
  const record = value as Record<string, unknown>;
  const properties = appliedRunReceiptSchema.properties as Record<string, JsonSchema>;
  return (appliedRunReceiptSchema.required ?? []).every((key) =>
    matchesSchema(record[key], properties[key] ?? {}),
  );
}
