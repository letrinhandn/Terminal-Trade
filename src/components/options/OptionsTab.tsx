"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import type { OptionContract, OptionsSub } from "@/lib/types";
import { formatPricerResults } from "@/lib/options/blackScholes";

const Plot = dynamic(
  () => import("react-plotly.js").then((m) => m.default),
  { ssr: false, loading: () => <div className="p-4 text-sm text-[#666]">Loading chart</div> },
);

export function OptionsTab({
  symbol,
  sub,
  onSymbolChange,
  onSubChange,
}: {
  symbol: string;
  sub: OptionsSub;
  onSymbolChange: (s: string) => void;
  onSubChange: (s: OptionsSub) => void;
}) {
  const currency = symbol.toUpperCase().startsWith("ETH") ? "ETH" : "BTC";
  const [contracts, setContracts] = useState<OptionContract[]>([]);
  const [status, setStatus] = useState("Idle");
  const [fromCache, setFromCache] = useState(false);
  const [showCalls, setShowCalls] = useState(true);
  const [showPuts, setShowPuts] = useState(true);
  const [expiryFilter, setExpiryFilter] = useState<string>("ALL");
  const [visibleCount, setVisibleCount] = useState(50);

  // pricer
  const [spot, setSpot] = useState(100);
  const [strike, setStrike] = useState(100);
  const [dte, setDte] = useState(30);
  const [iv, setIv] = useState(0.5);
  const [optType, setOptType] = useState<"call" | "put">("call");
  const pricerText = formatPricerResults(spot, strike, dte, iv, optType);

  const expiries = useMemo(
    () => Array.from(new Set(contracts.map((c) => c.expiry))).sort(),
    [contracts],
  );

  const filtered = useMemo(() => {
    return contracts.filter((c) => {
      if (expiryFilter !== "ALL" && c.expiry !== expiryFilter) return false;
      if (c.optionType === "C" && !showCalls) return false;
      if (c.optionType === "P" && !showPuts) return false;
      return true;
    });
  }, [contracts, expiryFilter, showCalls, showPuts]);

  const progressive = filtered.slice(0, visibleCount);

  async function loadChain(force = false) {
    setStatus("Fetching Deribit");
    onSymbolChange(currency);
    try {
      const res = await fetch(
        `/api/options/chain?currency=${currency}${force ? "&force=1" : ""}`,
      );
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setContracts(data.contracts || []);
      setFromCache(Boolean(data.fromCache));
      setVisibleCount(40);
      setStatus(
        `● LIVE ${currency} | ${(data.contracts || []).length} contracts | ${
          data.fromCache ? "cache" : "api"
        }`,
      );
      // progressive reveal
      let n = 40;
      const tick = () => {
        n = Math.min(n + 40, (data.contracts || []).length);
        setVisibleCount(n);
        if (n < (data.contracts || []).length) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);

      const und = data.contracts?.[0]?.underlyingPrice;
      if (und) {
        setSpot(und);
        setStrike(Math.round(und / 1000) * 1000);
      }
    } catch (e) {
      setStatus(`Error: ${e}`);
    }
  }

  function exportCsv() {
    const header = [
      "instrument",
      "expiry",
      "strike",
      "type",
      "mark",
      "iv",
      "delta",
      "gamma",
      "theta",
      "vega",
    ];
    const rows = filtered.map((c) =>
      [
        c.instrument,
        c.expiry,
        c.strike,
        c.optionType,
        c.markPrice,
        c.iv,
        c.delta,
        c.gamma,
        c.theta,
        c.vega,
      ].join(","),
    );
    const blob = new Blob([[header.join(","), ...rows].join("\n")], {
      type: "text/csv",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `options_${currency}_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const smile = useMemo(() => {
    const near = filtered.filter((c) => c.optionType === "C" && c.iv != null);
    const byStrike = near
      .slice()
      .sort((a, b) => a.strike - b.strike)
      .slice(0, 80);
    return {
      x: byStrike.map((c) => c.strike),
      y: byStrike.map((c) => (c.iv || 0) * 100),
    };
  }, [filtered]);

  const term = useMemo(() => {
    const map = new Map<string, number[]>();
    for (const c of filtered) {
      if (c.iv == null) continue;
      const arr = map.get(c.expiry) || [];
      arr.push(c.iv);
      map.set(c.expiry, arr);
    }
    const xs = Array.from(map.keys()).sort();
    return {
      x: xs,
      y: xs.map((e) => {
        const arr = map.get(e)!;
        return (arr.reduce((a, b) => a + b, 0) / arr.length) * 100;
      }),
    };
  }, [filtered]);

  const surface = useMemo(() => {
    const calls = filtered.filter((c) => c.optionType === "C" && c.iv != null);
    return {
      x: calls.map((c) => c.strike),
      y: calls.map((c) => c.expiry),
      z: calls.map((c) => (c.iv || 0) * 100),
    };
  }, [filtered]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-wrap items-center gap-2 border-b border-[#333] bg-[#0a0a0a] px-3 py-2">
        <select
          value={currency}
          onChange={(e) => onSymbolChange(e.target.value)}
          className="rounded border border-[#ff6600] bg-black px-2 py-1 text-[#ff8800]"
        >
          <option value="BTC">BTC</option>
          <option value="ETH">ETH</option>
        </select>
        <button
          type="button"
          onClick={() => loadChain(false)}
          className="rounded bg-[#ff6600] px-3 py-1 text-xs font-bold text-black"
        >
          LIVE MODE
        </button>
        <button
          type="button"
          onClick={() => loadChain(true)}
          className="rounded border border-[#ff6600] px-3 py-1 text-xs text-[#ff8800]"
        >
          Refresh
        </button>
        <button
          type="button"
          onClick={exportCsv}
          disabled={!filtered.length}
          className="rounded border border-[#444] px-3 py-1 text-xs text-[#aaa] disabled:opacity-40"
        >
          Export
        </button>
        <span className="font-mono text-xs text-[#888]">
          {status}
          {fromCache ? " | cached" : ""}
        </span>
        <div className="ml-auto flex gap-1">
          {(["chain", "vol", "strategy", "greeks"] as OptionsSub[]).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => onSubChange(s)}
              className={`rounded px-2 py-1 text-[10px] font-bold uppercase ${
                sub === s ? "bg-[#ff6600] text-black" : "bg-[#1a1a1a] text-[#888]"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {sub === "chain" && (
        <div className="grid flex-1 gap-3 p-3 lg:grid-cols-[200px_1fr]">
          <div className="space-y-2 rounded border border-[#333] p-3 text-xs">
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={showCalls} onChange={(e) => setShowCalls(e.target.checked)} />
              Calls
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={showPuts} onChange={(e) => setShowPuts(e.target.checked)} />
              Puts
            </label>
            <label className="block">
              Expiry
              <select
                value={expiryFilter}
                onChange={(e) => setExpiryFilter(e.target.value)}
                className="mt-1 w-full rounded border border-[#444] bg-black px-2 py-1"
              >
                <option value="ALL">ALL</option>
                {expiries.map((e) => (
                  <option key={e} value={e}>
                    {e}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="overflow-auto rounded border border-[#333]">
            <table className="w-full font-mono text-[11px]">
              <thead className="sticky top-0 bg-[#1a1a1a] text-[#ff6600]">
                <tr>
                  {["Instrument", "Exp", "K", "Type", "Mark", "IV", "Δ", "Γ", "Θ", "Vega"].map(
                    (h) => (
                      <th key={h} className="p-2 text-left">
                        {h}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody>
                {progressive.map((c) => (
                  <tr key={c.instrument} className="border-t border-[#1a1a1a] hover:bg-[#111]">
                    <td className="p-2">{c.instrument}</td>
                    <td className="p-2">{c.expiry}</td>
                    <td className="p-2">{c.strike}</td>
                    <td className="p-2">{c.optionType}</td>
                    <td className="p-2">{c.markPrice?.toFixed?.(4) ?? "-"}</td>
                    <td className="p-2">{c.iv != null ? (c.iv * 100).toFixed(1) : "-"}</td>
                    <td className="p-2">{c.delta?.toFixed?.(3) ?? "-"}</td>
                    <td className="p-2">{c.gamma?.toFixed?.(5) ?? "-"}</td>
                    <td className="p-2">{c.theta?.toFixed?.(4) ?? "-"}</td>
                    <td className="p-2">{c.vega?.toFixed?.(4) ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!contracts.length && (
              <p className="p-6 text-sm text-[#666]">Click LIVE MODE to load Deribit chain.</p>
            )}
          </div>
        </div>
      )}

      {sub === "vol" && (
        <div className="grid gap-4 p-4 lg:grid-cols-2">
          <ChartCard title="IV Smile (calls)">
            <Plot
              data={[{ x: smile.x, y: smile.y, type: "scatter", mode: "lines+markers", line: { color: "#ff6600" } }]}
              layout={plotLayout("Strike", "IV %")}
              config={{ displayModeBar: false }}
              style={{ width: "100%", height: 320 }}
            />
          </ChartCard>
          <ChartCard title="Term Structure">
            <Plot
              data={[{ x: term.x, y: term.y, type: "scatter", mode: "lines+markers", line: { color: "#ff9500" } }]}
              layout={plotLayout("Expiry", "Avg IV %")}
              config={{ displayModeBar: false }}
              style={{ width: "100%", height: 320 }}
            />
          </ChartCard>
          <div className="lg:col-span-2">
            <ChartCard title="3D Volatility Surface">
              <Plot
                data={[
                  {
                    x: surface.x,
                    y: surface.y,
                    z: surface.z,
                    type: "scatter3d",
                    mode: "markers",
                    marker: { size: 3, color: surface.z, colorscale: "Hot" },
                  },
                ]}
                layout={{
                  ...plotLayout("Strike", "Expiry"),
                  scene: {
                    xaxis: { title: "Strike", color: "#aaa" },
                    yaxis: { title: "Expiry", color: "#aaa" },
                    zaxis: { title: "IV %", color: "#aaa" },
                    bgcolor: "#000",
                  },
                  height: 480,
                }}
                config={{ displayModeBar: false }}
                style={{ width: "100%", height: 480 }}
              />
            </ChartCard>
          </div>
        </div>
      )}

      {sub === "strategy" && (
        <div className="grid max-w-xl gap-3 p-4">
          <h3 className="font-bold text-[#ff6600]">Black-Scholes Pricer</h3>
          {[
            ["Spot", spot, setSpot],
            ["Strike", strike, setStrike],
            ["DTE", dte, setDte],
            ["IV (decimal)", iv, setIv],
          ].map(([label, val, set]) => (
            <label key={label as string} className="text-xs text-[#888]">
              {label as string}
              <input
                type="number"
                step="any"
                value={val as number}
                onChange={(e) => (set as (n: number) => void)(Number(e.target.value))}
                className="mt-1 w-full rounded border border-[#444] bg-black px-2 py-1 font-mono text-[#ff8800]"
              />
            </label>
          ))}
          <select
            value={optType}
            onChange={(e) => setOptType(e.target.value as "call" | "put")}
            className="rounded border border-[#444] bg-black px-2 py-1"
          >
            <option value="call">Call</option>
            <option value="put">Put</option>
          </select>
          <pre className="rounded border border-[#ff6600] bg-[#050505] p-3 font-mono text-xs text-[#ddd]">
            {pricerText}
          </pre>
        </div>
      )}

      {sub === "greeks" && (
        <div className="p-4">
          <div className="rounded border-2 border-[#ff6600] p-4">
            <h3 className="mb-2 font-bold text-[#ff6600]">Greeks Monitor</h3>
            <p className="mb-3 text-sm text-[#888]">
              Minimal positions board from the loaded chain (top absolute delta).
            </p>
            <table className="w-full font-mono text-xs">
              <thead className="text-[#ff6600]">
                <tr>
                  <th className="p-2 text-left">Instrument</th>
                  <th className="p-2 text-right">Delta</th>
                  <th className="p-2 text-right">Gamma</th>
                  <th className="p-2 text-right">Vega</th>
                  <th className="p-2 text-right">Theta</th>
                </tr>
              </thead>
              <tbody>
                {[...filtered]
                  .filter((c) => c.delta != null)
                  .sort((a, b) => Math.abs(b.delta!) - Math.abs(a.delta!))
                  .slice(0, 25)
                  .map((c) => (
                    <tr key={c.instrument} className="border-t border-[#222]">
                      <td className="p-2">{c.instrument}</td>
                      <td className="p-2 text-right">{c.delta?.toFixed(3)}</td>
                      <td className="p-2 text-right">{c.gamma?.toFixed(5)}</td>
                      <td className="p-2 text-right">{c.vega?.toFixed(4)}</td>
                      <td className="p-2 text-right">{c.theta?.toFixed(4)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded border border-[#ff6600] bg-black">
      <div className="border-b border-[#ff6600] px-3 py-2 text-xs font-bold text-[#ff6600]">
        {title}
      </div>
      <div className="p-2">{children}</div>
    </div>
  );
}

function plotLayout(xTitle: string, yTitle: string) {
  return {
    paper_bgcolor: "#000",
    plot_bgcolor: "#000",
    font: { color: "#aaa", size: 11 },
    margin: { t: 20, r: 20, b: 40, l: 50 },
    xaxis: { title: xTitle, gridcolor: "#222" },
    yaxis: { title: yTitle, gridcolor: "#222" },
    height: 320,
  };
}
