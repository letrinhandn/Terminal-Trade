import { NextRequest, NextResponse } from "next/server";
import {
  fetchCryptoOhlcv,
  isCryptoSymbol,
} from "@/lib/data/crypto";
import { fetchOhlcv } from "@/lib/data/yahoo";

export const maxDuration = 60;

const RANGE_DAYS: Record<string, number> = {
  "5d": 5,
  "1mo": 31,
  "3mo": 93,
  "6mo": 186,
  "1y": 365,
  "2y": 730,
  "5y": 1825,
  "10y": 3650,
  max: 3650 * 5,
};

function startFromRange(range: string): string {
  const days = RANGE_DAYS[range.toLowerCase()] ?? RANGE_DAYS["1y"];
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - days);
  return d.toISOString().slice(0, 10);
}

export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get("symbol") || "AAPL";
  const range = req.nextUrl.searchParams.get("range");
  const startParam = req.nextUrl.searchParams.get("start");
  const end = req.nextUrl.searchParams.get("end") || undefined;
  const start =
    startParam || (range ? startFromRange(range) : "2023-01-01");
  try {
    if (isCryptoSymbol(symbol)) {
      const { bars, provider } = await fetchCryptoOhlcv(symbol, start, end);
      return NextResponse.json({
        symbol: symbol.toUpperCase().replace(/-USD$/, ""),
        bars,
        start,
        end: end ?? null,
        provider,
        sourceNote:
          provider === "coinbase"
            ? "Coinbase Exchange daily candles (venue price, not global aggregate)"
            : "Yahoo Finance",
      });
    }
    const data = await fetchOhlcv(symbol, start, end);
    return NextResponse.json({
      symbol: symbol.toUpperCase(),
      bars: data,
      start,
      end: end ?? null,
      provider: "yahoo",
    });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : String(e) },
      { status: 500 },
    );
  }
}
