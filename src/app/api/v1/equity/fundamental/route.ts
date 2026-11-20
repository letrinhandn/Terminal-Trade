import { NextRequest } from "next/server";
import { equityFundamentals } from "@/lib/platform/equityResearch";
import { fail, ok } from "@/lib/platform/json";

export const maxDuration = 60;

export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get("symbol") || "AAPL";
  const period =
    req.nextUrl.searchParams.get("period") === "quarterly"
      ? "quarterly"
      : "annual";
  try {
    return ok(await equityFundamentals(symbol, period));
  } catch (e) {
    return fail(e);
  }
}
