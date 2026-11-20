"use client";

import { useEffect, useState } from "react";
import type { IdeaRow, IdeasFilter } from "@/lib/types";
import { apiGet } from "@/lib/api";
import {
  addHolding,
  loadPortfolio,
  loadWatchlist,
  savePortfolio,
  saveWatchlist,
} from "@/lib/portfolio/store";

type IdeasPayload = {
  ideas: IdeaRow[];
  disclaimer?: string;
  generatedAt?: string;
  error?: string;
};

export function IdeasTab({
  symbol,
  onSymbolChange,
  onGoPortfolio,
}: {
  symbol: string;
  onSymbolChange: (s: string) => void;
  onGoPortfolio?: () => void;
}) {
  const [kind, setKind] = useState<IdeasFilter>("all");
  const [ideas, setIdeas] = useState<IdeaRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [log, setLog] = useState(
    "Screener ranks a curated universe by multi-signal score.",
  );

  async function load(force = false) {
    setLoading(true);
    setError(null);
    try {
      const q =
        kind === "all"
          ? "all"
          : kind === "stocks"
            ? "stock"
            : kind === "etfs"
              ? "etf"
              : "crypto";
      const res = await apiGet<IdeasPayload>(
        `/api/ideas?kind=${q}${force ? "&force=1" : ""}`,
      );
      setIdeas(res.ideas || []);
      setLog(
        `${res.ideas?.length ?? 0} ideas | ${res.generatedAt ? new Date(res.generatedAt).toLocaleString() : "cached"} | ${res.disclaimer || ""}`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind]);

  function watch(sym: string) {
    const list = loadWatchlist();
    if (!list.includes(sym)) saveWatchlist([...list, sym]);
    setLog(`Added ${sym} to watchlist`);
  }

  function addPaper(row: IdeaRow) {
    const p = loadPortfolio();
    const next = addHolding(p, {
      symbol: row.symbol,
      qty: 1,
      costBasis: row.price,
      note: `From Ideas score ${row.score}`,
    });
    savePortfolio(next);
    setLog(`Paper lot: 1 ${row.symbol} @ ${row.price.toFixed(2)}`);
    onGoPortfolio?.();
  }

  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-[#ff9500]">Ideas</h2>
          <p className="text-xs text-[#666]">
            Ranked research candidates. Not buy or sell advice.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {(
            [
              ["all", "All"],
              ["stocks", "Stocks"],
              ["etfs", "ETFs"],
              ["crypto", "Crypto"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => setKind(id)}
              className={`rounded px-3 py-2 text-xs font-bold ${
                kind === id
                  ? "bg-[#ff6600] text-black"
                  : "border border-[#333] text-[#888]"
              }`}
            >
              {label}
            </button>
          ))}
          <button
            type="button"
            className="rounded border border-[#ff6600] px-3 py-2 text-xs text-[#ff8800]"
            onClick={() => void load(true)}
            disabled={loading}
          >
            Rescreen
          </button>
        </div>
      </div>

      {loading && (
        <p className="text-sm text-[#666]">
          Screening Yahoo universe. First run may take a minute.
        </p>
      )}
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="overflow-x-auto border border-[#333]">
        <table className="w-full min-w-[800px] text-left text-sm">
          <thead className="bg-[#111] font-mono text-[11px] text-[#888]">
            <tr>
              <th className="p-2">Score</th>
              <th className="p-2">Symbol</th>
              <th className="p-2">Kind</th>
              <th className="p-2">Price</th>
              <th className="p-2">1D%</th>
              <th className="p-2">1M%</th>
              <th className="p-2">Top signals</th>
              <th className="p-2">Risk</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {ideas.map((row) => (
              <tr
                key={row.symbol}
                className={`border-t border-[#222] font-mono text-xs ${
                  row.symbol === symbol ? "bg-[#1a0a00]" : ""
                }`}
              >
                <td
                  className={`p-2 text-base font-bold ${
                    row.score >= 0 ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {row.score >= 0 ? "+" : ""}
                  {row.score}
                </td>
                <td className="p-2">
                  <button
                    type="button"
                    className="text-[#ff8800] hover:underline"
                    onClick={() => onSymbolChange(row.symbol)}
                  >
                    {row.symbol}
                  </button>
                  <div className="text-[10px] text-[#555]">{row.name}</div>
                </td>
                <td className="p-2 uppercase text-[#666]">{row.kind}</td>
                <td className="p-2 text-[#ccc]">
                  {row.price.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                  })}
                </td>
                <td
                  className={`p-2 ${row.changePct >= 0 ? "text-emerald-400" : "text-red-400"}`}
                >
                  {row.changePct.toFixed(2)}%
                </td>
                <td className="p-2 text-[#aaa]">
                  {row.changePct1m != null
                    ? `${row.changePct1m.toFixed(1)}%`
                    : "-"}
                </td>
                <td className="p-2 text-[10px] text-[#999]">
                  {row.signals
                    .slice(0, 2)
                    .map((s) => s.label)
                    .join(" | ") || "-"}
                </td>
                <td className="p-2 text-[10px] text-amber-500/90">
                  {row.riskFlags.join(", ") || "-"}
                </td>
                <td className="p-2 space-x-2 whitespace-nowrap">
                  <button
                    type="button"
                    className="text-[#ff8800] underline"
                    onClick={() => watch(row.symbol)}
                  >
                    Watch
                  </button>
                  <button
                    type="button"
                    className="text-emerald-400 underline"
                    onClick={() => addPaper(row)}
                  >
                    + Portfolio
                  </button>
                </td>
              </tr>
            ))}
            {!loading && !ideas.length && (
              <tr>
                <td colSpan={9} className="p-6 text-center text-[#666]">
                  No ideas returned. Try Rescreen.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="font-mono text-[11px] text-[#666]">{log}</p>
    </div>
  );
}
