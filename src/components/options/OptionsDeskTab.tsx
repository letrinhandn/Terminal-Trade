"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import type { OptionContract } from "@/lib/types";
import { apiGet } from "@/lib/api";

const Plot = dynamic(
  () => import("react-plotly.js").then((m) => m.default),
  {
    ssr: false,
    loading: () => (
      <div className="p-4 text-sm text-[#666]">Loading chart</div>
    ),
  },
);

type ChainRes = {
  underlying: string;
  underlyingPrice: number | null;
  source: "deribit" | "yahoo" | string;
  unit: "coin" | "usd" | string;
  note?: string;
  expirations?: string[];
  contracts: OptionContract[];
  fromCache?: boolean;
  error?: string;
};

function plotLayout(xTitle: string, yTitle: string) {
  return {
    paper_bgcolor: "#000",
    plot_bgcolor: "#000",
    font: { color: "#aaa", size: 11 },
    margin: { t: 20, r: 20, b: 40, l: 50 },
    xaxis: { title: xTitle, gridcolor: "#222" },
    yaxis: { title: yTitle, gridcolor: "#222" },
    height: 280,
  };
}

function isCryptoSym(s: string): "BTC" | "ETH" | null {
  const u = s.trim().toUpperCase();
  if (u === "BTC" || u.startsWith("BTC")) return "BTC";
  if (u === "ETH" || u.startsWith("ETH")) return "ETH";
  return null;
}

function fmtPx(v: number | null | undefined, unit: string) {
  if (v == null || !Number.isFinite(v)) return "-";
  if (unit === "coin") {
    if (v === 0) return "0";
    if (Math.abs(v) < 0.001) return v.toExponential(2);
    return v.toFixed(4);
  }
  return v.toFixed(2);
}

function fmtIv(iv: number | null | undefined) {
  if (iv == null || !Number.isFinite(iv)) return "-";
  return `${(iv * 100).toFixed(1)}%`;
}

