export async function GET() {
  const token = process.env.KINGAWEB_VERIFICATION_TOKEN;
  if (!token) return new Response("Verification proof is not configured", { status: 404 });
  return new Response(`kingaweb-verification=${token}\n`, {
    headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" },
  });
}
