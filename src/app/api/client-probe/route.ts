export async function POST(req: Request) {
  try {
    await req.json();
  } catch {
    // Probe may send malformed JSON; still acknowledge.
  }

  return Response.json({ ok: true });
}
