import type { DeepPartial, ChartOptions } from "lightweight-charts";
import type { UTCTimestamp } from "lightweight-charts";

export const CHART_ACCENT = "#ff6600";
export const CHART_UP = "#22c55e";
export const CHART_DOWN = "#ef4444";

export function toUtcDay(date: string): UTCTimestamp {
  return Math.floor(Date.parse(`${date}T12:00:00Z`) / 1000) as UTCTimestamp;
}

export function baseChartOptions(
  width: number,
  height: number,
): DeepPartial<ChartOptions> {
  return {
    layout: {
      background: { color: "#000000" },
      textColor: "#aaa",
      fontFamily:
        "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
    },
    grid: {
      vertLines: { color: "#1a1a1a" },
      horzLines: { color: "#1a1a1a" },
    },
    rightPriceScale: { borderColor: "#333" },
    timeScale: { borderColor: "#333", borderVisible: true },
    crosshair: {
      vertLine: { color: "#444", labelBackgroundColor: "#ff6600" },
      horzLine: { color: "#444", labelBackgroundColor: "#ff6600" },
    },
    width,
    height,
  };
}

export type ChartRange = "1M" | "3M" | "1Y" | "5Y";

export const RANGE_DAYS: Record<ChartRange, number> = {
  "1M": 31,
  "3M": 93,
  "1Y": 365,
  "5Y": 1825,
};

export function startFromRange(range: ChartRange): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - RANGE_DAYS[range]);
  return d.toISOString().slice(0, 10);
}

/** Simple SMA over close prices; returns {date,value} aligned to bars with enough lookback. */
export function smaSeries(
  bars: { date: string; close: number }[],
  period: number,
): { date: string; value: number }[] {
  const out: { date: string; value: number }[] = [];
  let sum = 0;
  for (let i = 0; i < bars.length; i++) {
    sum += bars[i].close;
    if (i >= period) sum -= bars[i - period].close;
    if (i >= period - 1) {
      out.push({ date: bars[i].date, value: sum / period });
    }
  }
  return out;
}
