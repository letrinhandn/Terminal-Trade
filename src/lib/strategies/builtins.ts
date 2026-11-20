import type { OhlcvBar } from "@/lib/types";

export type Bar = OhlcvBar & {
  signal?: number;
  macd?: number;
  macdSignal?: number;
  rsi?: number;
};

function ewma(values: number[], span: number): number[] {
  const alpha = 2 / (span + 1);
  const out: number[] = [];
  let prev = values[0] ?? 0;
  for (let i = 0; i < values.length; i++) {
    prev = i === 0 ? values[i] : alpha * values[i] + (1 - alpha) * prev;
    out.push(prev);
  }
  return out;
}

export function applyMacd(
  bars: OhlcvBar[],
  fast = 12,
  slow = 26,
  signalPeriod = 9,
): Bar[] {
  const closes = bars.map((b) => b.close);
  const emaFast = ewma(closes, fast);
  const emaSlow = ewma(closes, slow);
  const macd = emaFast.map((v, i) => v - emaSlow[i]);
  const macdSignal = ewma(macd, signalPeriod);
  return bars.map((b, i) => {
    let signal = 0;
    if (i > 0) {
      const crossUp = macd[i] > macdSignal[i] && macd[i - 1] <= macdSignal[i - 1];
      const crossDown = macd[i] < macdSignal[i] && macd[i - 1] >= macdSignal[i - 1];
      if (crossUp) signal = 1;
      if (crossDown) signal = -1;
    }
    return { ...b, macd: macd[i], macdSignal: macdSignal[i], signal };
  });
}

export function applyRsi(
  bars: OhlcvBar[],
  period = 14,
  oversold = 30,
  overbought = 70,
): Bar[] {
  const rsi: number[] = new Array(bars.length).fill(50);
  const gains: number[] = [];
  const losses: number[] = [];
  for (let i = 1; i < bars.length; i++) {
    const d = bars[i].close - bars[i - 1].close;
    gains.push(Math.max(d, 0));
    losses.push(Math.max(-d, 0));
  }
  for (let i = period; i < bars.length; i++) {
    const g = gains.slice(i - period, i).reduce((a, b) => a + b, 0) / period;
    const l = losses.slice(i - period, i).reduce((a, b) => a + b, 0) / period;
    const rs = l === 0 ? 100 : g / l;
    rsi[i] = 100 - 100 / (1 + rs);
  }
  return bars.map((b, i) => {
    let signal = 0;
    if (i > 0) {
      if (rsi[i] < oversold && rsi[i - 1] >= oversold) signal = 1;
      if (rsi[i] > overbought && rsi[i - 1] <= overbought) signal = -1;
    }
    return { ...b, rsi: rsi[i], signal };
  });
}

/** Advanced MACD: require rising histogram + volume above SMA20 */
export function applyMacdAdvanced(bars: OhlcvBar[]): Bar[] {
  const base = applyMacd(bars);
  const volSma: number[] = [];
  for (let i = 0; i < bars.length; i++) {
    const slice = bars.slice(Math.max(0, i - 19), i + 1);
    volSma.push(slice.reduce((a, b) => a + b.volume, 0) / slice.length);
  }
  return base.map((b, i) => {
    if (b.signal === 1) {
      const hist = (b.macd ?? 0) - (b.macdSignal ?? 0);
      const prevHist =
        i > 0 ? (base[i - 1].macd ?? 0) - (base[i - 1].macdSignal ?? 0) : hist;
      if (!(hist > prevHist && bars[i].volume >= volSma[i])) {
        return { ...b, signal: 0 };
      }
    }
    return b;
  });
}

export function applyMacdConservative(bars: OhlcvBar[]): Bar[] {
  return applyMacd(bars, 16, 32, 12);
}

export function applyMacdAggressive(bars: OhlcvBar[]): Bar[] {
  return applyMacd(bars, 8, 17, 6);
}

export const STRATEGY_IDS = [
  "MACD",
  "MACD_ADVANCED",
  "MACD_CONSERVATIVE",
  "MACD_AGGRESSIVE",
  "RSI",
] as const;

export type StrategyId = (typeof STRATEGY_IDS)[number];

export function runStrategy(id: StrategyId, bars: OhlcvBar[]): Bar[] {
  switch (id) {
    case "MACD":
      return applyMacd(bars);
    case "MACD_ADVANCED":
      return applyMacdAdvanced(bars);
    case "MACD_CONSERVATIVE":
      return applyMacdConservative(bars);
    case "MACD_AGGRESSIVE":
      return applyMacdAggressive(bars);
    case "RSI":
      return applyRsi(bars);
    default:
      return applyMacd(bars);
  }
}
