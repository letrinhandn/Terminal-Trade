"use client";

/** Simple SVG radar. */
export function RadarChart({
  axes,
  size = 220,
}: {
  axes: Record<string, number>;
  size?: number;
}) {
  const labels = Object.keys(axes);
  const n = labels.length || 1;
  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.36;
  const pts = labels.map((lab, i) => {
    const v = Math.max(0, Math.min(100, axes[lab])) / 100;
    const a = -Math.PI / 2 + (i / n) * Math.PI * 2;
    return {
      lab,
      x: cx + r * v * Math.cos(a),
      y: cy + r * v * Math.sin(a),
      lx: cx + (r + 18) * Math.cos(a),
      ly: cy + (r + 18) * Math.sin(a),
    };
  });
  const poly = pts.map((p) => `${p.x},${p.y}`).join(" ");
  const rings = [0.25, 0.5, 0.75, 1];

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {rings.map((rr) => (
        <polygon
          key={rr}
          points={labels
            .map((_, i) => {
              const a = -Math.PI / 2 + (i / n) * Math.PI * 2;
              return `${cx + r * rr * Math.cos(a)},${cy + r * rr * Math.sin(a)}`;
            })
            .join(" ")}
          fill="none"
          stroke="#222"
        />
      ))}
      {pts.map((p) => (
        <line
          key={p.lab}
          x1={cx}
          y1={cy}
          x2={cx + r * Math.cos(
            -Math.PI / 2 + (labels.indexOf(p.lab) / n) * Math.PI * 2,
          )}
          y2={cy + r * Math.sin(
            -Math.PI / 2 + (labels.indexOf(p.lab) / n) * Math.PI * 2,
          )}
          stroke="#222"
        />
      ))}
      <polygon points={poly} fill="rgba(255,102,0,0.25)" stroke="#ff6600" strokeWidth={2} />
      {pts.map((p) => (
        <text
          key={p.lab}
          x={p.lx}
          y={p.ly}
          textAnchor="middle"
          className="fill-[#888]"
          style={{ fontSize: 9, fontFamily: "monospace" }}
        >
          {p.lab}
        </text>
      ))}
    </svg>
  );
}
