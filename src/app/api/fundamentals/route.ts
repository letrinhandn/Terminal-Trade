import { NextRequest, NextResponse } from "next/server";
import { fetchFundamentals } from "@/lib/data/yahoo";


export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get("symbol") || "AAPL";
  try {
    const data = await fetchFundamentals(symbol);
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : String(e) }, { status: 500 });
  }
}
