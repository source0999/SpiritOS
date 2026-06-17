import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(_request: NextRequest) {
  void _request;
  // Passthrough for now - auth, rate limiting, homelab headers go here later
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/api/spirit",
    "/api/spirit/:path*",
    "/api/oracle",
    "/api/oracle/:path*",
    "/api/admin",
    "/api/admin/:path*",
    "/studio",
    "/studio/:path*",
  ],
};
