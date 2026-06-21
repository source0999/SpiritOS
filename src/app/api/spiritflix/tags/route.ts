import { NextRequest, NextResponse } from "next/server";
import {
  findSpiritFlixManualTaggedItems,
  getSpiritFlixManualTagScope,
  getSpiritFlixManualTagIndex,
  listSpiritFlixManualTagRecords,
} from "@/lib/spiritflix/manual-tags";
import {
  canonicalizeSpiritFlixManualModelName,
  listSpiritFlixManualModelRecords,
} from "@/lib/spiritflix/manual-models";

export const runtime = "nodejs";

function getManualModelMatchKey(modelName: string): string {
  return canonicalizeSpiritFlixManualModelName(modelName).toLowerCase();
}

function getCompactManualModelMatchKey(modelName: string): string {
  return getManualModelMatchKey(modelName).replace(/[^a-z0-9]/g, "");
}

export async function GET(request: NextRequest) {
  const tag = request.nextUrl.searchParams.get("tag");
  const modelName = request.nextUrl.searchParams.get("modelName");
  const includeItems = request.nextUrl.searchParams.get("includeItems") === "1";

  try {
    const index = await getSpiritFlixManualTagIndex();
    if (modelName) {
      const modelKey = getManualModelMatchKey(modelName);
      const compactModelKey = getCompactManualModelMatchKey(modelName);
      const [modelRecords, tagRecords] = await Promise.all([
        listSpiritFlixManualModelRecords(),
        listSpiritFlixManualTagRecords(),
      ]);
      const modelItems = modelRecords.filter((record) => (
        getManualModelMatchKey(record.modelName) === modelKey ||
        getCompactManualModelMatchKey(record.modelName) === compactModelKey
      ));
      const modelItemIds = new Set(modelItems.map((record) => record.itemId));
      const tagsByItemId = new Map(tagRecords.map((record) => [record.itemId, record]));
      const modelTags = Array.from(
        new Set(
          modelItems.flatMap((modelItem) => tagsByItemId.get(modelItem.itemId)?.manualTags ?? [])
            .filter((manualTag) => getSpiritFlixManualTagScope(manualTag) === "model"),
        ),
      ).sort((left, right) => left.localeCompare(right));
      return NextResponse.json({
        schema: "spiritflix-model-manual-tags/v1",
        modelName: canonicalizeSpiritFlixManualModelName(modelName),
        modelTags,
        itemIds: Array.from(modelItemIds),
        items: includeItems ? modelItems.map((modelItem) => ({
          ...modelItem,
          manualTags: tagsByItemId.get(modelItem.itemId)?.manualTags ?? [],
        })) : undefined,
      }, {
        headers: { "Cache-Control": "no-store" },
      });
    }
    if (!tag) {
      return NextResponse.json({
        ...index,
        items: includeItems ? await listSpiritFlixManualTagRecords() : undefined,
      }, {
        headers: { "Cache-Control": "no-store" },
      });
    }

    const items = await findSpiritFlixManualTaggedItems(tag);
    return NextResponse.json(
      {
        schema: "spiritflix-manual-tag-query/v1",
        tag: tag.trim().replace(/\s+/g, " ").toLowerCase(),
        itemIds: items.map((item) => item.itemId),
        items,
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix manual tags failed." },
      { status: 400 },
    );
  }
}
