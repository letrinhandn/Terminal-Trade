import { NextRequest } from "next/server";
import { equityQuote, equityQuotes } from "@/lib/platform/equity";
import { fail, ok } from "@/lib/platform/json";

export const maxDuration = 60;

export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get("symbol") || "AAPL";
  try {
    return ok(await equityQuote(symbol));
  } catch (e) {
    return fail(e);
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const raw = Array.isArray(body.symbols) ? body.symbols : [];
    const symbols = Array.from(
      new Set<string>(
        raw
          .map((s: unknown) => String(s || "").trim().toUpperCase())
          .filter((s: string): s is string => Boolean(s)),
      ),
    ).slice(0, 40);
    return ok(await equityQuotes(symbols));
  } catch (e) {
    return fail(e);
  }
}
