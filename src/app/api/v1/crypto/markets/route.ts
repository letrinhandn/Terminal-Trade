import { NextRequest } from "next/server";
import { fetchCoinMarkets, isCoinGeckoConfigured } from "@/lib/data/coingecko";
import { cached } from "@/lib/platform/cache";
import { fail, ok } from "@/lib/platform/json";
import { runProvider } from "@/lib/platform/run";

export const maxDuration = 60;

/** CoinGecko top markets - overview tape for crypto. */
export async function GET(req: NextRequest) {
  const limit = Math.min(
    Math.max(Number(req.nextUrl.searchParams.get("limit") || 40), 1),
    100,
  );
  try {
    const markets = await cached(`cg:markets:${limit}`, 60_000, () =>
      fetchCoinMarkets(limit),
    );
    return ok(
      await runProvider(
        "coingecko",
        async () => ({
          markets,
          attribution: "CoinGecko",
          licenseNote: isCoinGeckoConfigured()
            ? "CoinGecko Demo key - prototype / non-commercial unless you upgrade"
            : "Keyless CoinGecko Demo - rate-limited; set COINGECKO_DEMO_API_KEY",
        }),
        [
          "CoinDesk Data API is not used here (paid subscription required since 2026-05-21)",
        ],
      ),
    );
  } catch (e) {
    return fail(e);
  }
}
