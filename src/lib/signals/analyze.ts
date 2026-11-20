import {
  fetchCryptoOhlcv,
  fetchCryptoQuote,
  isCryptoSymbol,
} from "@/lib/data/crypto";
import { fetchOhlcv, fetchQuote } from "@/lib/data/yahoo";
import {
  changePctLookback,
  detectSignals,
  scoreFromSignals,
} from "@/lib/signals/engine";
import type { SignalsResponse } from "@/lib/types";

function lookbackStart(days: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - days);
  return d.toISOString().slice(0, 10);
}

export async function analyzeSymbol(
  symbol: string,
  lookbackDays = 400,
): Promise<SignalsResponse> {
  const start = lookbackStart(lookbackDays);
  let bars;
  let price: number;

  if (isCryptoSymbol(symbol)) {
    const [ohlcv, q] = await Promise.all([
      fetchCryptoOhlcv(symbol, start),
      fetchCryptoQuote(symbol).catch(() => null),
    ]);
    bars = ohlcv.bars;
    price = q?.quote.price ?? bars[bars.length - 1]?.close ?? 0;
  } else {
    const [b, quote] = await Promise.all([
      fetchOhlcv(symbol, start),
      fetchQuote(symbol).catch(() => null),
    ]);
    bars = b;
    price = quote?.price ?? bars[bars.length - 1]?.close ?? 0;
  }

  if (!bars.length) {
    throw new Error(`No OHLCV for ${symbol}`);
  }

  const signals = detectSignals(bars);
  const last = bars[bars.length - 1];
  return {
    symbol: symbol.toUpperCase().replace(/-USD$/, ""),
    asOf: last.date,
    price,
    changePct1m: changePctLookback(bars, 21),
    signals,
    score: scoreFromSignals(signals),
  };
}
