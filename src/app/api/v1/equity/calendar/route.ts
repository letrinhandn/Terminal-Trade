import { NextRequest } from "next/server";
import { equityCalendar } from "@/lib/platform/equityResearch";
import { fail, ok } from "@/lib/platform/json";

export const maxDuration = 60;

export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get("symbol") || "AAPL";
  try {
    return ok(await equityCalendar(symbol));
  } catch (e) {
    return fail(e);
  }
}
