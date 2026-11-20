import { NextRequest, NextResponse } from "next/server";
import { analyzeSymbol } from "@/lib/signals/analyze";

export const maxDuration = 60;

export async function GET(req: NextRequest) {
  const symbol = (req.nextUrl.searchParams.get("symbol") || "AAPL").toUpperCase();
  const lookback = Number(req.nextUrl.searchParams.get("lookback") || 400);
  try {
    const data = await analyzeSymbol(
      symbol,
      Number.isFinite(lookback) ? Math.min(Math.max(lookback, 120), 800) : 400,
    );
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : String(e) },
      { status: 500 },
    );
  }
}
