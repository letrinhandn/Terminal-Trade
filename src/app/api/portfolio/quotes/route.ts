import { NextRequest, NextResponse } from "next/server";
import { fetchQuote } from "@/lib/data/yahoo";
import type { QuoteSnapshot } from "@/lib/types";

export const maxDuration = 60;

/** Batch quotes for paper portfolio mark-to-market. */
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

    const quotes: QuoteSnapshot[] = [];
    const errors: { symbol: string; error: string }[] = [];

    for (const symbol of symbols) {
      try {
        quotes.push(await fetchQuote(symbol));
      } catch (e) {
        errors.push({
          symbol,
          error: e instanceof Error ? e.message : String(e),
        });
      }
    }

    return NextResponse.json({ quotes, errors });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : String(e) },
      { status: 500 },
    );
  }
}
