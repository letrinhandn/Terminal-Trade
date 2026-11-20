import type { QuoteSnapshot } from "@/lib/types";
import {
  COINGECKO_IDS,
  baseCryptoSymbol,
} from "@/lib/data/cryptoIds";

const BASE = "https://api.coingecko.com/api/v3";

function demoKey(): string {
  return process.env.COINGECKO_DEMO_API_KEY || process.env.COINGECKO_API_KEY || "";
}

export function isCoinGeckoConfigured(): boolean {
  return Boolean(demoKey());
}

async function cgGet<T>(path: string, params: Record<string, string> = {}): Promise<T> {
  const url = new URL(`${BASE}${path}`);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const key = demoKey();
  const headers: Record<string, string> = { Accept: "application/json" };
  if (key) {
    headers["x-cg-demo-api-key"] = key;
    url.searchParams.set("x_cg_demo_api_key", key);
  }
  const res = await fetch(url.toString(), {
    headers,
    next: { revalidate: 60 },
  });
  if (!res.ok) {
    throw new Error(`CoinGecko ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

type MarketRow = {
  id: string;
  symbol: string;
  name: string;
  current_price: number | null;
  market_cap: number | null;
  total_volume: number | null;
  high_24h: number | null;
  low_24h: number | null;
  price_change_24h: number | null;
  price_change_percentage_24h: number | null;
};

/** Top coins by market cap (overview / Markets crypto tape). */
export async function fetchCoinMarkets(limit = 50): Promise<MarketRow[]> {
  return cgGet<MarketRow[]>("/coins/markets", {
    vs_currency: "usd",
    order: "market_cap_desc",
    per_page: String(Math.min(Math.max(limit, 1), 100)),
    page: "1",
    sparkline: "false",
    price_change_percentage: "24h",
  });
}

export async function fetchCoinGeckoQuote(symbol: string): Promise<QuoteSnapshot> {
  const base = baseCryptoSymbol(symbol);
  const id = COINGECKO_IDS[base];
  if (!id) throw new Error(`No CoinGecko id for ${base}`);

  const rows = await cgGet<MarketRow[]>("/coins/markets", {
    vs_currency: "usd",
    ids: id,
    sparkline: "false",
    price_change_percentage: "24h",
  });
  const row = rows[0];
  if (!row || row.current_price == null) {
    throw new Error(`No CoinGecko market data for ${base}`);
  }
  const price = Number(row.current_price);
  const change = Number(row.price_change_24h ?? 0);
  const changePct = Number(row.price_change_percentage_24h ?? 0);
  return {
    symbol: base,
    name: row.name,
    price,
    change,
    changePct,
    open: price - change,
    previousClose: price - change,
    high: Number(row.high_24h ?? price),
    low: Number(row.low_24h ?? price),
    volume: Number(row.total_volume ?? 0),
    marketCap: row.market_cap != null ? Number(row.market_cap) : undefined,
  };
}

export async function fetchCoinGeckoQuotes(
  symbols: string[],
): Promise<QuoteSnapshot[]> {
  const ids = symbols
    .map((s) => COINGECKO_IDS[baseCryptoSymbol(s)])
    .filter(Boolean) as string[];
  if (!ids.length) return [];
  const rows = await cgGet<MarketRow[]>("/coins/markets", {
    vs_currency: "usd",
    ids: ids.join(","),
    sparkline: "false",
    price_change_percentage: "24h",
  });
  return rows
    .filter((r) => r.current_price != null)
    .map((row) => {
      const price = Number(row.current_price);
      const change = Number(row.price_change_24h ?? 0);
      const changePct = Number(row.price_change_percentage_24h ?? 0);
      const base = row.symbol.toUpperCase();
      return {
        symbol: base,
        name: row.name,
        price,
        change,
        changePct,
        open: price - change,
        previousClose: price - change,
        high: Number(row.high_24h ?? price),
        low: Number(row.low_24h ?? price),
        volume: Number(row.total_volume ?? 0),
        marketCap: row.market_cap != null ? Number(row.market_cap) : undefined,
      } satisfies QuoteSnapshot;
    });
}
