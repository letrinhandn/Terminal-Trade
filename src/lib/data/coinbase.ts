import type { OhlcvBar } from "@/lib/types";
import {
  COINBASE_PRODUCTS,
  baseCryptoSymbol,
} from "@/lib/data/cryptoIds";

/**
 * Coinbase Exchange public candles (no API key).
 * Prices are **exchange-specific** (Coinbase), not a global aggregate index.
 * Docs: https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductcandles
 */
const BASE = "https://api.exchange.coinbase.com";

export function coinbaseProduct(symbol: string): string | null {
  return COINBASE_PRODUCTS[baseCryptoSymbol(symbol)] ?? null;
}

export async function fetchCoinbaseOhlcv(
  symbol: string,
  start: string,
  end?: string,
): Promise<OhlcvBar[]> {
  const product = coinbaseProduct(symbol);
  if (!product) {
    throw new Error(`No Coinbase USD product for ${symbol}`);
  }

  const startDate = new Date(`${start}T00:00:00Z`);
  const endDate = end
    ? new Date(`${end}T23:59:59Z`)
    : new Date();
  if (startDate >= endDate) {
    throw new Error("Start date must be before end date");
  }

  // Coinbase caps ~300 candles per request; chunk by ~250 days at 1d
  const granularity = 86400;
  const maxSpanSec = 250 * granularity;
  const bars: OhlcvBar[] = [];
  let cursor = startDate.getTime();
  const endMs = endDate.getTime();

  while (cursor < endMs) {
    const chunkEnd = Math.min(cursor + maxSpanSec * 1000, endMs);
    const url = new URL(`${BASE}/products/${product}/candles`);
    url.searchParams.set("granularity", String(granularity));
    url.searchParams.set("start", new Date(cursor).toISOString());
    url.searchParams.set("end", new Date(chunkEnd).toISOString());

    const res = await fetch(url.toString(), {
      headers: { Accept: "application/json" },
      next: { revalidate: 300 },
    });
    if (!res.ok) {
      throw new Error(`Coinbase ${res.status}: ${await res.text()}`);
    }
    // [ time, low, high, open, close, volume ]
    const raw = (await res.json()) as number[][];
    for (const row of raw) {
      if (!Array.isArray(row) || row.length < 6) continue;
      const [time, low, high, open, close, volume] = row;
      bars.push({
        date: new Date(time * 1000).toISOString().slice(0, 10),
        open: Number(open),
        high: Number(high),
        low: Number(low),
        close: Number(close),
        volume: Number(volume),
      });
    }
    cursor = chunkEnd + 1000;
  }

  const byDate = new Map<string, OhlcvBar>();
  for (const b of bars) {
    if (Number.isFinite(b.close)) byDate.set(b.date, b);
  }
  const out = Array.from(byDate.values()).sort((a, b) =>
    a.date.localeCompare(b.date),
  );
  if (!out.length) {
    throw new Error(`No Coinbase candles for ${product}`);
  }
  return out;
}
