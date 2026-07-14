import { NextRequest, NextResponse } from "next/server";
import { spiritFlixAdminMutationDenied } from "@/lib/spiritflix/admin-authority";

export const runtime = "nodejs";

export async function POST(_request: NextRequest) {
  return NextResponse.json(spiritFlixAdminMutationDenied(), { status: 410 });
}
