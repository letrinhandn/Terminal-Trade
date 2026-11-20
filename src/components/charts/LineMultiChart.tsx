"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  LineSeries,
  type IChartApi,
} from "lightweight-charts";
import { baseChartOptions, toUtcDay } from "@/components/charts/chartTheme";

const DEFAULT_COLORS = [
  "#ff6600",
  "#60a5fa",
  "#22c55e",
  "#a78bfa",
  "#f472b6",
  "#eab308",
];

export type LineSeriesInput = {
  id: string;
  label?: string;
  color?: string;
  points: { date: string; value: number }[];
};

export function LineMultiChart({
  series,
  height = 220,
  emptyLabel = "No series",
}: {
  series: LineSeriesInput[];
  height?: number;
  emptyLabel?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    const usable = series.filter((s) => s.points.length > 0);
    if (!el || !usable.length) return;

    const chart: IChartApi = createChart(
      el,
      baseChartOptions(el.clientWidth || 600, height),
    );

    usable.forEach((s, i) => {
      const line = chart.addSeries(LineSeries, {
        color: s.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length],
        lineWidth: 2,
        title: s.label || s.id,
      });
      const byTime = new Map<number, number>();
      for (const p of s.points) {
        if (!Number.isFinite(p.value)) continue;
        byTime.set(toUtcDay(p.date) as number, p.value);
      }
      line.setData(
        Array.from(byTime.entries())
          .sort((a, b) => a[0] - b[0])
          .map(([time, value]) => ({
            time: time as ReturnType<typeof toUtcDay>,
            value,
          })),
      );
    });

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
  }, [series, height]);

  if (!series.some((s) => s.points.length)) {
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
      <div className="mt-1 flex flex-wrap gap-3 text-[9px] text-[#888]">
        {series.map((s, i) => (
          <span key={s.id} className="inline-flex items-center gap-1">
            <span
              className="inline-block h-1.5 w-3 rounded-sm"
              style={{
                background:
                  s.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length],
              }}
            />
            {s.label || s.id}
          </span>
        ))}
      </div>
    </div>
  );
}
