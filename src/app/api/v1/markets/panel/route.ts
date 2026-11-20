import { NextRequest } from "next/server";
import { fail, ok } from "@/lib/platform/json";
import { marketsPanel } from "@/lib/platform/markets";

export const maxDuration = 60;

export async function GET(req: NextRequest) {
  const symbolsParam = req.nextUrl.searchParams.get("symbols") || "SPY,QQQ,AAPL,BTC";
  const range = req.nextUrl.searchParams.get("range") || "3mo";
  const active = req.nextUrl.searchParams.get("active") || undefined;
  const symbols = symbolsParam.split(/[,|\s]+/).filter(Boolean);
  try {
    return ok(await marketsPanel(symbols, range, active));
  } catch (e) {
    return fail(e);
  }
}
