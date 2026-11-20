import { NextRequest } from "next/server";
import { equityProfile } from "@/lib/platform/equity";
import { fail, ok } from "@/lib/platform/json";

export const maxDuration = 60;

export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get("symbol") || "AAPL";
  try {
    return ok(await equityProfile(symbol));
  } catch (e) {
    return fail(e);
  }
}
