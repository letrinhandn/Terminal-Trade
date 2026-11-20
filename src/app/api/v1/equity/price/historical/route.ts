import { NextRequest } from "next/server";
import { equityHistorical } from "@/lib/platform/equity";
import { fail, ok } from "@/lib/platform/json";

export const maxDuration = 60;

function daysAgo(n: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - n);
  return d.toISOString().slice(0, 10);
}

export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get("symbol") || "AAPL";
  const start = req.nextUrl.searchParams.get("start") || daysAgo(365);
  const end = req.nextUrl.searchParams.get("end") || undefined;
  try {
    return ok(await equityHistorical(symbol, start, end));
  } catch (e) {
    return fail(e);
  }
}
