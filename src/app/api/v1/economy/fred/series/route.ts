import { NextRequest, NextResponse } from "next/server";
import { FRED_PRESETS, fredSeries, isFredConfigured } from "@/lib/platform/economy";
import { fail, ok } from "@/lib/platform/json";

export const maxDuration = 60;

export async function GET(req: NextRequest) {
  const list = req.nextUrl.searchParams.get("list");
  if (list === "1") {
    return NextResponse.json({
      configured: isFredConfigured(),
      presets: FRED_PRESETS,
    });
  }
  const seriesId = req.nextUrl.searchParams.get("id") || "GDP";
  const start = req.nextUrl.searchParams.get("start") || undefined;
  const end = req.nextUrl.searchParams.get("end") || undefined;
  try {
    return ok(await fredSeries(seriesId, start, end));
  } catch (e) {
    return fail(e);
  }
}
