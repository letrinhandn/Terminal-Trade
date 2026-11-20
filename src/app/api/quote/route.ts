import { NextRequest, NextResponse } from "next/server";
import { fetchQuote } from "@/lib/data/yahoo";


export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get("symbol") || "AAPL";
  try {
    const data = await fetchQuote(symbol);
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : String(e) }, { status: 500 });
  }
}
