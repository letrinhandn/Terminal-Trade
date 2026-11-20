import { NextRequest, NextResponse } from "next/server";
import { unstable_cache } from "next/cache";
import { fetchLiveChain } from "@/lib/market/deribit";
import { fetchYahooOptionsChain } from "@/lib/market/yahooOptions";

export const maxDuration = 60;

function isCryptoOpt(s: string): "BTC" | "ETH" | null {
  const u = s.trim().toUpperCase();
  if (u === "BTC" || u === "BTC-USD" || u.startsWith("BTC")) return "BTC";
  if (u === "ETH" || u === "ETH-USD" || u.startsWith("ETH")) return "ETH";
  return null;
}

const getCachedDeribit = unstable_cache(
  async (currency: "BTC" | "ETH") => {
    const contracts = await fetchLiveChain(currency, { enrichGreeks: true });
    const und =
      contracts.find((c) => c.underlyingPrice != null)?.underlyingPrice ?? null;
    return {
      currency,
      underlying: currency,
      underlyingPrice: und,
      mode: "live" as const,
      source: "deribit" as const,
      unit: "coin" as const,
      note: "Mark/bid/ask in coin. IV from Deribit mark_iv. Greeks on near-ATM front expiries via ticker.",
      timestamp: new Date().toISOString(),
      contracts,
    };
  },
  ["options-chain-deribit-v2"],
  { revalidate: 120 },
);

const getCachedYahoo = unstable_cache(
  async (symbol: string, dateKey: string) => {
    const date = dateKey ? new Date(dateKey) : undefined;
    const data = await fetchYahooOptionsChain(symbol, date);
    return {
      currency: null as string | null,
      underlying: data.symbol,
      underlyingPrice: data.underlyingPrice,
      expirations: data.expirations,
      mode: "live" as const,
      source: "yahoo" as const,
      unit: "usd" as const,
      note: "Equity options via Yahoo. Last as mark. No greeks. Stale IV filtered out.",
      timestamp: new Date().toISOString(),
      contracts: data.contracts,
    };
  },
  ["options-chain-yahoo-v1"],
  { revalidate: 120 },
);

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const force = sp.get("force") === "1";
  const dateParam = sp.get("date") || "";
  const raw =
    sp.get("symbol") ||
    sp.get("underlying") ||
    sp.get("currency") ||
    "BTC";
  const crypto = isCryptoOpt(raw);

  try {
    if (crypto) {
      if (force) {
        const contracts = await fetchLiveChain(crypto, { enrichGreeks: true });
        const und =
          contracts.find((c) => c.underlyingPrice != null)?.underlyingPrice ??
          null;
        return NextResponse.json({
          currency: crypto,
          underlying: crypto,
          underlyingPrice: und,
          mode: "live",
          source: "deribit",
          unit: "coin",
          fromCache: false,
          note: "Mark/bid/ask in coin. IV from Deribit mark_iv. Greeks on near-ATM front expiries via ticker.",
          timestamp: new Date().toISOString(),
          contracts,
        });
      }
      const data = await getCachedDeribit(crypto);
      return NextResponse.json({ ...data, fromCache: true });
    }

    const symbol = raw.trim().toUpperCase();
    if (force) {
      const data = await fetchYahooOptionsChain(
        symbol,
        dateParam ? new Date(dateParam) : undefined,
      );
      return NextResponse.json({
        currency: null,
        underlying: data.symbol,
        underlyingPrice: data.underlyingPrice,
        expirations: data.expirations,
        mode: "live",
        source: "yahoo",
        unit: "usd",
        fromCache: false,
        note: "Equity options via Yahoo. Last as mark. No greeks. Stale IV filtered out.",
        timestamp: new Date().toISOString(),
        contracts: data.contracts,
      });
    }
    const data = await getCachedYahoo(symbol, dateParam);
    return NextResponse.json({ ...data, fromCache: true });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : String(e) },
      { status: 500 },
    );
  }
}
