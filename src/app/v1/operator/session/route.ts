import { NextRequest, NextResponse } from "next/server";
import { createOperatorSession, operatorCookieName, readOperatorSessionStatus, requireOperatorSession, revokeOperatorSession } from "@/lib/coding/operator-approval-session";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  return NextResponse.json(await readOperatorSessionStatus(request), { headers: { "Cache-Control": "no-store" } });
}

export async function POST(request: NextRequest) {
  let credential = "";
  try {
    const body = await request.json() as { credential?: unknown };
    credential = typeof body.credential === "string" ? body.credential : "";
  } catch {
    return NextResponse.json({ reason_code: "operator_request_invalid" }, { status: 400, headers: { "Cache-Control": "no-store" } });
  }
  try {
    const session = await createOperatorSession(request, credential);
    const response = NextResponse.json({ operator: session.operator, role: session.role, csrf: session.csrf, expires_at: session.expires_at }, { headers: { "Cache-Control": "no-store" } });
    response.cookies.set(operatorCookieName(), session.id, { httpOnly: true, sameSite: "strict", secure: new URL(request.url).protocol === "https:", maxAge: session.max_age_seconds, path: "/v1" });
    return response;
  } catch (error) {
    return NextResponse.json({ reason_code: error instanceof Error ? error.message : "operator_session_failed" }, { status: 403, headers: { "Cache-Control": "no-store" } });
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const session = await requireOperatorSession(request);
    await revokeOperatorSession(session);
    const response = NextResponse.json({ status: "revoked" }, { headers: { "Cache-Control": "no-store" } });
    response.cookies.set(operatorCookieName(), "", { httpOnly: true, maxAge: 0, path: "/v1", sameSite: "strict", secure: new URL(request.url).protocol === "https:" });
    return response;
  } catch (error) {
    return NextResponse.json({ reason_code: error instanceof Error ? error.message : "operator_session_revoke_failed" }, { status: 403, headers: { "Cache-Control": "no-store" } });
  }
}
