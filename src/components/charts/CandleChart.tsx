"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type SeriesMarker,
  type Time,
} from "lightweight-charts";
import type { OhlcvBar } from "@/lib/types";
import {
  baseChartOptions,
  CHART_DOWN,
  CHART_UP,
  smaSeries,
  toUtcDay,
} from "@/components/charts/chartTheme";

export type CandleMarker = {
  date: string;
  position?: "aboveBar" | "belowBar" | "inBar";
  shape?: "arrowUp" | "arrowDown" | "circle" | "square";
  color?: string;
  text?: string;
};

const SMA_COLORS = ["#ff9500", "#60a5fa", "#a78bfa"];

export function CandleChart({
  bars,
  height = 360,
  showVolume = true,
  smaPeriods = [],
  markers = [],
  sourceNote,
  emptyLabel = "No OHLCV",
}: {
  bars: OhlcvBar[];
  height?: number;
  showVolume?: boolean;
  smaPeriods?: number[];
  markers?: CandleMarker[];
  sourceNote?: string;
  emptyLabel?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const smaKey = smaPeriods.join(",");
  const markerKey = markers
    .map((m) => `${m.date}:${m.shape}:${m.text ?? ""}`)
    .join("|");

  useEffect(() => {
    const el = ref.current;
    if (!el || !bars.length) return;

    const width = Math.max(el.clientWidth || 0, el.parentElement?.clientWidth || 0, 320);
    const chart: IChartApi = createChart(
      el,
      baseChartOptions(width, height),
    );

    const candle: ISeriesApi<"Candlestick"> = chart.addSeries(
      CandlestickSeries,
      {
        upColor: CHART_UP,
        downColor: CHART_DOWN,
        borderUpColor: CHART_UP,
        borderDownColor: CHART_DOWN,
        wickUpColor: CHART_UP,
        wickDownColor: CHART_DOWN,
      },
    );

    const byTime = new Map<
      number,
      { time: ReturnType<typeof toUtcDay>; open: number; high: number; low: number; close: number }
    >();
    for (const b of bars) {
      if (
        !Number.isFinite(b.open) ||
        !Number.isFinite(b.high) ||
        !Number.isFinite(b.low) ||
        !Number.isFinite(b.close)
      ) {
        continue;
      }
      const time = toUtcDay(b.date);
      byTime.set(time as number, {
        time,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      });
    }
    const unique = Array.from(byTime.values()).sort(
      (a, b) => (a.time as number) - (b.time as number),
    );
    candle.setData(unique);

    if (showVolume) {
      chart.priceScale("right").applyOptions({
        scaleMargins: { top: 0.05, bottom: 0.22 },
      });
      const vol = chart.addSeries(HistogramSeries, {
        priceFormat: { type: "volume" },
        priceScaleId: "vol",
      });
      chart.priceScale("vol").applyOptions({
        scaleMargins: { top: 0.82, bottom: 0 },
      });
      vol.setData(
        bars.map((b) => ({
          time: toUtcDay(b.date),
          value: b.volume,
          color:
            b.close >= b.open
              ? "rgba(34,197,94,0.45)"
              : "rgba(239,68,68,0.45)",
        })),
      );
    }

    smaPeriods.forEach((period, i) => {
      const line = chart.addSeries(LineSeries, {
        color: SMA_COLORS[i % SMA_COLORS.length],
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      const sma = smaSeries(
        bars.map((b) => ({ date: b.date, close: b.close })),
        period,
      );
      line.setData(
        sma.map((p) => ({ time: toUtcDay(p.date), value: p.value })),
      );
    });

    if (markers.length) {
      const timeSet = new Set(unique.map((u) => u.time as number));
      const seriesMarkers: SeriesMarker<Time>[] = markers
        .map((m) => ({
          time: toUtcDay(m.date) as Time,
          position: m.position ?? "belowBar",
          shape: m.shape ?? "circle",
          color: m.color ?? "#ff6600",
          text: m.text,
        }))
        .filter((m) => timeSet.has(m.time as number));
      if (seriesMarkers.length) {
        createSeriesMarkers(candle, seriesMarkers);
      }
    }

    chart.timeScale().fitContent();

    // Remeasure after layout (avoids 0-width first paint)
    requestAnimationFrame(() => {
      const w = ref.current?.clientWidth || 0;
      if (w > 0) chart.applyOptions({ width: w });
      chart.timeScale().fitContent();
    });

    const ro = new ResizeObserver(() => {
      const w = ref.current?.clientWidth || 0;
      if (w > 0) chart.applyOptions({ width: w });
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      chart.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bars, height, showVolume, smaKey, markerKey]);

  if (!bars.length) {
    return (
      <div
        className="flex items-center justify-center text-sm text-[#666]"
        style={{ height }}
      >
        {emptyLabel}
      </div>
    );
  }

  return (
    <div className="w-full">
      <div ref={ref} className="w-full" style={{ height }} />
      {sourceNote && (
        <p className="mt-1 text-[9px] leading-snug text-[#555]">{sourceNote}</p>
      )}
    </div>
  );
}
