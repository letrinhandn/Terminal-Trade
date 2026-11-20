"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet } from "@/lib/api";
import { HeatmapMatrix } from "@/components/charts/HeatmapMatrix";
import { RadarChart } from "@/components/charts/RadarChart";

type Intel = {
  title: string;
  url: string;
  seendate: string;
  source: string;
  domain: string;
  level: "FLASH" | "URGENT" | "WATCH";
  tag: string;
  focus: string;
};

type GeoPayload = {
  data: {
    indicators: { symbol: string; label: string; price: number; changePct: number }[];
    intel: Intel[];
    radar: Record<string, number>;
    globalRisk: number;
    stats: { conflicts: number; sanctions: number; alerts: number };
    countryMatrix: {
      name: string;
      mil: number;
      eco: number;
      pol: number;
      tot: number;
      trd: number;
      san: number;
      mentions: number;
    }[];
    focusCounts: { id: string; key: string; mentions: number }[];
    routes: {
      name: string;
      threat: string;
      mentions: number;
      risk: number;
      sample: string | null;
    }[];
    series: {
      id: string;
      label: string;
      color: string;
      dates: string[];
      values: number[];
    }[];
    corr: { labels: string[]; matrix: number[][] };
    marketImpact: {
      symbol: string;
      label: string;
      price: number;
      changePct: number;
      volume: number;
      corr: number;
      impl: string;
    }[];
    focusPanel: {
      id: string;
      headlines: Intel[];
      mentions: number;
      note: string;
    };
    attribution: string;
  };
  meta?: { warnings?: string[] };
};

function Panel({
  title,
  children,
  className = "",
  bodyClassName = "p-2",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section
      className={`flex min-h-0 flex-col overflow-hidden border border-[#2a2a2a] bg-[#0a0a0a] ${className}`}
    >
      <header className="shrink-0 border-b border-[#1f1f1f] bg-[#111] px-2 py-1">
        <h3 className="text-[10px] font-semibold tracking-[0.08em] text-[#ff8c00]">
          {title}
        </h3>
      </header>
      <div className={`min-h-0 flex-1 overflow-auto ${bodyClassName}`}>
        {children}
      </div>
    </section>
  );
}

function scoreColor(n: number) {
  if (n >= 7) return "text-[#ff5252]";
  if (n >= 4) return "text-[#eab308]";
  return "text-[#00e676]";
}

