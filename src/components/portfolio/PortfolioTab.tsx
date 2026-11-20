"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { MarkedHolding, OhlcvBar, PaperPortfolio, QuoteSnapshot } from "@/lib/types";
import { apiGet, apiPost } from "@/lib/api";
import {
  addHolding,
  emptyPortfolio,
  loadPortfolio,
  removeHolding,
  savePortfolio,
} from "@/lib/portfolio/store";
import { computePortfolioRisk } from "@/lib/portfolio/risk";
import { AllocationDonut } from "@/components/charts/AllocationDonut";
import { EquityChart } from "@/components/charts/EquityChart";
import { HeatmapMatrix } from "@/components/charts/HeatmapMatrix";
import { Sparkline } from "@/components/charts/Sparkline";
import {
  appendLedger,
  loadLedger,
  loadNavSnaps,
  pushNavSnap,
  seedDemoPortfolioIfEmpty,
  type LedgerTx,
} from "@/lib/portfolio/ledger";

type PanelPayload = {
  data: {
    ohlcvBySymbol: Record<string, OhlcvBar[]>;
    sparklineBySymbol: Record<string, { date: string; value: number }[]>;
    corr: { labels: string[]; matrix: number[][] };
  };
};

type Section =
  | "positions"
  | "sectors"
  | "perf"
  | "risk"
  | "optimize"
  | "reports";

function Panel({
  title,
  children,
  className = "",
  right,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
  right?: React.ReactNode;
}) {
  return (
    <section
      className={`flex min-h-0 flex-col overflow-hidden border border-[#2a2a2a] bg-[#0a0a0a] ${className}`}
    >
      <header className="flex shrink-0 items-center justify-between border-b border-[#1f1f1f] bg-[#111] px-2 py-1">
        <h3 className="text-[10px] font-semibold tracking-[0.08em] text-[#ff8c00]">
          {title}
        </h3>
        {right}
      </header>
      <div className="min-h-0 flex-1 overflow-auto p-2">{children}</div>
    </section>
  );
}

function sectorOf(q?: QuoteSnapshot): string {
  if (!q?.sector) return "Other";
  const s = q.sector;
  if (/crypto|CURRENCY/i.test(s)) return "Crypto";
  if (/tech|software|semiconductor/i.test(s)) return "Technology";
  if (/financ|bank/i.test(s)) return "Financial";
  if (/health|pharma|biotech/i.test(s)) return "Healthcare";
  if (/energy|oil/i.test(s)) return "Energy";
  if (/consumer/i.test(s)) return "Consumer";
  return s.length > 16 ? s.slice(0, 14) + "" : s;
}

function maxDrawdown(curve: { equity: number }[]): number {
  let peak = -Infinity;
  let mdd = 0;
  for (const p of curve) {
    peak = Math.max(peak, p.equity);
    if (peak > 0) mdd = Math.min(mdd, (p.equity - peak) / peak);
  }
  return mdd * 100;
}

const SECTIONS: { id: Section; label: string }[] = [
  { id: "positions", label: "POSITIONS" },
  { id: "sectors", label: "SECTORS" },
  { id: "perf", label: "PERF/RISK" },
  { id: "optimize", label: "OPTIMIZE" },
  { id: "reports", label: "REPORTS" },
  { id: "risk", label: "RISK" },
];

