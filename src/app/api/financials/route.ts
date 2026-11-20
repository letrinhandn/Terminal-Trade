import { NextRequest, NextResponse } from "next/server";
import { getFinancials, isFinnhubConfigured } from "@/lib/data/finnhub";

export const maxDuration = 60;

export async function GET(req: NextRequest) {
  if (!isFinnhubConfigured()) {
    return NextResponse.json(
      { error: "FINNHUB_API_KEY not configured", configured: false },
      { status: 503 },
    );
  }
  const symbol = req.nextUrl.searchParams.get("symbol") || "AAPL";
  const freq = (req.nextUrl.searchParams.get("freq") || "annual") as
    | "annual"
    | "quarterly";
  try {
    const data = await getFinancials(symbol, freq);
    return NextResponse.json({ configured: true, data });
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : String(e) }, { status: 500 });
  }
}
