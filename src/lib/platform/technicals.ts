import { isCryptoSymbol } from "@/lib/data/crypto";
import { analyzeSymbol } from "@/lib/signals/analyze";
import { runProvider } from "@/lib/platform/run";
import type { PlatformResult } from "@/lib/platform/types";
import type { SignalsResponse } from "@/lib/types";
import { cached } from "@/lib/platform/cache";

export async function technicalSignals(
  symbol: string,
  lookback = 400,
): Promise<PlatformResult<SignalsResponse>> {
  const warnings = isCryptoSymbol(symbol)
    ? [
        "Crypto OHLCV prefers Coinbase Exchange daily candles (venue price); quotes prefer CoinGecko Demo",
      ]
    : [];
  return runProvider(
    "internal",
    () =>
      cached(`tech:sig:${symbol}:${lookback}`, 120_000, () =>
        analyzeSymbol(symbol, lookback),
      ),
    warnings,
  );
}