function MultiLineChart({
  series,
}: {
  series: GeoPayload["data"]["series"];
}) {
  const w = 420;
  const h = 180;
  const pad = { t: 10, r: 10, b: 22, l: 28 };
  const paths = useMemo(() => {
    if (!series.length) return [];
    const len = Math.max(...series.map((s) => s.values.length), 2);
    const all = series.flatMap((s) => s.values);
    const min = Math.min(...all, 90);
    const max = Math.max(...all, 110);
    const span = max - min || 1;
    const iw = w - pad.l - pad.r;
    const ih = h - pad.t - pad.b;
    return series.map((s) => {
      const pts = s.values.map((v, i) => {
        const x = pad.l + (i / Math.max(len - 1, 1)) * iw;
        const y = pad.t + (1 - (v - min) / span) * ih;
        return `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
      });
      return { ...s, d: pts.join(" ") };
    });
  }, [series]);

  if (!series.length) {
    return <p className="text-[10px] text-[#555]">No series</p>;
  }

  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} className="h-full w-full min-h-[140px]">
        {[0.25, 0.5, 0.75].map((g) => (
          <line
            key={g}
            x1={pad.l}
            x2={w - pad.r}
            y1={pad.t + g * (h - pad.t - pad.b)}
            y2={pad.t + g * (h - pad.t - pad.b)}
            stroke="#1a1a1a"
          />
        ))}
        {paths.map((p) => (
          <path
            key={p.id}
            d={p.d}
            fill="none"
            stroke={p.color}
            strokeWidth={1.5}
          />
        ))}
        <text
          x={pad.l}
          y={h - 6}
          className="fill-[#555]"
          style={{ fontSize: 9, fontFamily: "monospace" }}
        >
          30D indexed (100 = start)
        </text>
      </svg>
      <div className="mt-1 flex flex-wrap gap-2 font-mono text-[9px]">
        {series.map((s) => (
          <span key={s.id} style={{ color: s.color }}>
            ● {s.label}
          </span>
        ))}
      </div>
    </div>
  );
}

export function GeopoliticsTab({ onStatus }: { onStatus?: (s: string) => void }) {
  const [data, setData] = useState<GeoPayload["data"] | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [focus, setFocus] = useState("INDIA");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const res = await apiGet<GeoPayload>("/api/v1/geopolitics/overview");
        if (cancelled) return;
        setData(res.data);
        setWarnings(res.meta?.warnings || []);
        onStatus?.(
          `GEO | risk ${res.data.globalRisk}/10 | ${res.data.stats.alerts} alerts | ${res.data.corr.labels.length} corr`,
        );
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [onStatus]);

  const filteredIntel = useMemo(() => {
    if (!data) return [];
    if (focus === "ALL") return data.intel;
    const re = new RegExp(
      focus.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
      "i",
    );
    return data.intel.filter((a) => a.focus === focus || re.test(a.title));
  }, [data, focus]);

  const focusHeadlines = useMemo(() => {
    if (!data) return [];
    return data.intel
      .filter((a) => new RegExp(focus, "i").test(a.title) || a.focus === focus)
      .slice(0, 8);
  }, [data, focus]);

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-black text-[10px]">
      {/* Status strip */}
      <div className="flex shrink-0 flex-wrap items-center gap-x-5 gap-y-1 border-b border-[#ff6600]/40 bg-[#0d0800] px-2 py-1.5 font-mono">
        <span className="text-[#ff8800]">
          GLOBAL RISK:{" "}
          <span className="font-bold text-[#ff5252]">
            {data ? data.globalRisk.toFixed(2) : "-"}/10
          </span>
        </span>
        <span className="text-[#ccc]">
          CONFLICT KW:{" "}
          <span className="text-[#ff8800]">{data?.stats.conflicts ?? "-"}</span>
        </span>
        <span className="text-[#ccc]">
          SANCTION KW:{" "}
          <span className="text-[#ff8800]">{data?.stats.sanctions ?? "-"}</span>
        </span>
        <span className="text-[#ccc]">
          ALERTS:{" "}
          <span className="text-[#00e676]">{data?.stats.alerts ?? "-"}</span>
        </span>
        <span className="ml-auto text-[9px] text-[#555]">
          Keyword proxies only
        </span>
      </div>

      {/* Focus chips */}
      <div className="flex shrink-0 flex-wrap gap-1 border-b border-[#222] bg-black px-2 py-1">
        <button
          type="button"
          onClick={() => setFocus("ALL")}
          className={`px-2 py-0.5 font-mono text-[9px] ${
            focus === "ALL"
              ? "bg-[#ff6600] text-black"
              : "border border-[#333] text-[#888]"
          }`}
        >
          ALL
        </button>
        {(data?.focusCounts || []).map((f) => (
          <button
            key={f.id}
            type="button"
            onClick={() => setFocus(f.id)}
            className={`px-2 py-0.5 font-mono text-[9px] ${
              focus === f.id
                ? "bg-[#ff6600] text-black"
                : "border border-[#333] text-[#888] hover:text-[#ff8800]"
            }`}
          >
            <span className="opacity-50">{f.key}</span> {f.id}
            {f.mentions > 0 && (
              <span className="ml-1 text-[#00e676]">{f.mentions}</span>
            )}
          </button>
        ))}
      </div>

      {loading && !data && (
        <p className="p-2 text-[#666]">Loading geopolitics</p>
      )}
      {err && <p className="p-2 text-[#ff5252]">{err}</p>}

      {data && (
        <div className="grid min-h-0 flex-1 grid-cols-1 gap-1 overflow-auto p-1 xl:grid-cols-12 xl:grid-rows-[minmax(180px,1fr)_minmax(160px,1fr)_minmax(140px,0.9fr)]">
          {/* Row 1 */}
          <Panel
            title="Real-Time Intelligence Stream"
            className="xl:col-span-4"
          >
            <ul className="space-y-1 font-mono">
              {(filteredIntel.length ? filteredIntel : data.intel)
                .slice(0, 25)
                .map((a) => (
                  <li
                    key={a.url + a.title}
                    className="border-b border-[#151515] pb-1"
                  >
                    <div className="flex flex-wrap gap-1 text-[9px]">
                      <span className="text-[#555]">
                        {a.seendate.slice(0, 10) || "-"}
                      </span>
                      <span
                        className={
                          a.level === "FLASH"
                            ? "text-[#ff5252]"
                            : a.level === "URGENT"
                              ? "text-[#eab308]"
                              : "text-[#666]"
                        }
                      >
                        [{a.level}]
                      </span>
                      <span className="text-[#38bdf8]">[{a.tag}]</span>
                      <span className="text-[#ff8800]">{a.focus}</span>
                    </div>
                    <a
                      href={a.url}
                      target="_blank"
                      rel="noreferrer"
                      className="leading-snug text-[#ccc] hover:text-[#ff8800]"
                    >
                      {a.title}
                    </a>
                  </li>
                ))}
              {!data.intel.length && (
                <li className="text-[#555]">No headlines (GDELT/RSS limited)</li>
              )}
            </ul>
          </Panel>

          <Panel
            title="Country Risk Assessment (headline proxy)"
            className="xl:col-span-5"
          >
            <table className="w-full border-collapse font-mono text-[10px]">
              <thead className="sticky top-0 bg-[#0a0a0a] text-[#666]">
                <tr>
                  <th className="p-1 text-left font-normal">Country</th>
                  {["MIL", "ECO", "POL", "TOT", "TRD", "SAN"].map((h) => (
                    <th key={h} className="p-1 text-right font-normal">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.countryMatrix.map((r) => (
                  <tr key={r.name} className="border-t border-[#1a1a1a]">
                    <td className="p-1 text-[#ff8800]">
                      {r.name}
                      <span className="ml-1 text-[8px] text-[#555]">
                        n={r.mentions}
                      </span>
                    </td>
                    {(
                      [
                        r.mil,
                        r.eco,
                        r.pol,
                        r.tot,
                        r.trd,
                        r.san,
                      ] as number[]
                    ).map((v, i) => (
                      <td
                        key={i}
                        className={`p-1 text-right ${scoreColor(v)}`}
                      >
                        {v.toFixed(1)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>

          <Panel title="Economic Threat Indicators" className="xl:col-span-3">
            <ul className="space-y-1 font-mono text-[10px]">
              {data.indicators.map((i) => (
                <li
                  key={i.symbol}
                  className={`flex justify-between gap-2 border-b border-[#151515] px-1 py-1 ${
                    Math.abs(i.changePct) >= 1.5 ? "bg-[#2a0a0a]" : ""
                  }`}
                >
                  <span className="text-[#ff8800]">{i.label}</span>
                  <span className="text-[#eee]">{i.price.toFixed(2)}</span>
                  <span
                    className={
                      i.changePct >= 0 ? "text-[#00e676]" : "text-[#ff5252]"
                    }
                  >
                    {i.changePct >= 0 ? "+" : ""}
                    {i.changePct.toFixed(2)}%
                  </span>
                </li>
              ))}
            </ul>
          </Panel>

          {/* Row 2 */}
          <Panel
            title="Multi-Vector Market Stress (30D)"
            className="xl:col-span-5"
          >
            <MultiLineChart series={data.series} />
          </Panel>

          <Panel title="Threat Radar" className="xl:col-span-3">
            <div className="flex justify-center">
              <RadarChart axes={data.radar} size={200} />
            </div>
          </Panel>

          <Panel
            title="Geopolitical Risk vs Markets"
            className="xl:col-span-4"
          >
            <HeatmapMatrix
              labels={data.corr.labels}
              matrix={data.corr.matrix}
            />
          </Panel>

          {/* Row 3 */}
          <Panel title="Market Impact Analysis" className="xl:col-span-4">
            <table className="w-full border-collapse font-mono text-[10px]">
              <thead className="text-[#666]">
                <tr>
                  <th className="p-1 text-left font-normal">Sector</th>
                  <th className="p-1 text-right font-normal">Corr VIX</th>
                  <th className="p-1 text-right font-normal">Impl</th>
                  <th className="p-1 text-right font-normal">Vol</th>
                  <th className="p-1 text-right font-normal">Chg%</th>
                </tr>
              </thead>
              <tbody>
                {data.marketImpact.map((m) => (
                  <tr key={m.symbol} className="border-t border-[#1a1a1a]">
                    <td className="p-1 text-[#ff8800]">{m.label}</td>
                    <td className="p-1 text-right">{m.corr.toFixed(2)}</td>
                    <td className="p-1 text-right text-[#888]">{m.impl}</td>
                    <td className="p-1 text-right text-[#aaa]">
                      {(m.volume / 1e6).toFixed(1)}M
                    </td>
                    <td
                      className={`p-1 text-right ${
                        m.changePct >= 0 ? "text-[#00e676]" : "text-[#ff5252]"
                      }`}
                    >
                      {m.changePct >= 0 ? "+" : ""}
                      {m.changePct.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>

          <Panel title="Critical Trade Route Risk" className="xl:col-span-4">
            <ul className="space-y-2">
              {data.routes.map((r) => (
                <li
                  key={r.name}
                  className="border-b border-[#151515] pb-1.5 font-mono"
                >
                  <div className="flex justify-between gap-2">
                    <span className="text-[#ff8800]">{r.name}</span>
                    <span className={scoreColor(r.risk)}>
                      RISK {r.risk}/10
                    </span>
                  </div>
                  <div className="mt-0.5 flex justify-between text-[9px] text-[#666]">
                    <span>{r.threat}</span>
                    <span>hits {r.mentions}</span>
                  </div>
                  {r.sample && (
                    <p className="mt-0.5 line-clamp-2 text-[9px] text-[#777]">
                      {r.sample}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </Panel>

          <Panel
            title={`${focus === "ALL" ? "INDIA" : focus} Strategic Focus`}
            className="xl:col-span-4"
          >
            <div className="mb-2 font-mono text-[9px] text-[#666]">
              Mentions in batch:{" "}
              <span className="text-[#ff8800]">{focusHeadlines.length}</span>
              {" | "}
              {data.focusPanel.note}
            </div>
            <ul className="space-y-1.5">
              {(focusHeadlines.length
                ? focusHeadlines
                : data.focusPanel.headlines
              ).map((a) => (
                <li key={a.url + a.title} className="border-b border-[#151515] pb-1">
                  <a
                    href={a.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[#ccc] hover:text-[#ff8800]"
                  >
                    {a.title}
                  </a>
                </li>
              ))}
              {!focusHeadlines.length && !data.focusPanel.headlines.length && (
                <li className="text-[#555]">
                  No headlines for this focus in current batch
                </li>
              )}
            </ul>
          </Panel>
        </div>
      )}

      {data && (
        <p className="shrink-0 truncate border-t border-[#1a1a1a] px-2 py-0.5 text-[8px] text-[#444]">
          {data.attribution}
          {warnings.length ? ` | ${warnings.slice(0, 3).join(" | ")}` : ""}
        </p>
      )}
    </div>
  );
}
