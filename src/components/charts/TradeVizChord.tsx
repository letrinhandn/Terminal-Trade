"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet } from "@/lib/api";

type Partner = {
  code: number;
  short: string;
  name: string;
  exports: number;
  imports: number;
};

type Payload = {
  data: { period: string; partners: Partner[]; source: string };
};

/** US trade partners from Comtrade export/import flows. */
export function TradeVizChord({ size = 300 }: { size?: number }) {
  const [partners, setPartners] = useState<Partner[]>([]);
  const [period, setPeriod] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const res = await apiGet<Payload>("/api/v1/trade/us-partners");
        if (cancelled) return;
        setPartners((res.data.partners || []).slice(0, 12));
        setPeriod(res.data.period);
        setError(null);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e));
          setPartners([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const totals = useMemo(() => {
    const exp = partners.reduce((s, p) => s + p.exports, 0);
    const imp = partners.reduce((s, p) => s + p.imports, 0);
    return { exp, imp, max: Math.max(...partners.map((p) => p.exports + p.imports), 1) };
  }, [partners]);

  const pad = 40;
  const cx = size / 2;
  const cy = size / 2;
  const rOuter = size * 0.32;
  const rLabel = size * 0.44;

  const nodes = partners.map((p, i) => {
    const a = -Math.PI / 2 + (i / Math.max(partners.length, 1)) * Math.PI * 2;
    return {
      ...p,
      a,
      x: cx + rOuter * Math.cos(a),
      y: cy + rOuter * Math.sin(a),
      lx: cx + rLabel * Math.cos(a),
      ly: cy + rLabel * Math.sin(a),
    };
  });

  if (loading) {
    return (
      <div className="flex h-[280px] items-center justify-center text-xs text-[#666]">
        Loading US trade
      </div>
    );
  }
  if (error || !partners.length) {
    return (
      <div className="flex h-[280px] items-center justify-center px-4 text-center text-xs text-[#888]">
        {error || "No Comtrade data"}
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-1 flex flex-wrap items-center justify-between gap-2 px-1 text-[10px] text-[#888]">
        <span>US partners {period}</span>
        <span className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1">
            <span className="inline-block h-1.5 w-3 rounded-sm bg-[#ff6600]" /> Exp
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="inline-block h-1.5 w-3 rounded-sm bg-[#8b5cf6]" /> Imp
          </span>
        </span>
      </div>
      <div className="flex justify-center">
        <svg
          width="100%"
          height={size}
          viewBox={`${-pad} ${-pad} ${size + pad * 2} ${size + pad * 2}`}
          className="max-w-[360px]"
          role="img"
          aria-label={`US trade partners ${period}`}
        >
          {[0.4, 0.65, 1].map((rr) => (
            <circle
              key={rr}
              cx={cx}
              cy={cy}
              r={rOuter * rr}
              fill="none"
              stroke="#1c1c1c"
            />
          ))}
          {nodes.map((n) => {
            const w = (n.exports + n.imports) / totals.max;
            const mid = rOuter * 0.5;
            const qxExp = cx + mid * Math.cos(n.a - 0.12);
            const qyExp = cy + mid * Math.sin(n.a - 0.12);
            const qxImp = cx + mid * Math.cos(n.a + 0.12);
            const qyImp = cy + mid * Math.sin(n.a + 0.12);
            return (
              <g key={n.code}>
                {n.exports > 0 && (
                  <path
                    d={`M ${cx} ${cy} Q ${qxExp} ${qyExp} ${n.x} ${n.y}`}
                    fill="none"
                    stroke="#ff6600"
                    strokeWidth={1.5 + (n.exports / totals.max) * 12}
                    strokeLinecap="round"
                    opacity={0.35 + w * 0.5}
                  />
                )}
                {n.imports > 0 && (
                  <path
                    d={`M ${cx} ${cy} Q ${qxImp} ${qyImp} ${n.x} ${n.y}`}
                    fill="none"
                    stroke="#8b5cf6"
                    strokeWidth={1.5 + (n.imports / totals.max) * 12}
                    strokeLinecap="round"
                    opacity={0.35 + w * 0.5}
                  />
                )}
                <rect
                  x={n.x - 18}
                  y={n.y - 10}
                  width={36}
                  height={20}
                  rx={2}
                  fill="#121212"
                  stroke="#3a3a3a"
                />
                <text
                  x={n.lx}
                  y={n.ly}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="#c8c8c8"
                  style={{ fontSize: 11, fontFamily: "ui-sans-serif, system-ui" }}
                >
                  {n.short}
                </text>
                <title>
                  {n.name}: Exp ${(n.exports / 1e9).toFixed(1)}B / Imp $
                  {(n.imports / 1e9).toFixed(1)}B
                </title>
              </g>
            );
          })}
          <rect
            x={cx - 18}
            y={cy - 12}
            width={36}
            height={24}
            rx={2}
            fill="#1a0a00"
            stroke="#ff6600"
            strokeWidth={1.5}
          />
          <text
            x={cx}
            y={cy + 1}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="#ff9500"
            style={{ fontSize: 12, fontWeight: 700, fontFamily: "ui-sans-serif, system-ui" }}
          >
            US
          </text>
        </svg>
      </div>
      <div className="mt-1 grid grid-cols-2 gap-2 px-1 font-mono text-[10px] text-[#888]">
        <div>
          Exp{" "}
          <span className="text-[#ff8800]">
            ${(totals.exp / 1e12).toFixed(2)}T
          </span>
        </div>
        <div className="text-right">
          Imp{" "}
          <span className="text-[#a78bfa]">
            ${(totals.imp / 1e12).toFixed(2)}T
          </span>
        </div>
      </div>
    </div>
  );
}
