import { NextRequest } from "next/server";
import { equityOverviewWidgets } from "@/lib/platform/equityResearch";
import { equityQuote } from "@/lib/platform/equity";
import { getCompanyBundle, isFinnhubConfigured } from "@/lib/data/finnhub";
import { cached } from "@/lib/platform/cache";
import { fail, ok } from "@/lib/platform/json";
import { runProvider } from "@/lib/platform/run";

export const maxDuration = 60;

export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get("symbol") || "AAPL";
  try {
    const warnings: string[] = [];
    const [quote, widgets] = await Promise.all([
      equityQuote(symbol),
      equityOverviewWidgets(symbol),
    ]);
    let finnhub: unknown = null;
    if (isFinnhubConfigured()) {
      try {
        finnhub = await cached(`eq:fh:${symbol.toUpperCase()}`, 600_000, () =>
          getCompanyBundle(symbol),
        );
      } catch (e) {
        warnings.push(e instanceof Error ? e.message : String(e));
      }
    } else {
      warnings.push("FINNHUB_API_KEY not set");
    }
    return ok(
      await runProvider(
        finnhub ? "finnhub" : "yahoo",
        async () => ({
          quote: quote.data,
          widgets: widgets.data,
          finnhub,
        }),
        warnings,
      ),
    );
  } catch (e) {
    return fail(e);
  }
}
