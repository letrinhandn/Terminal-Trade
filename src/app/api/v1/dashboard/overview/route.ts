import { NextRequest } from "next/server";
import { fetchDashboardBundle } from "@/lib/data/dashboard";
import { cached } from "@/lib/platform/cache";
import { fail, ok } from "@/lib/platform/json";
import { runProvider } from "@/lib/platform/run";

export const maxDuration = 60;

export async function GET(req: NextRequest) {
  const focus = req.nextUrl.searchParams.get("symbol") || "AAPL";
  try {
    return ok(
      await runProvider(
        "yahoo",
        () =>
          cached(`dash:overview:${focus.toUpperCase()}`, 60_000, () =>
            fetchDashboardBundle(focus),
          ),
        [
          "Dashboard mosaic: Yahoo quotes/screener, alternative.me Fear and Greed, RSS news",
        ],
      ),
    );
  } catch (e) {
    return fail(e);
  }
}
