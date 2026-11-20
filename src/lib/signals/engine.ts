import type { MarketSignal, OhlcvBar, SignalSide } from "@/lib/types";

function sma(values: number[], period: number, i: number): number | null {
  if (i + 1 < period) return null;
  let sum = 0;
  for (let j = i - period + 1; j <= i; j++) sum += values[j];
  return sum / period;
}

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

function rsiSeries(closes: number[], period = 14): number[] {
  const rsi = new Array(closes.length).fill(50);
  const gains: number[] = [];
  const losses: number[] = [];
  for (let i = 1; i < closes.length; i++) {
    const d = closes[i] - closes[i - 1];
    gains.push(Math.max(d, 0));
    losses.push(Math.max(-d, 0));
  }
  for (let i = period; i < closes.length; i++) {
    const g = gains.slice(i - period, i).reduce((a, b) => a + b, 0) / period;
    const l = losses.slice(i - period, i).reduce((a, b) => a + b, 0) / period;
    const rs = l === 0 ? 100 : g / l;
    rsi[i] = 100 - 100 / (1 + rs);
  }
  return rsi;
}

function clamp01(n: number): number {
  return Math.max(0, Math.min(1, n));
}

function pctChange(from: number, to: number): number {
  if (!from) return 0;
  return ((to - from) / from) * 100;
}