export function PortfolioTab({
  symbol,
  onSymbolChange,
  onGoIdeas,
}: {
  symbol: string;
  onSymbolChange: (s: string) => void;
  onGoIdeas?: () => void;
}) {
  const [portfolio, setPortfolio] = useState<PaperPortfolio>(emptyPortfolio());
  const [quotes, setQuotes] = useState<Record<string, QuoteSnapshot>>({});
  const [ledger, setLedger] = useState<LedgerTx[]>([]);
  const [navCurve, setNavCurve] = useState<{ date: string; equity: number }[]>([]);
  const [sparks, setSparks] = useState<
    Record<string, { date: string; value: number }[]>
  >({});
  const [corr, setCorr] = useState<{ labels: string[]; matrix: number[][] }>({
    labels: [],
    matrix: [],
  });
  const [sym, setSym] = useState(symbol);
  const [qty, setQty] = useState("10");
  const [cost, setCost] = useState("");
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState("Paper portfolio (local)");
  const [section, setSection] = useState<Section>("positions");
  const [filter, setFilter] = useState("");
  const [range, setRange] = useState<"1M" | "3M" | "1Y">("3M");

  useEffect(() => {
    const p = seedDemoPortfolioIfEmpty(loadPortfolio, savePortfolio);
    setPortfolio(p);
    setLedger(loadLedger());
  }, []);

  useEffect(() => setSym(symbol), [symbol]);

  const refreshQuotes = useCallback(async (p: PaperPortfolio) => {
    const symbols = p.holdings.map((h) => h.symbol);
    if (!symbols.length) {
      setQuotes({});
      return;
    }
    setBusy(true);
    try {
      const res = await apiPost<{ data: { quotes: QuoteSnapshot[] } }>(
        "/api/v1/equity/quote",
        { symbols },
      );
      const map: Record<string, QuoteSnapshot> = {};
      for (const q of res.data.quotes || []) map[q.symbol] = q;
      setQuotes(map);
      setLog(`Marked ${res.data.quotes?.length ?? 0} | Yahoo`);
    } catch (e) {
      setLog(`Quote error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setBusy(false);
    }
  }, []);

  const refreshPanel = useCallback(async (p: PaperPortfolio) => {
    const symbols = p.holdings.map((h) => h.symbol);
    if (!symbols.length) return;
    const rangeMap = { "1M": "1mo", "3M": "3mo", "1Y": "1y" } as const;
    try {
      const qs = new URLSearchParams({
        symbols: symbols.slice(0, 12).join(","),
        range: rangeMap[range],
        active: symbols[0],
      });
      const res = await apiGet<PanelPayload>(`/api/v1/markets/panel?${qs}`);
      setSparks(res.data.sparklineBySymbol || {});
      setCorr(res.data.corr || { labels: [], matrix: [] });

      const ohlcv = res.data.ohlcvBySymbol || {};
      const dates = new Set<string>();
      for (const bars of Object.values(ohlcv)) {
        for (const b of bars) dates.add(b.date);
      }
      const sortedDates = Array.from(dates).sort();
      const curve: { date: string; equity: number }[] = [];
      for (const d of sortedDates) {
        let equity = p.cash;
        for (const h of p.holdings) {
          const bars = ohlcv[h.symbol] || [];
          const hit = [...bars].reverse().find((b) => b.date <= d);
          const close = hit?.close ?? h.costBasis;
          equity += close * h.qty;
        }
        curve.push({ date: d, equity });
      }
      if (curve.length) setNavCurve(curve);
      else {
        const snaps = loadNavSnaps();
        setNavCurve(snaps.map((s) => ({ date: s.date, equity: s.equity })));
      }
    } catch {
      /* keep prior */
    }
  }, [range]);

  useEffect(() => {
    void refreshQuotes(portfolio);
    void refreshPanel(portfolio);
  }, [portfolio.holdings.length, range]); // eslint-disable-line react-hooks/exhaustive-deps

  function persist(next: PaperPortfolio) {
    setPortfolio(next);
    savePortfolio(next);
  }

  const marked: MarkedHolding[] = useMemo(() => {
    const rows = portfolio.holdings.map((h) => {
      const q = quotes[h.symbol];
      const price = q?.price ?? h.costBasis;
      const marketValue = price * h.qty;
      const costValue = h.costBasis * h.qty;
      const pnl = marketValue - costValue;
      return {
        ...h,
        name: q?.name || h.symbol,
        price,
        changePct: q?.changePct ?? 0,
        marketValue,
        costValue,
        pnl,
        pnlPct: costValue ? (pnl / costValue) * 100 : 0,
        weight: 0,
      };
    });
    const equity = portfolio.cash + rows.reduce((a, r) => a + r.marketValue, 0);
    return rows.map((r) => ({
      ...r,
      weight: equity > 0 ? (r.marketValue / equity) * 100 : 0,
    }));
  }, [portfolio, quotes]);

  const filtered = useMemo(() => {
    const q = filter.trim().toUpperCase();
    if (!q) return marked;
    return marked.filter((m) => m.symbol.includes(q) || m.name.toUpperCase().includes(q));
  }, [marked, filter]);

  const totals = useMemo(() => {
    const invested = marked.reduce((a, r) => a + r.marketValue, 0);
    const costV = marked.reduce((a, r) => a + r.costValue, 0);
    const pnl = invested - costV;
    const equity = portfolio.cash + invested;
    const dayPnl = marked.reduce(
      (a, r) => a + ((r.price * r.changePct) / 100) * r.qty,
      0,
    );
    return {
      invested,
      cost: costV,
      pnl,
      equity,
      dayPnl,
      dayPct: equity ? (dayPnl / equity) * 100 : 0,
      pnlPct: costV ? (pnl / costV) * 100 : 0,
    };
  }, [marked, portfolio.cash]);

  useEffect(() => {
    if (totals.equity > 0) pushNavSnap(totals.equity);
  }, [totals.equity]);

  const risk = useMemo(
    () => computePortfolioRisk(portfolio.cash, marked),
    [portfolio.cash, marked],
  );

  const mdd = useMemo(() => maxDrawdown(navCurve), [navCurve]);

  const sectorSlices = useMemo(() => {
    const map = new Map<string, number>();
    for (const m of marked) {
      const sec = sectorOf(quotes[m.symbol]);
      map.set(sec, (map.get(sec) || 0) + m.weight);
    }
    if (totals.equity) map.set("Cash", (portfolio.cash / totals.equity) * 100);
    return Array.from(map.entries()).map(([label, weight]) => ({
      id: label,
      label,
      weight,
    }));
  }, [marked, quotes, portfolio.cash, totals.equity]);

  async function onBuy() {
    const q = Number(qty);
    let c = Number(cost);
    if (!c || Number.isNaN(c)) {
      try {
        const res = await apiPost<{ data: { quotes: QuoteSnapshot[] } }>(
          "/api/v1/equity/quote",
          { symbols: [sym] },
        );
        c = res.data.quotes?.[0]?.price ?? 0;
      } catch {
        c = 0;
      }
    }
    if (!sym.trim() || !(q > 0) || !(c > 0)) {
      setLog("Need symbol, qty > 0, and cost (or live quote).");
      return;
    }
    const next = addHolding(portfolio, {
      symbol: sym,
      qty: q,
      costBasis: c,
    });
    persist(next);
    setLedger(
      appendLedger({
        date: new Date().toISOString().slice(0, 10),
        symbol: sym.toUpperCase(),
        type: "BUY",
        qty: q,
        price: c,
        total: q * c,
      }),
    );
    onSymbolChange(sym.trim().toUpperCase());
    setLog(`BUY ${q} ${sym.toUpperCase()} @ ${c}`);
    void refreshQuotes(next);
    void refreshPanel(next);
  }

  function onSellSelected() {
    const h = marked.find((m) => m.symbol === sym.toUpperCase()) || marked[0];
    if (!h) {
      setLog("No holding to sell");
      return;
    }
    persist(removeHolding(portfolio, h.id));
    setLedger(
      appendLedger({
        date: new Date().toISOString().slice(0, 10),
        symbol: h.symbol,
        type: "SELL",
        qty: h.qty,
        price: h.price,
        total: h.marketValue,
      }),
    );
    setLog(`SELL ${h.qty} ${h.symbol} @ mark`);
  }

  const pct = (n: number) =>
    `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-black text-[10px]">
      {/* Portfolio command bar */}
      <div className="flex shrink-0 flex-wrap items-center gap-2 border-b border-[#222] bg-[#0a0a0a] px-2 py-1.5">
        <select
          className="border border-[#333] bg-black px-2 py-1 font-mono text-[10px] text-[#ff8800]"
          defaultValue="demo"
        >
          <option value="demo">DEMO PORTFOLIO (USD)</option>
        </select>
        <button
          type="button"
          onClick={() => void onBuy()}
          className="bg-[#ff6600] px-2.5 py-1 font-bold text-black"
        >
          BUY
        </button>
        <button
          type="button"
          onClick={onSellSelected}
          className="border border-[#444] px-2.5 py-1 text-[#ccc]"
        >
          SELL
        </button>
        <button
          type="button"
          className="border border-[#333] px-2.5 py-1 text-[#888]"
          onClick={() => setLog("Dividends unavailable")}
        >
          DIV
        </button>
        <div className="mx-1 h-4 w-px bg-[#333]" />
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setSection(s.id)}
            className={`px-2 py-1 tracking-wide ${
              section === s.id
                ? "bg-[#1a0a00] text-[#ff8800]"
                : "text-[#666] hover:text-[#aaa]"
            }`}
          >
            {s.label}
          </button>
        ))}
        <button
          type="button"
          className="ml-auto border border-[#333] px-2 py-1 text-[#aaa]"
          disabled={busy}
          onClick={() => {
            void refreshQuotes(portfolio);
            void refreshPanel(portfolio);
          }}
        >
          REFRESH
        </button>
        {onGoIdeas && (
          <button
            type="button"
            className="border border-[#ff6600] px-2 py-1 text-[#ff8800]"
            onClick={onGoIdeas}
          >
            IDEAS
          </button>
        )}
      </div>

      {/* Stats ribbon */}
      <div className="grid shrink-0 grid-cols-2 gap-px border-b border-[#222] bg-[#222] sm:grid-cols-4 xl:grid-cols-8">
        {[
          {
            label: "NAV",
            value: totals.equity.toLocaleString(undefined, {
              maximumFractionDigits: 2,
            }),
            sub: `${marked.length} positions`,
            color: "text-[#ff9500]",
          },
          {
            label: "TODAY",
            value: `${totals.dayPnl >= 0 ? "+" : ""}${totals.dayPnl.toFixed(2)}`,
            sub: pct(totals.dayPct),
            color: totals.dayPnl >= 0 ? "text-[#00e676]" : "text-[#ff5252]",
          },
          {
            label: "UNREALISED P&L",
            value: `${totals.pnl >= 0 ? "+" : ""}${totals.pnl.toFixed(2)}`,
            sub: pct(totals.pnlPct),
            color: totals.pnl >= 0 ? "text-[#00e676]" : "text-[#ff5252]",
          },
          {
            label: "CASH",
            value: portfolio.cash.toFixed(2),
            sub: "in NAV",
            color: "text-[#eee]",
          },
          {
            label: "VOLATILITY",
            value: `${risk.volProxy.toFixed(1)}%`,
            sub: "proxy",
            color: "text-[#eee]",
          },
          {
            label: "SHARPE",
            value: risk.sharpeProxy.toFixed(2),
            sub: "proxy",
            color: "text-[#eee]",
          },
          {
            label: "MAX DRAWDOWN",
            value: `${mdd.toFixed(1)}%`,
            sub: "from NAV curve",
            color: "text-[#ff5252]",
          },
          {
            label: "CONCENTRATION",
            value: `${risk.maxWeight.toFixed(1)}%`,
            sub: risk.maxWeightSymbol || "-",
            color: "text-[#eee]",
          },
        ].map((t) => (
          <div key={t.label} className="bg-black px-2 py-1.5">
            <div className="text-[8px] tracking-wider text-[#666]">{t.label}</div>
            <div className={`font-mono text-sm font-bold ${t.color}`}>
              {t.value}
            </div>
            <div className="font-mono text-[9px] text-[#555]">{t.sub}</div>
          </div>
        ))}
      </div>

      {/* Main mosaic: top heatmap|perf|sectors | bottom blotter|txn */}
      <div className="grid min-h-0 flex-1 grid-rows-[minmax(200px,2fr)_minmax(220px,3fr)] gap-1 p-1">
        <div className="grid min-h-0 gap-1 lg:grid-cols-12">
          <Panel title="HOLDINGS" className="lg:col-span-3">
            <div className="grid grid-cols-2 gap-1 sm:grid-cols-3 lg:grid-cols-2">
              {marked.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => {
                    onSymbolChange(m.symbol);
                    setSym(m.symbol);
                  }}
                  className="border border-[#1a1a1a] p-1.5 text-left font-mono"
                  style={{
                    background:
                      m.changePct >= 0
                        ? `rgba(0,230,118,${0.12 + Math.min(0.45, Math.abs(m.changePct) / 12)})`
                        : `rgba(255,82,82,${0.12 + Math.min(0.45, Math.abs(m.changePct) / 12)})`,
                  }}
                >
                  <div className="text-[#ff8800]">{m.symbol}</div>
                  <div
                    className={
                      m.changePct >= 0 ? "text-[#00e676]" : "text-[#ff5252]"
                    }
                  >
                    {m.changePct >= 0 ? "+" : ""}
                    {m.changePct.toFixed(2)}%
                  </div>
                </button>
              ))}
            </div>
          </Panel>

          <Panel
            title="PERFORMANCE"
            className="lg:col-span-5"
            right={
              <div className="flex gap-1">
                {(["1M", "3M", "1Y"] as const).map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRange(r)}
                    className={`px-1.5 py-0.5 font-mono text-[9px] ${
                      range === r
                        ? "bg-[#ff6600] text-black"
                        : "text-[#666] hover:text-[#aaa]"
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
            }
          >
            <div className="mb-1 flex justify-between font-mono text-[9px] text-[#666]">
              <span>
                NAV{" "}
                <span className="text-[#ff8800]">
                  {totals.equity.toFixed(2)}
                </span>
              </span>
              <span>
                COST{" "}
                <span className="text-[#aaa]">{totals.cost.toFixed(2)}</span>
              </span>
            </div>
            <EquityChart
              data={navCurve.map((n) => ({ date: n.date, equity: n.equity }))}
              height={180}
            />
          </Panel>

          <Panel title="SECTORS & CORRELATION" className="lg:col-span-4">
            {(section === "sectors" ||
              section === "positions" ||
              section === "perf" ||
              section === "risk") && (
              <>
                <AllocationDonut slices={sectorSlices} size={120} />
                <div className="mt-2">
                  <HeatmapMatrix
                    labels={corr.labels.slice(0, 6)}
                    matrix={corr.matrix
                      .slice(0, 6)
                      .map((r) => r.slice(0, 6))}
                  />
                </div>
              </>
            )}
            {section === "optimize" && (
              <p className="text-[#555]">
                Optimize is not included. Use an offline optimizer if needed.
              </p>
            )}
            {section === "reports" && (
              <p className="text-[#555]">
                Print the blotter from the browser for a simple report.
              </p>
            )}
          </Panel>
        </div>

        <div className="grid min-h-0 gap-1 lg:grid-cols-12">
          <Panel
            title={`POSITIONS (${filtered.length})`}
            className="lg:col-span-8"
            right={
              <input
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="Filter"
                className="w-28 border border-[#333] bg-black px-1.5 py-0.5 font-mono text-[9px] text-[#ff8800]"
              />
            }
          >
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] border-collapse font-mono text-[10px]">
                <thead className="sticky top-0 bg-[#0a0a0a] text-[#666]">
                  <tr>
                    {[
                      "SYMBOL",
                      "QTY",
                      "LAST",
                      "AVG COST",
                      "MKT VAL",
                      "COST",
                      "P&L",
                      "P&L%",
                      "CHG%",
                      "TREND",
                      "WT%",
                      "",
                    ].map((h) => (
                      <th key={h} className="p-1 text-left font-normal">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((m) => (
                    <tr
                      key={m.id}
                      className="border-t border-[#1a1a1a] hover:bg-[#111]"
                    >
                      <td className="p-1">
                        <button
                          type="button"
                          className="text-[#ff8800]"
                          onClick={() => {
                            onSymbolChange(m.symbol);
                            setSym(m.symbol);
                          }}
                        >
                          {m.symbol}
                        </button>
                      </td>
                      <td className="p-1">{m.qty}</td>
                      <td className="p-1">{m.price.toFixed(2)}</td>
                      <td className="p-1">{m.costBasis.toFixed(2)}</td>
                      <td className="p-1">{m.marketValue.toFixed(0)}</td>
                      <td className="p-1">{m.costValue.toFixed(0)}</td>
                      <td
                        className={`p-1 ${m.pnl >= 0 ? "text-[#00e676]" : "text-[#ff5252]"}`}
                      >
                        {m.pnl.toFixed(0)}
                      </td>
                      <td
                        className={`p-1 ${m.pnlPct >= 0 ? "text-[#00e676]" : "text-[#ff5252]"}`}
                      >
                        {m.pnlPct.toFixed(1)}%
                      </td>
                      <td
                        className={`p-1 ${m.changePct >= 0 ? "text-[#00e676]" : "text-[#ff5252]"}`}
                      >
                        {m.changePct.toFixed(2)}%
                      </td>
                      <td className="p-1">
                        <Sparkline
                          values={sparks[m.symbol] || []}
                          height={16}
                          width={48}
                        />
                      </td>
                      <td className="p-1">{m.weight.toFixed(1)}</td>
                      <td className="p-1">
                        <button
                          type="button"
                          className="text-[#555] hover:text-[#ff5252]"
                          onClick={() => persist(removeHolding(portfolio, m.id))}
                        >
                          ×
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel title="TRANSACTION HISTORY" className="lg:col-span-4">
            <div className="mb-2 flex flex-wrap gap-1 border-b border-[#1a1a1a] pb-2">
              <input
                value={sym}
                onChange={(e) => setSym(e.target.value.toUpperCase())}
                className="w-16 border border-[#333] bg-black px-1 py-0.5 font-mono text-[#ff8800]"
                placeholder="SYM"
              />
              <input
                value={qty}
                onChange={(e) => setQty(e.target.value)}
                className="w-12 border border-[#333] bg-black px-1 py-0.5 font-mono text-[#ff8800]"
                placeholder="Qty"
              />
              <input
                value={cost}
                onChange={(e) => setCost(e.target.value)}
                className="w-16 border border-[#333] bg-black px-1 py-0.5 font-mono text-[#ff8800]"
                placeholder="Px"
              />
              <button
                type="button"
                onClick={() => void onBuy()}
                className="bg-[#ff6600] px-2 py-0.5 font-bold text-black"
              >
                BUY
              </button>
            </div>
            <p className="mb-1 text-[9px] text-[#555]">{log}</p>
            <table className="w-full border-collapse font-mono text-[9px]">
              <thead className="text-[#666]">
                <tr>
                  {["DATE", "SYM", "TYPE", "QTY", "PX", "TOTAL"].map((h) => (
                    <th key={h} className="p-1 text-left font-normal">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ledger.slice(0, 50).map((t) => (
                  <tr key={t.id} className="border-t border-[#151515]">
                    <td className="p-1">{t.date}</td>
                    <td className="p-1 text-[#ff8800]">{t.symbol}</td>
                    <td className="p-1">{t.type}</td>
                    <td className="p-1">{t.qty}</td>
                    <td className="p-1">{t.price.toFixed(2)}</td>
                    <td className="p-1">{t.total.toFixed(0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        </div>
      </div>
    </div>
  );
}
