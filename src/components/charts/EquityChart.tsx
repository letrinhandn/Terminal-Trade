"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  AreaSeries,
  type IChartApi,
  type ISeriesApi,
} from "lightweight-charts";
import {
  baseChartOptions,
  CHART_ACCENT,
  toUtcDay,
} from "@/components/charts/chartTheme";

export function EquityChart({
  data,
  height = 280,
}: {
  data: { date: string; equity: number }[];
  height?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || data.length === 0) return;

    const chart: IChartApi = createChart(
      el,
      baseChartOptions(el.clientWidth || 600, height),
    );

    const series: ISeriesApi<"Area"> = chart.addSeries(AreaSeries, {
      lineColor: CHART_ACCENT,
      topColor: "rgba(255,102,0,0.35)",
      bottomColor: "rgba(255,102,0,0.02)",
      lineWidth: 2,
    });

    const dedup = new Map<number, number>();
    for (const d of data) {
      if (!Number.isFinite(d.equity)) continue;
      dedup.set(toUtcDay(d.date) as number, d.equity);
    }
    series.setData(
      Array.from(dedup.entries())
        .sort((a, b) => a[0] - b[0])
        .map(([time, value]) => ({
          time: time as ReturnType<typeof toUtcDay>,
          value,
        })),
    );
    chart.timeScale().fitContent();

    const ro = new ResizeObserver(() => {
      if (ref.current) {
        chart.applyOptions({ width: ref.current.clientWidth });
      }
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [data, height]);

  if (!data.length) {
    return (
      <div
        className="flex items-center justify-center text-sm text-[#666]"
        style={{ height }}
      >
        No equity data
      </div>
    );
  }

  return <div ref={ref} className="w-full" style={{ minHeight: height }} />;
}