/** Detect rule-based signals from daily OHLCV (research helper, not advice). */
export function detectSignals(bars: OhlcvBar[]): MarketSignal[] {
  if (bars.length < 60) return [];

  const closes = bars.map((b) => b.close);
  const volumes = bars.map((b) => b.volume);
  const i = bars.length - 1;
  const asOf = bars[i].date;
  const out: MarketSignal[] = [];

  // MACD cross
  const ema12 = ewma(closes, 12);
  const ema26 = ewma(closes, 26);
  const macd = ema12.map((v, idx) => v - ema26[idx]);
  const macdSig = ewma(macd, 9);
  const hist = macd[i] - macdSig[i];
  const prevHist = macd[i - 1] - macdSig[i - 1];
  if (macd[i] > macdSig[i] && macd[i - 1] <= macdSig[i - 1]) {
    out.push({
      id: "macd_bull_cross",
      label: "MACD bullish cross",
      side: "bullish",
      strength: clamp01(0.55 + Math.min(Math.abs(hist) / (closes[i] * 0.01), 0.4)),
      asOf,
      detail: `MACD crossed above signal (hist ${hist.toFixed(3)})`,
      replayStrategy: "MACD",
    });
  } else if (macd[i] < macdSig[i] && macd[i - 1] >= macdSig[i - 1]) {
    out.push({
      id: "macd_bear_cross",
      label: "MACD bearish cross",
      side: "bearish",
      strength: clamp01(0.55 + Math.min(Math.abs(hist) / (closes[i] * 0.01), 0.4)),
      asOf,
      detail: `MACD crossed below signal (hist ${hist.toFixed(3)})`,
      replayStrategy: "MACD",
    });
  } else if (hist > 0 && hist > prevHist) {
    out.push({
      id: "macd_hist_rising",
      label: "MACD momentum rising",
      side: "bullish",
      strength: 0.4,
      asOf,
      detail: `Histogram rising (${prevHist.toFixed(3)} → ${hist.toFixed(3)})`,
      replayStrategy: "MACD",
    });
  } else if (hist < 0 && hist < prevHist) {
    out.push({
      id: "macd_hist_falling",
      label: "MACD momentum fading",
      side: "bearish",
      strength: 0.4,
      asOf,
      detail: `Histogram falling (${prevHist.toFixed(3)} → ${hist.toFixed(3)})`,
      replayStrategy: "MACD",
    });
  }

  // RSI
  const rsi = rsiSeries(closes, 14);
  const r = rsi[i];
  const rp = rsi[i - 1];
  if (r < 30 && rp >= 30) {
    out.push({
      id: "rsi_oversold_exit",
      label: "RSI entered oversold",
      side: "bullish",
      strength: clamp01((30 - r) / 30 + 0.45),
      asOf,
      detail: `RSI ${r.toFixed(1)} (was ${rp.toFixed(1)})`,
      replayStrategy: "RSI",
    });
  } else if (r > 70 && rp <= 70) {
    out.push({
      id: "rsi_overbought_enter",
      label: "RSI entered overbought",
      side: "bearish",
      strength: clamp01((r - 70) / 30 + 0.45),
      asOf,
      detail: `RSI ${r.toFixed(1)} (was ${rp.toFixed(1)})`,
      replayStrategy: "RSI",
    });
  } else if (r < 35) {
    out.push({
      id: "rsi_oversold_zone",
      label: "RSI oversold zone",
      side: "bullish",
      strength: 0.35,
      asOf,
      detail: `RSI ${r.toFixed(1)}`,
      replayStrategy: "RSI",
    });
  } else if (r > 65) {
    out.push({
      id: "rsi_overbought_zone",
      label: "RSI elevated",
      side: "bearish",
      strength: 0.35,
      asOf,
      detail: `RSI ${r.toFixed(1)}`,
      replayStrategy: "RSI",
    });
  }

  // SMA trend
  const sma50 = sma(closes, 50, i);
  const sma200 = sma(closes, 200, i);
  const sma50p = sma(closes, 50, i - 1);
  if (sma50 != null && sma50p != null) {
    if (closes[i] > sma50 && closes[i - 1] <= sma50p) {
      out.push({
        id: "price_above_sma50",
        label: "Price reclaimed SMA50",
        side: "bullish",
        strength: 0.6,
        asOf,
        detail: `Close ${closes[i].toFixed(2)} vs SMA50 ${sma50.toFixed(2)}`,
      });
    } else if (closes[i] < sma50 && closes[i - 1] >= sma50p) {
      out.push({
        id: "price_below_sma50",
        label: "Price lost SMA50",
        side: "bearish",
        strength: 0.6,
        asOf,
        detail: `Close ${closes[i].toFixed(2)} vs SMA50 ${sma50.toFixed(2)}`,
      });
    }
  }
  if (sma50 != null && sma200 != null) {
    const side: SignalSide = sma50 >= sma200 ? "bullish" : "bearish";
    out.push({
      id: side === "bullish" ? "golden_bias" : "death_bias",
      label: side === "bullish" ? "SMA50 above SMA200" : "SMA50 below SMA200",
      side,
      strength: 0.5,
      asOf,
      detail: `SMA50 ${sma50.toFixed(2)} / SMA200 ${sma200.toFixed(2)}`,
    });
  }

  // Volume spike
  const volSma20 = sma(volumes, 20, i);
  if (volSma20 && volSma20 > 0 && volumes[i] >= volSma20 * 1.8) {
    const upDay = closes[i] >= closes[i - 1];
    out.push({
      id: "volume_spike",
      label: upDay ? "High-volume advance" : "High-volume decline",
      side: upDay ? "bullish" : "bearish",
      strength: clamp01(volumes[i] / volSma20 / 3),
      asOf,
      detail: `Vol ${(volumes[i] / 1e6).toFixed(2)}M vs 20d avg ${(volSma20 / 1e6).toFixed(2)}M`,
    });
  }

  // Momentum
  if (i >= 21) {
    const m1m = pctChange(closes[i - 21], closes[i]);
    if (m1m >= 8) {
      out.push({
        id: "mom_1m_strong",
        label: "Strong 1M momentum",
        side: "bullish",
        strength: clamp01(m1m / 20),
        asOf,
        detail: `~1M change ${m1m.toFixed(1)}%`,
      });
    } else if (m1m <= -8) {
      out.push({
        id: "mom_1m_weak",
        label: "Weak 1M momentum",
        side: "bearish",
        strength: clamp01(Math.abs(m1m) / 20),
        asOf,
        detail: `~1M change ${m1m.toFixed(1)}%`,
      });
    }
  }

  return out.sort((a, b) => b.strength - a.strength);
}

/** Aggregate -100..100 score from active signals. */
export function scoreFromSignals(signals: MarketSignal[]): number {
  if (!signals.length) return 0;
  let raw = 0;
  for (const s of signals) {
    const dir = s.side === "bullish" ? 1 : s.side === "bearish" ? -1 : 0;
    raw += dir * s.strength * 40;
  }
  return Math.max(-100, Math.min(100, Math.round(raw)));
}

export function changePctLookback(bars: OhlcvBar[], days: number): number | null {
  if (bars.length < days + 1) return null;
  const a = bars[bars.length - 1 - days].close;
  const b = bars[bars.length - 1].close;
  if (!a) return null;
  return ((b - a) / a) * 100;
}
