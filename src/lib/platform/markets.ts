import {
  fetchCryptoOhlcv,
  isCryptoSymbol,
} from "@/lib/data/crypto";
import { fetchOhlcv } from "@/lib/data/yahoo";
import { cached } from "@/lib/platform/cache";
import { runProvider } from "@/lib/platform/run";
import type { PlatformResult } from "@/lib/platform/types";
import type { OhlcvBar } from "@/lib/types";

const RANGE_DAYS: Record<string, number> = {
  "1mo": 31,
  "3mo": 93,
  "1y": 365,
  "5y": 1825,
};

function startFromRange(range: string): string {
  const r = range.toLowerCase();
  const mapped =
    RANGE_DAYS[r] ??
    ({ "1m": 31, "3m": 93, "6m": 186, "1y": 365, "5y": 1825 } as Record<
      string,
      number
    >)[r] ??
    93;
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - mapped);
  return d.toISOString().slice(0, 10);
}

async function loadBars(symbol: string, start: string): Promise<{
  bars: OhlcvBar[];
  provider: string;
  sourceNote?: string;
}> {
  if (isCryptoSymbol(symbol)) {
    const { bars, provider } = await fetchCryptoOhlcv(symbol, start);
    return {
      bars,
      provider,
      sourceNote:
        provider === "coinbase"
          ? "Coinbase Exchange (venue)"
          : "Yahoo Finance",
    };
  }
  const bars = await fetchOhlcv(symbol, start);
  return { bars, provider: "yahoo" };
}

function dailyReturns(closes: number[]): number[] {
  const out: number[] = [];
  for (let i = 1; i < closes.length; i++) {
    const prev = closes[i - 1];
    out.push(prev ? (closes[i] - prev) / prev : 0);
  }
  return out;
}

function pearson(a: number[], b: number[]): number {
  const n = Math.min(a.length, b.length);
  if (n < 3) return 0;
  const aa = a.slice(a.length - n);
  const bb = b.slice(b.length - n);
  const ma = aa.reduce((s, x) => s + x, 0) / n;
  const mb = bb.reduce((s, x) => s + x, 0) / n;
  let num = 0;
  let da = 0;
  let db = 0;
  for (let i = 0; i < n; i++) {
    const xa = aa[i] - ma;
    const xb = bb[i] - mb;
    num += xa * xb;
    da += xa * xa;
    db += xb * xb;
  }
  const den = Math.sqrt(da * db);
  return den ? num / den : 0;
}

function normalizeTo100(
  bars: OhlcvBar[],
): { date: string; value: number }[] {
  if (!bars.length) return [];
  const base = bars[0].close || 1;
  return bars.map((b) => ({
    date: b.date,
    value: (b.close / base) * 100,
  }));
}

export type MarketsPanel = {
  ohlcvBySymbol: Record<string, OhlcvBar[]>;
  sparklineBySymbol: Record<string, { date: string; value: number }[]>;
  relative: { id: string; label: string; points: { date: string; value: number }[] }[];
  corr: { labels: string[]; matrix: number[][] };
  sourceNotes: Record<string, string>;
  providers: Record<string, string>;
};

export async function marketsPanel(
  symbols: string[],
  range = "3mo",
  active?: string,
): Promise<PlatformResult<MarketsPanel>> {
  const start = startFromRange(range);
  const uniq = Array.from(
    new Set(
      symbols
        .map((s) => s.trim().toUpperCase().replace(/-USD$/, ""))
        .filter(Boolean),
    ),
  ).slice(0, 16);

  const ohlcvBySymbol: Record<string, OhlcvBar[]> = {};
  const sparklineBySymbol: Record<string, { date: string; value: number }[]> =
    {};
  const sourceNotes: Record<string, string> = {};
  const providers: Record<string, string> = {};
  const warnings: string[] = [];

  await Promise.all(
    uniq.map(async (sym) => {
      try {
        const packed = await cached(
          `mkt:ohlcv:${sym}:${start}`,
          300_000,
          () => loadBars(sym, start),
        );
        ohlcvBySymbol[sym] = packed.bars;
        sparklineBySymbol[sym] = packed.bars.slice(-30).map((b) => ({
          date: b.date,
          value: b.close,
        }));
        providers[sym] = packed.provider;
        if (packed.sourceNote) sourceNotes[sym] = packed.sourceNote;
      } catch (e) {
        warnings.push(
          `${sym}: ${e instanceof Error ? e.message : String(e)}`,
        );
        ohlcvBySymbol[sym] = [];
        sparklineBySymbol[sym] = [];
      }
    }),
  );

  const focus = (active || uniq[0] || "SPY").toUpperCase().replace(/-USD$/, "");
  const benchmarks = ["SPY"];
  if (isCryptoSymbol(focus) && !uniq.includes("BTC")) {
    // ensure BTC bench for crypto focus
  }
  const relIds = Array.from(
    new Set([focus, ...benchmarks, ...(isCryptoSymbol(focus) ? ["BTC"] : [])]),
  ).filter((id) => ohlcvBySymbol[id]?.length || uniq.includes(id));

  // Load missing benchmarks
  for (const id of relIds) {
    if (ohlcvBySymbol[id]?.length) continue;
    try {
      const packed = await cached(`mkt:ohlcv:${id}:${start}`, 300_000, () =>
        loadBars(id, start),
      );
      ohlcvBySymbol[id] = packed.bars;
      providers[id] = packed.provider;
    } catch {
      /* skip */
    }
  }

  const relative = relIds
    .filter((id) => ohlcvBySymbol[id]?.length)
    .map((id) => ({
      id,
      label: id,
      points: normalizeTo100(ohlcvBySymbol[id]),
    }));

  const corrLabels = uniq.filter((s) => (ohlcvBySymbol[s]?.length || 0) >= 10);
  const rets = corrLabels.map((s) =>
    dailyReturns(ohlcvBySymbol[s].map((b) => b.close)),
  );
  const matrix = corrLabels.map((_, i) =>
    corrLabels.map((__, j) =>
      i === j ? 1 : Number(pearson(rets[i], rets[j]).toFixed(3)),
    ),
  );

  return runProvider(
    "internal",
    async () => ({
      ohlcvBySymbol,
      sparklineBySymbol,
      relative,
      corr: { labels: corrLabels, matrix },
      sourceNotes,
      providers,
    }),
    warnings,
  );
}