export function OptionsDeskTab({
  symbol,
  onStatus,
}: {
  symbol: string;
  onStatus?: (s: string) => void;
}) {
  const cryptoFromSym = isCryptoSym(symbol);
  const [mode, setMode] = useState<"crypto" | "equity">(
    cryptoFromSym ? "crypto" : "equity",
  );
  const [currency, setCurrency] = useState<"BTC" | "ETH">(
    cryptoFromSym || "BTC",
  );
  const [equitySym, setEquitySym] = useState(
    cryptoFromSym ? "AAPL" : symbol.toUpperCase() || "AAPL",
  );
  const [contracts, setContracts] = useState<OptionContract[]>([]);
  const [meta, setMeta] = useState<Omit<ChainRes, "contracts"> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [expiry, setExpiry] = useState<string>("");
  const [showCalls, setShowCalls] = useState(true);
  const [showPuts, setShowPuts] = useState(true);

  useEffect(() => {
    const c = isCryptoSym(symbol);
    if (c) {
      setMode("crypto");
      setCurrency(c);
    } else if (symbol.trim()) {
      setMode("equity");
      setEquitySym(symbol.toUpperCase());
    }
  }, [symbol]);

  const queryKey = mode === "crypto" ? currency : equitySym;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const q =
          mode === "crypto"
            ? `/api/options/chain?currency=${currency}&force=1`
            : `/api/options/chain?symbol=${encodeURIComponent(equitySym)}&force=1`;
        const data = await apiGet<ChainRes>(q);
        if (cancelled) return;
        setContracts(data.contracts || []);
        setMeta({
          underlying: data.underlying,
          underlyingPrice: data.underlyingPrice,
          source: data.source,
          unit: data.unit,
          note: data.note,
          expirations: data.expirations,
          fromCache: data.fromCache,
        });
        const exps = Array.from(
          new Set((data.contracts || []).map((c) => c.expiry)),
        ).sort();
        setExpiry((prev) => (prev && exps.includes(prev) ? prev : exps[0] || ""));
        onStatus?.(
          `Options ${data.underlying} ${data.source} ${data.contracts?.length ?? 0} contracts`,
        );
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e));
          setContracts([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [mode, queryKey, currency, equitySym, onStatus]);

  const expiries = useMemo(
    () => Array.from(new Set(contracts.map((c) => c.expiry))).sort(),
    [contracts],
  );

  const filtered = useMemo(() => {
    return contracts.filter((c) => {
      if (expiry && c.expiry !== expiry) return false;
      if (c.optionType === "C" && !showCalls) return false;
      if (c.optionType === "P" && !showPuts) return false;
      return true;
    });
  }, [contracts, expiry, showCalls, showPuts]);

  const unit = meta?.unit || "usd";
  const und = meta?.underlyingPrice;

  const smile = useMemo(() => {
    const calls = filtered
      .filter((c) => c.optionType === "C" && c.iv != null)
      .slice()
      .sort((a, b) => a.strike - b.strike);
    return {
      x: calls.map((c) => c.strike),
      y: calls.map((c) => (c.iv || 0) * 100),
    };
  }, [filtered]);

  const term = useMemo(() => {
    const map = new Map<string, number[]>();
    for (const c of contracts) {
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
  }, [contracts]);

  const tableRows = filtered.slice(0, 120);
  const greeksCount = contracts.filter((c) => c.delta != null).length;

  return (
    <div className="space-y-3 p-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-[#ff9500]">Options</h2>
          <p className="max-w-2xl text-xs text-[#666]">
            {meta?.note ||
              "Live chains: Deribit crypto (BTC/ETH) or Yahoo equity. Mark units differ by source."}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 font-mono text-[11px]">
          <button
            type="button"
            className={`border px-2 py-1 ${mode === "crypto" ? "border-[#ff6600] text-[#ff8800]" : "border-[#333] text-[#888]"}`}
            onClick={() => setMode("crypto")}
          >
            CRYPTO
          </button>
          <button
            type="button"
            className={`border px-2 py-1 ${mode === "equity" ? "border-[#ff6600] text-[#ff8800]" : "border-[#333] text-[#888]"}`}
            onClick={() => setMode("equity")}
          >
            EQUITY
          </button>
          {mode === "crypto" ? (
            <>
              {(["BTC", "ETH"] as const).map((c) => (
                <button
                  key={c}
                  type="button"
                  className={`border px-2 py-1 ${currency === c ? "border-[#ff6600] text-[#ff8800]" : "border-[#333] text-[#888]"}`}
                  onClick={() => setCurrency(c)}
                >
                  {c}
                </button>
              ))}
            </>
          ) : (
            <input
              className="w-24 border border-[#333] bg-black px-2 py-1 uppercase text-[#ccc]"
              value={equitySym}
              onChange={(e) => setEquitySym(e.target.value.toUpperCase())}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  setEquitySym((s) => s.trim().toUpperCase());
                }
              }}
              placeholder="AAPL"
            />
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 border border-[#222] bg-[#0a0a0a] px-3 py-2 font-mono text-[10px] text-[#888]">
        <span className="text-[#ff8800]">
          {meta?.underlying || queryKey}
        </span>
        <span>
          Spot{" "}
          {und != null
            ? unit === "coin"
              ? und.toFixed(1)
              : `$${und.toFixed(2)}`
            : "-"}
        </span>
        <span>{meta?.source || "-"}</span>
        <span>{contracts.length} contracts</span>
        <span>Greeks {greeksCount}</span>
        <span>{loading ? "Loading" : "Live"}</span>
        <label className="ml-auto flex items-center gap-1">
          Expiry
          <select
            className="border border-[#333] bg-black px-1 py-0.5 text-[#ccc]"
            value={expiry}
            onChange={(e) => setExpiry(e.target.value)}
          >
            {expiries.map((e) => (
              <option key={e} value={e}>
                {e}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1">
          <input
            type="checkbox"
            checked={showCalls}
            onChange={(e) => setShowCalls(e.target.checked)}
          />
          Calls
        </label>
        <label className="flex items-center gap-1">
          <input
            type="checkbox"
            checked={showPuts}
            onChange={(e) => setShowPuts(e.target.checked)}
          />
          Puts
        </label>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="grid gap-3 lg:grid-cols-2">
        <div className="border border-[#333] bg-[#0a0a0a]">
          <div className="border-b border-[#222] px-3 py-1.5 text-[10px] font-bold uppercase tracking-wide text-[#ff6600]">
            IV smile calls {expiry || ""}
          </div>
          <div className="p-2">
            {smile.x.length ? (
              <Plot
                data={[
                  {
                    x: smile.x,
                    y: smile.y,
                    type: "scatter",
                    mode: "lines+markers",
                    line: { color: "#ff6600" },
                    marker: { size: 4 },
                  },
                ]}
                layout={plotLayout("Strike", "IV %")}
                config={{ displayModeBar: false }}
                style={{ width: "100%", height: 280 }}
              />
            ) : (
              <p className="p-6 text-center text-xs text-[#555]">
                No IV for this expiry
              </p>
            )}
          </div>
        </div>
        <div className="border border-[#333] bg-[#0a0a0a]">
          <div className="border-b border-[#222] px-3 py-1.5 text-[10px] font-bold uppercase tracking-wide text-[#ff6600]">
            Term structure avg IV
          </div>
          <div className="p-2">
            {term.x.length ? (
              <Plot
                data={[
                  {
                    x: term.x,
                    y: term.y,
                    type: "scatter",
                    mode: "lines+markers",
                    line: { color: "#ff9500" },
                    marker: { size: 4 },
                  },
                ]}
                layout={plotLayout("Expiry", "Avg IV %")}
                config={{ displayModeBar: false }}
                style={{ width: "100%", height: 280 }}
              />
            ) : (
              <p className="p-6 text-center text-xs text-[#555]">No term data</p>
            )}
          </div>
        </div>
      </div>

      <div className="overflow-x-auto border border-[#333]">
        <table className="w-full min-w-[900px] font-mono text-[11px]">
          <thead className="bg-[#111] text-[#888]">
            <tr>
              {[
                "Instrument",
                "Expiry",
                "K",
                "Type",
                unit === "coin" ? "Mark (coin)" : "Last",
                "Bid",
                "Ask",
                "IV",
                "Δ",
                "OI",
                "Vol",
              ].map((h) => (
                <th key={h} className="p-2 text-left font-normal">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && !tableRows.length ? (
              <tr>
                <td colSpan={11} className="p-4 text-[#666]">
                  Loading chain
                </td>
              </tr>
            ) : null}
            {!loading && !tableRows.length ? (
              <tr>
                <td colSpan={11} className="p-4 text-[#666]">
                  No contracts for filter
                </td>
              </tr>
            ) : null}
            {tableRows.map((c) => (
              <tr key={c.instrument} className="border-t border-[#222]">
                <td className="p-2 text-[#ff8800]">{c.instrument}</td>
                <td className="p-2">{c.expiry}</td>
                <td className="p-2">{c.strike}</td>
                <td className="p-2">{c.optionType}</td>
                <td className="p-2">{fmtPx(c.markPrice, unit)}</td>
                <td className="p-2">{fmtPx(c.bid, unit)}</td>
                <td className="p-2">{fmtPx(c.ask, unit)}</td>
                <td className="p-2">{fmtIv(c.iv)}</td>
                <td className="p-2">
                  {c.delta != null ? c.delta.toFixed(3) : "-"}
                </td>
                <td className="p-2">
                  {c.openInterest != null ? c.openInterest : "-"}
                </td>
                <td className="p-2">{c.volume != null ? c.volume : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
