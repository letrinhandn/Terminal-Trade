import { fetchFundamentals, fetchOhlcv, fetchQuote } from "@/lib/data/yahoo";
import { getCompanyBundle, isFinnhubConfigured } from "@/lib/data/finnhub";
import {
  fetchCryptoOhlcv,
  fetchCryptoQuote,
  fetchCryptoQuotes,
  isCryptoSymbol,
} from "@/lib/data/crypto";
import { cached } from "@/lib/platform/cache";
import { runProvider } from "@/lib/platform/run";
import type { PlatformResult, ProviderId } from "@/lib/platform/types";
import type { OhlcvBar, QuoteSnapshot } from "@/lib/types";

export async function equityQuote(
  symbol: string,
): Promise<PlatformResult<QuoteSnapshot>> {
  if (isCryptoSymbol(symbol)) {
    const { quote, provider } = await cached(
      `eq:quote:crypto:${symbol.toUpperCase()}`,
      30_000,
      () => fetchCryptoQuote(symbol),
    );
    return runProvider(provider, async () => quote);
  }
  return runProvider("yahoo", () =>
    cached(`eq:quote:${symbol.toUpperCase()}`, 30_000, () =>
      fetchQuote(symbol),
    ),
  );
}

export async function equityQuotes(
  symbols: string[],
): Promise<
  PlatformResult<{ quotes: QuoteSnapshot[]; errors: { symbol: string; error: string }[] }>
> {
  const crypto = symbols.filter(isCryptoSymbol);
  const equity = symbols.filter((s) => !isCryptoSymbol(s));
  const quotes: QuoteSnapshot[] = [];
  const errors: { symbol: string; error: string }[] = [];
  let cryptoProvider: ProviderId = "yahoo";

  if (crypto.length) {
    const batch = await fetchCryptoQuotes(crypto);
    quotes.push(...batch.quotes);
    errors.push(...batch.errors);
    cryptoProvider = batch.provider === "coingecko" ? "coingecko" : "yahoo";
  }

  for (const s of equity) {
    try {
      quotes.push(
        await cached(`eq:quote:${s}`, 30_000, () => fetchQuote(s)),
      );
    } catch (e) {
      errors.push({
        symbol: s,
        error: e instanceof Error ? e.message : String(e),
      });
    }
  }

  const warnings: string[] = [];
  if (crypto.length && equity.length) {
    warnings.push(
      `Mixed tape: crypto via ${cryptoProvider === "coingecko" ? "CoinGecko" : "Yahoo"}; equities via Yahoo`,
    );
  } else if (crypto.length && cryptoProvider === "coingecko") {
    warnings.push(
      "Crypto quotes: CoinGecko (Demo - not for commercial redistribution)",
    );
  }

  return runProvider(
    crypto.length && !equity.length ? cryptoProvider : "yahoo",
    async () => ({ quotes, errors }),
    warnings,
  );
}

export async function equityHistorical(
  symbol: string,
  start: string,
  end?: string,
): Promise<PlatformResult<{ symbol: string; bars: OhlcvBar[]; sourceNote?: string }>> {
  if (isCryptoSymbol(symbol)) {
    const { bars, provider } = await cached(
      `eq:ohlcv:crypto:${symbol}:${start}:${end || ""}`,
      300_000,
      () => fetchCryptoOhlcv(symbol, start, end),
    );
    return runProvider(provider, async () => ({
      symbol: symbol.toUpperCase().replace(/-USD$/, ""),
      bars,
      sourceNote:
        provider === "coinbase"
          ? "OHLCV from Coinbase Exchange (venue price, not global aggregate)"
          : "OHLCV from Yahoo Finance",
    }));
  }
  return runProvider("yahoo", async () => {
    const bars = await cached(
      `eq:ohlcv:${symbol}:${start}:${end || ""}`,
      300_000,
      () => fetchOhlcv(symbol, start, end),
    );
    return { symbol: symbol.toUpperCase(), bars };
  });
}

export async function equityProfile(symbol: string): Promise<
  PlatformResult<{
    fundamentals: Awaited<ReturnType<typeof fetchFundamentals>>;
    finnhub: Awaited<ReturnType<typeof getCompanyBundle>> | null;
  }>
> {
  const warnings: string[] = [];
  const fundamentals = await cached(`eq:fund:${symbol}`, 600_000, () =>
    fetchFundamentals(symbol),
  );
  let finnhub = null;
  if (isFinnhubConfigured()) {
    try {
      finnhub = await cached(`eq:fh:${symbol}`, 600_000, () =>
        getCompanyBundle(symbol),
      );
    } catch (e) {
      warnings.push(
        `Finnhub: ${e instanceof Error ? e.message : String(e)}`,
      );
    }
  } else {
    warnings.push("FINNHUB_API_KEY not set - profile limited to Yahoo");
  }
  return runProvider(
    finnhub ? "finnhub" : "yahoo",
    async () => ({ fundamentals, finnhub }),
    warnings,
  );
}
