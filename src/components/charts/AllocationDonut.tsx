"use client";

type Slice = { id: string; label: string; weight: number; color?: string };

const COLORS = [
  "#ff6600",
  "#ff9500",
  "#60a5fa",
  "#22c55e",
  "#a78bfa",
  "#f472b6",
  "#eab308",
  "#94a3b8",
];

/** Simple SVG donut for paper portfolio weights. */
export function AllocationDonut({
  slices,
  size = 160,
}: {
  slices: Slice[];
  size?: number;
}) {
  const usable = slices.filter((s) => s.weight > 0.05);
  const total = usable.reduce((a, s) => a + s.weight, 0) || 1;
  const r = size / 2;
  const inner = r * 0.55;
  const cx = r;
  const cy = r;

  let angle = -Math.PI / 2;
  const paths: { d: string; color: string; label: string; weight: number }[] =
    [];

  usable.forEach((s, i) => {
    const frac = s.weight / total;
    const sweep = frac * Math.PI * 2;
    const a0 = angle;
    const a1 = angle + sweep;
    angle = a1;
    const x0 = cx + r * Math.cos(a0);
    const y0 = cy + r * Math.sin(a0);
    const x1 = cx + r * Math.cos(a1);
    const y1 = cy + r * Math.sin(a1);
    const xi0 = cx + inner * Math.cos(a1);
    const yi0 = cy + inner * Math.sin(a1);
    const xi1 = cx + inner * Math.cos(a0);
    const yi1 = cy + inner * Math.sin(a0);
    const large = sweep > Math.PI ? 1 : 0;
    const d = [
      `M ${x0} ${y0}`,
      `A ${r} ${r} 0 ${large} 1 ${x1} ${y1}`,
      `L ${xi0} ${yi0}`,
      `A ${inner} ${inner} 0 ${large} 0 ${xi1} ${yi1}`,
      "Z",
    ].join(" ");
    paths.push({
      d,
      color: s.color || COLORS[i % COLORS.length],
      label: s.label,
      weight: s.weight,
    });
  });

  if (!usable.length) {
    return (
      <div
        className="flex items-center justify-center text-xs text-[#555]"
        style={{ width: size, height: size }}
      >
        No positions
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-4">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {paths.map((p) => (
          <path
            key={p.label + p.weight}
            d={p.d}
            fill={p.color}
            stroke="#000"
            strokeWidth={1}
          >
            <title>
              {p.label} {p.weight.toFixed(1)}%
            </title>
          </path>
        ))}
      </svg>
      <ul className="space-y-1 font-mono text-[10px] text-[#aaa]">
        {paths.map((p) => (
          <li key={p.label} className="flex items-center gap-2">
            <span
              className="inline-block h-2 w-2 rounded-sm"
              style={{ background: p.color }}
            />
            {p.label}
            <span className="text-[#666]">{p.weight.toFixed(1)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
