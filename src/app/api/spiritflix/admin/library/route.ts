import { NextRequest, NextResponse } from "next/server";
import { listJellyfinAdminItems } from "@/lib/spiritflix/admin/jellyfin-admin";
import type { SpiritFlixAdminLibraryRequest } from "@/lib/spiritflix/admin/types";
import { resolveRequestMediaSession, trustedSpiritFlixMutation } from "@/lib/spiritflix/server-session";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  if (!trustedSpiritFlixMutation(request)) return NextResponse.json({ reason_code: "spiritflix_origin_untrusted" }, { status: 403 });
  const session = resolveRequestMediaSession(request.cookies);
  if (!session) return NextResponse.json({ reason_code: "spiritflix_session_missing" }, { status: 401 });

  let payload: Omit<SpiritFlixAdminLibraryRequest, "accessToken" | "serverUrl" | "userId">;

  try {
    payload = (await request.json()) as Omit<SpiritFlixAdminLibraryRequest, "accessToken" | "serverUrl" | "userId">;
  } catch {
    return NextResponse.json({ error: "Invalid SpiritFlix admin library request." }, { status: 400 });
  }

  if (Object.prototype.hasOwnProperty.call(payload, "accessToken") || Object.prototype.hasOwnProperty.call(payload, "serverUrl") || Object.prototype.hasOwnProperty.call(payload, "userId")) {
    return NextResponse.json({ reason_code: "spiritflix_client_authority_forbidden" }, { status: 400 });
  }

  try {
    const response = await listJellyfinAdminItems({ ...payload, accessToken: session.authorization, serverUrl: session.serverUrl, userId: session.userId });
    return NextResponse.json(response, {
      headers: {
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix admin library listing failed." },
      { status: 400 },
    );
  }
}
