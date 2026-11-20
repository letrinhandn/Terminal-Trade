"use client";

import { CHART_DOWN, CHART_UP } from "@/components/charts/chartTheme";

/** Tiny SVG sparkline - no lightweight-charts (avoids 0-width / watermark bugs). */
export function Sparkline({
  values,
  height = 28,
  width = 72,
}: {
  values: { date: string; value: number }[];
  height?: number;
  width?: number;
}) {
  const pts = values.filter((v) => Number.isFinite(v.value));
  if (pts.length < 2) {
    return (
      <svg width={width} height={height} className="inline-block align-middle">
        <line
          x1={4}
          x2={width - 4}
          y1={height / 2}
          y2={height / 2}
          stroke="#333"
          strokeWidth={1}
        />
      </svg>
    );
  }

  const ys = pts.map((p) => p.value);
  const min = Math.min(...ys);
  const max = Math.max(...ys);
  const span = max - min || 1;
  const pad = 2;
  const w = width - pad * 2;
  const h = height - pad * 2;
  const coords = pts.map((p, i) => {
    const x = pad + (i / (pts.length - 1)) * w;
    const y = pad + (1 - (p.value - min) / span) * h;
    return [x, y] as const;
  });
  const line = coords.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `${line} L${coords[coords.length - 1][0].toFixed(1)},${height - pad} L${coords[0][0].toFixed(1)},${height - pad} Z`;
  const up = ys[ys.length - 1] >= ys[0];
  const stroke = up ? CHART_UP : CHART_DOWN;
  const fill = up ? "rgba(34,197,94,0.25)" : "rgba(239,68,68,0.25)";

  return (
    <svg
      width={width}
      height={height}
      className="inline-block align-middle"
      aria-hidden
    >
      <path d={area} fill={fill} />
      <path d={line} fill="none" stroke={stroke} strokeWidth={1.5} />
    </svg>
  );
}
