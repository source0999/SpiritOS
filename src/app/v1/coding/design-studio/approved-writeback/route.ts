import { runDesignStudioApprovedWriteback } from "@/lib/coding/design-studio-approved-writeback-runtime";

export const runtime = "nodejs";

export async function POST(request: Request) {
  let input: unknown;
  try {
    input = await request.json();
  } catch {
    return Response.json(
      {
        endpoint: "/v1/coding/design-studio/approved-writeback",
        preview_write_authority: false,
        result: {
          reasons: ["design_writeback_request_invalid"],
          status: "rejected",
          write_invoked: false,
        },
        write_authority: false,
      },
      { headers: { "Cache-Control": "no-store" }, status: 400 },
    );
  }
  const result = await runDesignStudioApprovedWriteback(input as never);

  return Response.json(
    {
      endpoint: "/v1/coding/design-studio/approved-writeback",
      preview_write_authority: false,
      result,
      write_authority: result.status === "written",
    },
    {
      headers: { "Cache-Control": "no-store" },
      status: result.status === "written" ? 200 : 403,
    },
  );
}
