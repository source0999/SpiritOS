import { runDesignStudioApprovedWriteback } from "@/lib/coding/design-studio-approved-writeback-runtime";

export async function POST(request: Request) {
  const input = await request.json();
  const result = await runDesignStudioApprovedWriteback(input);

  return Response.json(
    {
      endpoint: "/v1/coding/design-studio/approved-writeback",
      preview_write_authority: false,
      result,
      write_authority: result.status === "written",
    },
    { status: result.status === "written" ? 200 : 403 },
  );
}
