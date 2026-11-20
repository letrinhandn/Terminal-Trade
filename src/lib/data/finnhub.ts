const BASE = "https://finnhub.io/api/v1";

function key(): string {
  return process.env.FINNHUB_API_KEY || "";
}

async function get<T>(
  path: string,
  params: Record<string, string> = {},
): Promise<T> {
  const apiKey = key();
  if (!apiKey) {
    throw new Error("FINNHUB_API_KEY not configured");
  }
  const url = new URL(`${BASE}${path}`);
  Object.entries({ ...params, token: apiKey }).forEach(([k, v]) =>
    url.searchParams.set(k, v),
  );
  const res = await fetch(url.toString(), { next: { revalidate: 300 } });
  if (!res.ok) throw new Error(`Finnhub ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

async function getOptional<T>(
  path: string,
  params: Record<string, string> = {},
): Promise<T | null> {
  try {
    return await get<T>(path, params);
  } catch {
    return null;
  }
}

export function isFinnhubConfigured(): boolean {
  return Boolean(key());
}

/**
 * Free-tier-friendly company pack.
 * Premium endpoints (price-target, insider, full financials-reported, etc.)
 * are fetched optionally and omitted on 403.
 */
export async function getCompanyBundle(symbol: string) {
  const s = symbol.toUpperCase();
  const [
    profile,
    quote,
    metrics,
    recommendations,
    priceTargets,
    upgrades,
    earnings,
    insider,
    peers,
  ] = await Promise.all([
    getOptional("/stock/profile2", { symbol: s }),
    getOptional("/quote", { symbol: s }),
    getOptional("/stock/metric", { symbol: s, metric: "all" }),
    getOptional("/stock/recommendation", { symbol: s }),
    getOptional("/stock/price-target", { symbol: s }),
    getOptional("/stock/upgrade-downgrade", { symbol: s }),
    getOptional("/stock/earnings", { symbol: s }),
    getOptional("/stock/insider-transactions", { symbol: s }),
    getOptional<string[]>("/stock/peers", { symbol: s }),
  ]);

  if (!profile && !quote && !metrics && !peers) {
    throw new Error(
      "Finnhub returned no data - check API key / plan entitlements",
    );
  }

  return {
    profile,
    quote,
    metrics,
    recommendations,
    price_targets: priceTargets,
    upgrades,
    earnings,
    insider,
    peers: peers || [],
  };
}

export async function getFinancials(
  symbol: string,
  freq: "annual" | "quarterly" = "annual",
) {
  return get("/stock/financials-reported", {
    symbol: symbol.toUpperCase(),
    freq: freq === "annual" ? "annual" : "quarterly",
  });
}
