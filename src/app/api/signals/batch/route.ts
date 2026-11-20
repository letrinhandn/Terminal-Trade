import { NextRequest, NextResponse } from "next/server";
import { analyzeSymbol } from "@/lib/signals/analyze";
import type { SignalsResponse } from "@/lib/types";

export const maxDuration = 60;

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
    ).slice(0, 12);

    if (!symbols.length) {
      return NextResponse.json({ error: "symbols required" }, { status: 400 });
    }

    const results: SignalsResponse[] = [];
    const errors: { symbol: string; error: string }[] = [];

    // Sequential to stay gentle on Yahoo
    for (const symbol of symbols) {
      try {
        results.push(await analyzeSymbol(symbol, 400));
      } catch (e) {
        errors.push({
          symbol,
          error: e instanceof Error ? e.message : String(e),
        });
      }
    }

    return NextResponse.json({ results, errors });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : String(e) },
      { status: 500 },
    );
  }
}
