"use client";

import { useEffect, useMemo, useState } from "react";
import type { BacktestResult, SignalsResponse } from "@/lib/types";
import { apiGet, apiPost } from "@/lib/api";
import {
  loadWatchlist,
  saveWatchlist,
} from "@/lib/portfolio/store";
import { CandleChart } from "@/components/charts/CandleChart";
import { EquityChart } from "@/components/charts/EquityChart";
import { RangeChips } from "@/components/charts/RangeChips";
import type { ChartRange } from "@/components/charts/chartTheme";
import { useOhlcv } from "@/components/charts/useOhlcv";

export function SignalsTab({
  symbol,
  onSymbolChange,
}: {
  symbol: string;
  onSymbolChange: (s: string) => void;
}) {
  const [localSym, setLocalSym] = useState(symbol);
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [data, setData] = useState<SignalsResponse | null>(null);
  const [batch, setBatch] = useState<SignalsResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [replay, setReplay] = useState<BacktestResult | null>(null);
  const [log, setLog] = useState("Rules-based signals. Not investment advice.");
  const [chartRange, setChartRange] = useState<ChartRange>("1Y");
  const { bars, sourceNote, loading: chartLoading } = useOhlcv(
    symbol,
    chartRange,
  );

  const markers = useMemo(
    () =>
      (data?.signals || []).map((s) => ({
        date: s.asOf.slice(0, 10),
        position:
          s.side === "bearish"
            ? ("aboveBar" as const)
            : ("belowBar" as const),
        shape:
          s.side === "bearish"
            ? ("arrowDown" as const)
            : s.side === "bullish"
              ? ("arrowUp" as const)
              : ("circle" as const),
        color:
          s.side === "bearish"
            ? "#ef4444"
            : s.side === "bullish"
              ? "#22c55e"
              : "#ff6600",
        text: s.label.slice(0, 12),
      })),
    [data],
  );

  useEffect(() => setLocalSym(symbol), [symbol]);
  useEffect(() => {
    setWatchlist(loadWatchlist());
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      setReplay(null);
      try {
        const res = await apiGet<{ data: SignalsResponse }>(
          `/api/v1/technicals/signals?symbol=${encodeURIComponent(symbol)}`,
        );
        if (!cancelled) {
          setData(res.data);
          setLog(
            `${res.data.symbol} score ${res.data.score >= 0 ? "+" : ""}${res.data.score} | ${res.data.signals.length} signals | as of ${res.data.asOf}`,
          );
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e));
          setData(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [symbol]);

  function persistWatch(next: string[]) {
    setWatchlist(next);
    saveWatchlist(next);
  }

  function addToWatch(sym: string) {
    const s = sym.trim().toUpperCase();
    if (!s) return;
    if (watchlist.includes(s)) return;
    persistWatch([...watchlist, s]);
  }

  async function scanWatchlist() {
    if (!watchlist.length) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiPost<{ results: SignalsResponse[] }>(
        "/api/signals/batch",
        { symbols: watchlist },
      );
      setBatch(res.results || []);
      setLog(`Scanned ${res.results?.length ?? 0} watchlist symbols`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function runReplay(strategy: "MACD" | "RSI") {
    setLoading(true);
    try {
      const start = new Date();
      start.setFullYear(start.getFullYear() - 2);
      const res = await apiPost<BacktestResult>("/api/backtest", {
        symbol,
        start: start.toISOString().slice(0, 10),
        strategy,
        initialCapital: 10000,
        commission: 0.001,
      });
      setReplay(res);
      setLog(
        `Replay ${strategy}: return ${res.totalReturn.toFixed(1)}% | DD ${res.maxDrawdown.toFixed(1)}% | trades ${res.numTrades}`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const sideColor = (side: string) =>
    side === "bullish"
      ? "text-emerald-400 border-emerald-700"
      : side === "bearish"
        ? "text-red-400 border-red-800"
        : "text-[#aaa] border-[#333]";

  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-xs text-[#888]">
          Symbol
          <input
            value={localSym}
            onChange={(e) => setLocalSym(e.target.value.toUpperCase())}
            onKeyDown={(e) => {
              if (e.key === "Enter") onSymbolChange(localSym.trim().toUpperCase());
            }}
            className="mt-1 block rounded border border-[#ff6600] bg-black px-2 py-1 font-mono text-sm text-[#ff8800]"
          />
        </label>
        <button
          type="button"
          className="rounded bg-[#ff6600] px-3 py-2 text-sm font-bold text-black"
          onClick={() => onSymbolChange(localSym.trim().toUpperCase())}
        >
          Analyze
        </button>
        <button
          type="button"
          className="rounded border border-[#ff6600] px-3 py-2 text-sm text-[#ff8800]"
          onClick={() => addToWatch(symbol)}
        >
          + Watch
        </button>
        <button
          type="button"
          className="rounded border border-[#444] px-3 py-2 text-sm text-[#ccc]"
          onClick={scanWatchlist}
          disabled={loading}
        >
          Scan watchlist
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {watchlist.map((w) => (
          <button
            key={w}
            type="button"
            onClick={() => onSymbolChange(w)}
            className={`rounded border px-2 py-1 font-mono text-xs ${
              w === symbol
                ? "border-[#ff6600] bg-[#1a0a00] text-[#ff8800]"
                : "border-[#333] text-[#888] hover:border-[#666]"
            }`}
          >
            {w}
            <span
              className="ml-2 text-[#555] hover:text-red-400"
              onClick={(e) => {
                e.stopPropagation();
                persistWatch(watchlist.filter((x) => x !== w));
              }}
            >
              ×
            </span>
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}
      {loading && <p className="text-sm text-[#666]">Loading</p>}

      {data && (
        <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
          <div className="space-y-3">
            <div className="flex flex-wrap items-baseline gap-4 border border-[#333] bg-[#0a0a0a] p-4">
              <div>
                <div className="text-xs text-[#666]">Score</div>
                <div
                  className={`font-mono text-3xl font-bold ${
                    data.score >= 0 ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {data.score >= 0 ? "+" : ""}
                  {data.score}
                </div>
              </div>
              <div>
                <div className="text-xs text-[#666]">Price</div>
                <div className="font-mono text-xl text-[#ff9500]">
                  {data.price.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                  })}
                </div>
              </div>
              <div>
                <div className="text-xs text-[#666]">~1M</div>
                <div className="font-mono text-lg text-[#ccc]">
                  {data.changePct1m != null
                    ? `${data.changePct1m.toFixed(1)}%`
                    : "-"}
                </div>
              </div>
            </div>

            <div className="border border-[#333] bg-[#0a0a0a] p-3">
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-[10px] font-bold uppercase tracking-wide text-[#ff6600]">
                  Price + signal markers
                </h3>
                <RangeChips value={chartRange} onChange={setChartRange} />
              </div>
              <CandleChart
                bars={bars}
                height={300}
                smaPeriods={[20, 50]}
                markers={markers}
                sourceNote={
                  sourceNote ||
                  (chartLoading ? "Loading" : "Yahoo / Coinbase OHLCV")
                }
              />
            </div>

            <div className="grid gap-2 sm:grid-cols-2">
              {data.signals.length === 0 && (
                <p className="text-sm text-[#666]">No active rule triggers.</p>
              )}
              {data.signals.map((s) => (
                <div
                  key={s.id}
                  className={`rounded border bg-[#050505] p-3 ${sideColor(s.side)}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-bold text-[#eee]">{s.label}</span>
                    <span className="font-mono text-[10px] uppercase opacity-80">
                      {s.side} | {(s.strength * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="mt-1 font-mono text-xs text-[#999]">{s.detail}</p>
                  {s.replayStrategy && (
                    <button
                      type="button"
                      className="mt-2 text-xs text-[#ff8800] underline"
                      onClick={() => runReplay(s.replayStrategy!)}
                    >
                      Replay {s.replayStrategy} (2y)
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <aside className="space-y-3 border border-[#333] bg-[#0a0a0a] p-3">
            <h3 className="text-xs font-bold uppercase tracking-wide text-[#ff6600]">
              Watchlist scan
            </h3>
            {batch.length === 0 && (
              <p className="text-xs text-[#666]">Run Scan watchlist to compare.</p>
            )}
            <ul className="space-y-2">
              {[...batch]
                .sort((a, b) => b.score - a.score)
                .map((b) => (
                  <li key={b.symbol}>
                    <button
                      type="button"
                      className="flex w-full items-center justify-between font-mono text-xs hover:text-[#ff8800]"
                      onClick={() => onSymbolChange(b.symbol)}
                    >
                      <span>{b.symbol}</span>
                      <span
                        className={
                          b.score >= 0 ? "text-emerald-400" : "text-red-400"
                        }
                      >
                        {b.score >= 0 ? "+" : ""}
                        {b.score}
                      </span>
                    </button>
                  </li>
                ))}
            </ul>
            {replay && (
              <div className="border-t border-[#222] pt-3 text-xs text-[#aaa]">
                <div className="text-[#ff6600]">Last replay</div>
                <div className="font-mono">
                  {replay.strategy}: {replay.totalReturn.toFixed(1)}% | Sharpe{" "}
                  {Number(replay.sharpeRatio).toFixed(2)}
                </div>
                {replay.equityCurve?.length > 0 && (
                  <div className="mt-2">
                    <EquityChart data={replay.equityCurve} height={140} />
                  </div>
                )}
              </div>
            )}
          </aside>
        </div>
      )}

      <p className="font-mono text-[11px] text-[#666]">{log}</p>
    </div>
  );
}
