import type { OhlcvBar, QuoteSnapshot } from "@/lib/types";
import { isCryptoSymbol } from "@/lib/data/cryptoIds";
import {
  fetchCoinGeckoQuote,
  fetchCoinGeckoQuotes,
} from "@/lib/data/coingecko";
import { coinbaseProduct, fetchCoinbaseOhlcv } from "@/lib/data/coinbase";
import { fetchOhlcv, fetchQuote } from "@/lib/data/yahoo";

export { isCryptoSymbol };

/**
 * Quote router for crypto:
 * 1) CoinGecko (market aggregate) when Demo key present or public Demo works
 * 2) Yahoo fallback
 */
export async function fetchCryptoQuote(symbol: string): Promise<{
  quote: QuoteSnapshot;
  provider: "coingecko" | "yahoo";
}> {
  if (!isCryptoSymbol(symbol)) {
    throw new Error(`${symbol} is not a known crypto major`);
  }
  try {
    const quote = await fetchCoinGeckoQuote(symbol);
    return { quote, provider: "coingecko" };
  } catch {
    // Demo key optional - keyless Demo may work; otherwise Yahoo fallback
    const quote = await fetchQuote(symbol);
    return { quote, provider: "yahoo" };
  }
}

export async function fetchCryptoQuotes(symbols: string[]): Promise<{
  quotes: QuoteSnapshot[];
  provider: "coingecko" | "yahoo" | "mixed";
  errors: { symbol: string; error: string }[];
}> {
  const crypto = symbols.filter(isCryptoSymbol);
  const errors: { symbol: string; error: string }[] = [];
  try {
    const quotes = await fetchCoinGeckoQuotes(crypto);
    const got = new Set(quotes.map((q) => q.symbol));
    for (const s of crypto) {
      const base = s.toUpperCase().replace(/-USD$/, "");
      if (!got.has(base)) {
        try {
          quotes.push((await fetchCryptoQuote(base)).quote);
        } catch (e) {
          errors.push({
            symbol: base,
            error: e instanceof Error ? e.message : String(e),
          });
        }
      }
    }
    return { quotes, provider: "coingecko", errors };
  } catch {
    const quotes: QuoteSnapshot[] = [];
    for (const s of crypto) {
      try {
        quotes.push(await fetchQuote(s));
      } catch (e) {
        errors.push({
          symbol: s,
          error: e instanceof Error ? e.message : String(e),
        });
      }
    }
    return { quotes, provider: "yahoo", errors };
  }
}

/**
 * OHLCV for crypto Signals/charts:
 * prefer Coinbase Exchange public candles (disclose source),
 * else Yahoo.
 */
export async function fetchCryptoOhlcv(
  symbol: string,
  start: string,
  end?: string,
): Promise<{ bars: OhlcvBar[]; provider: "coinbase" | "yahoo" }> {
  if (coinbaseProduct(symbol)) {
    try {
      const bars = await fetchCoinbaseOhlcv(symbol, start, end);
      return { bars, provider: "coinbase" };
    } catch {
      /* fall through */
    }
  }
  const bars = await fetchOhlcv(symbol, start, end);
  return { bars, provider: "yahoo" };
}
