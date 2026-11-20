"use client";

import { useEffect, useMemo, useState } from "react";
import type { BacktestResult, BacktestSub } from "@/lib/types";
import { STRATEGY_IDS, type StrategyId } from "@/lib/strategies/builtins";
import { EquityChart } from "@/components/charts/EquityChart";
import { apiGet, apiPost } from "@/lib/api";

const STORAGE_KEY = "tt_custom_strategies_v1";

type CustomStrategy = { id: string; name: string; code: string };

const DEFAULT_TEMPLATE = `// Custom strategy - must return bars with { signal: 1|-1|0 }
// bars: Array<{ date, open, high, low, close, volume }>
function run(bars) {
  return bars.map((b, i) => ({
    b,
    signal: i > 0 && b.close > bars[i-1].close * 1.02 ? 1
          : i > 0 && b.close < bars[i-1].close * 0.98 ? -1
          : 0,
  }));
}
`;

export function BacktestTab({
  symbol,
  sub,
  onSymbolChange,
  onSubChange,
}: {
  symbol: string;
  sub: BacktestSub;
  onSymbolChange: (s: string) => void;
  onSubChange: (s: BacktestSub) => void;
}) {
  const [localSym, setLocalSym] = useState(symbol);
  const [strategy, setStrategy] = useState<StrategyId>("MACD");
  const [start, setStart] = useState("2023-01-01");
  const [end, setEnd] = useState("");
  const [capital, setCapital] = useState(10000);
  const [commission, setCommission] = useState(0.001);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState("Ready");
  const [customs, setCustoms] = useState<CustomStrategy[]>([]);
  const [editorName, setEditorName] = useState("MyStrategy");
  const [editorCode, setEditorCode] = useState(DEFAULT_TEMPLATE);

  useEffect(() => setLocalSym(symbol), [symbol]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setCustoms(JSON.parse(raw) as CustomStrategy[]);
    } catch {
      /* ignore */
    }
  }, []);

  const strategyLabels = useMemo(
    () => STRATEGY_IDS.map((id) => ({ id, label: id.replaceAll("_", " ") })),
    [],
  );

  async function runBacktest() {
    setBusy(true);
    setLog("Running");
    const sym = localSym.trim().toUpperCase();
    onSymbolChange(sym);
    try {
      const data = await apiPost<BacktestResult>("/api/backtest", {
        symbol: sym,
        start,
        end: end || undefined,
        strategy,
        initialCapital: capital,
        commission,
      });
      setResult(data);
      setLog(
        `Done: ${data.numTrades} trades | return ${data.totalReturn.toFixed(2)}% | Sharpe ${data.sharpeRatio.toFixed(2)}`,
      );
      onSubChange("run");
    } catch (e) {
      setLog(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setBusy(false);
    }
  }

  function saveCustom() {
    const next = [
      ...customs.filter((c) => c.name !== editorName),
      { id: editorName, name: editorName, code: editorCode },
    ];
    setCustoms(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setLog(`Saved custom strategy ${editorName} (runs in Web Worker locally)`);
  }

  async function testInWorker() {
    setLog("Testing custom strategy in Web Worker");
    try {
      const ohlcv = await apiGet<{ bars: unknown[] }>(
        `/api/ohlcv?symbol=${encodeURIComponent(localSym)}&start=${start}`,
      );
      const worker = new Worker(
        new URL("../../workers/strategyWorker.ts", import.meta.url),
      );
      const result = await new Promise<{
        ok: boolean;
        error?: string;
        bars?: { signal?: number }[];
      }>((resolve, reject) => {
        const timer = setTimeout(
          () => reject(new Error("Worker timeout")),
          15000,
        );
        worker.onmessage = (e) => {
          clearTimeout(timer);
          resolve(e.data);
        };
        worker.onerror = (e) => {
          clearTimeout(timer);
          reject(e.message ? new Error(e.message) : e);
        };
        worker.postMessage({ code: editorCode, bars: ohlcv.bars || [] });
      });
      worker.terminate();
      if (!result.ok) throw new Error(result.error || "Worker failed");
      const signals = (result.bars || []).filter((b) => b.signal).length;
      setLog(
        `Worker OK - ${(result.bars || []).length} bars, ${signals} non-zero signals`,
      );
    } catch (e) {
      setLog(`Worker error: ${e instanceof Error ? e.message : String(e)}`);
    }
  }

  function exportCsv() {
    if (!result) return;
    const rows = [
      ["metric", "value"],
      ...Object.entries(result.metrics).map(([k, v]) => [k, String(v)]),
    ];
    const csv = rows.map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `backtest_${result.symbol}_${result.strategy}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex gap-2 border-b border-[#333] bg-[#111] px-3 py-2">
        {(["run", "manager", "editor"] as BacktestSub[]).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSubChange(s)}
            className={`rounded px-3 py-1 text-xs font-bold uppercase ${
              sub === s ? "bg-[#ff6600] text-black" : "bg-[#1a1a1a] text-[#aaa]"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {sub === "run" && (
        <div className="grid gap-4 p-4 lg:grid-cols-[320px_1fr]">
          <div className="space-y-3 rounded border-2 border-[#ff6600] p-3">
            <Field label="Symbol">
              <input
                value={localSym}
                onChange={(e) => setLocalSym(e.target.value.toUpperCase())}
                className="w-full rounded border border-[#444] bg-black px-2 py-1 font-mono text-[#ff8800]"
              />
            </Field>
            <Field label="Strategy">
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value as StrategyId)}
                className="w-full rounded border border-[#444] bg-black px-2 py-1"
              >
                {strategyLabels.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Start">
              <input
                type="date"
                value={start}
                onChange={(e) => setStart(e.target.value)}
                className="w-full rounded border border-[#444] bg-black px-2 py-1"
              />
            </Field>
            <Field label="End (optional)">
              <input
                type="date"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
                className="w-full rounded border border-[#444] bg-black px-2 py-1"
              />
            </Field>
            <Field label="Capital">
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(Number(e.target.value))}
                className="w-full rounded border border-[#444] bg-black px-2 py-1"
              />
            </Field>
            <Field label="Commission">
              <input
                type="number"
                step="0.0001"
                value={commission}
                onChange={(e) => setCommission(Number(e.target.value))}
                className="w-full rounded border border-[#444] bg-black px-2 py-1"
              />
            </Field>
            <button
              type="button"
              disabled={busy}
              onClick={runBacktest}
              className="w-full rounded bg-[#ff6600] py-2 font-bold text-black disabled:opacity-50"
            >
              {busy ? "Running" : "RUN BACKTEST"}
            </button>
            <button
              type="button"
              disabled={!result}
              onClick={exportCsv}
              className="w-full rounded border border-[#ff6600] py-2 text-sm text-[#ff8800] disabled:opacity-40"
            >
              Export CSV
            </button>
            <p className="font-mono text-xs text-[#888]">{log}</p>
          </div>

          <div className="space-y-3">
            {result ? (
              <>
                <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
                  {Object.entries(result.metrics).map(([k, v]) => (
                    <div key={k} className="rounded border border-[#333] bg-[#0a0a0a] p-2">
                      <div className="text-[10px] uppercase text-[#888]">{k}</div>
                      <div className="font-mono text-[#ff9500]">{v}</div>
                    </div>
                  ))}
                </div>
                <div className="rounded border border-[#ff6600] p-2">
                  <EquityChart data={result.equityCurve} />
                </div>
                <div className="max-h-64 overflow-auto rounded border border-[#333]">
                  <table className="w-full font-mono text-xs">
                    <thead className="bg-[#1a1a1a] text-[#ff6600]">
                      <tr>
                        <th className="p-2 text-left">Entry</th>
                        <th className="p-2 text-left">Exit</th>
                        <th className="p-2 text-right">Return %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.trades.map((t, i) => (
                        <tr key={i} className="border-t border-[#222]">
                          <td className="p-2">{t.entryDate}</td>
                          <td className="p-2">{t.exitDate}</td>
                          <td
                            className={`p-2 text-right ${
                              t.returnPct >= 0 ? "text-emerald-400" : "text-red-400"
                            }`}
                          >
                            {t.returnPct.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <p className="text-[#666]">Run a backtest to see equity curve and trades.</p>
            )}
          </div>
        </div>
      )}

      {sub === "manager" && (
        <div className="space-y-3 p-4">
          <h3 className="font-bold text-[#ff6600]">Built-in strategies</h3>
          <ul className="grid gap-2 md:grid-cols-2">
            {strategyLabels.map((s) => (
              <li key={s.id} className="rounded border border-[#333] bg-[#0a0a0a] p-3 text-sm">
                {s.label}
                <button
                  type="button"
                  className="ml-3 text-xs text-[#ff8800] underline"
                  onClick={() => {
                    setStrategy(s.id);
                    onSubChange("run");
                  }}
                >
                  Use
                </button>
              </li>
            ))}
          </ul>
          <h3 className="pt-4 font-bold text-[#ff6600]">Custom (browser storage)</h3>
          {customs.length === 0 && <p className="text-sm text-[#666]">No custom strategies yet.</p>}
          <ul className="space-y-2">
            {customs.map((c) => (
              <li key={c.id} className="flex items-center justify-between rounded border border-[#333] p-3 text-sm">
                <span>{c.name}</span>
                <button
                  type="button"
                  className="text-[#ff8800]"
                  onClick={() => {
                    setEditorName(c.name);
                    setEditorCode(c.code);
                    onSubChange("editor");
                  }}
                >
                  Edit
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {sub === "editor" && (
        <div className="space-y-3 p-4">
          <Field label="Name">
            <input
              value={editorName}
              onChange={(e) => setEditorName(e.target.value)}
              className="w-full max-w-md rounded border border-[#444] bg-black px-2 py-1"
            />
          </Field>
          <textarea
            value={editorCode}
            onChange={(e) => setEditorCode(e.target.value)}
            rows={18}
            className="w-full rounded border border-[#ff6600] bg-[#050505] p-3 font-mono text-xs text-[#ddd]"
          />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={saveCustom}
              className="rounded bg-[#ff6600] px-4 py-2 text-sm font-bold text-black"
            >
              Save
            </button>
            <button
              type="button"
              onClick={testInWorker}
              className="rounded border border-[#ff6600] px-4 py-2 text-sm text-[#ff8800]"
            >
              Test in Web Worker
            </button>
            <button
              type="button"
              onClick={() => setEditorCode(DEFAULT_TEMPLATE)}
              className="rounded border border-[#444] px-4 py-2 text-sm text-[#aaa]"
            >
              Reset template
            </button>
          </div>
          <p className="text-xs text-[#888]">
            Custom strategies are stored in localStorage and intended for Web Worker execution.
            Built-in strategies run on the server via /api/backtest.
          </p>
        </div>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-xs">
      <span className="mb-1 block text-[#888]">{label}</span>
      {children}
    </label>
  );
}
