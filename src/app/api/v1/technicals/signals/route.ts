import { NextRequest } from "next/server";
import { technicalSignals } from "@/lib/platform/technicals";
import { fail, ok } from "@/lib/platform/json";

export const maxDuration = 60;

export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get("symbol") || "AAPL";
  const lookback = Number(req.nextUrl.searchParams.get("lookback") || 400);
  try {
    return ok(
      await technicalSignals(
        symbol,
        Number.isFinite(lookback)
          ? Math.min(Math.max(lookback, 120), 800)
          : 400,
      ),
    );
  } catch (e) {
    return fail(e);
  }
}
