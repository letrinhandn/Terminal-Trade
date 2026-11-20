"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { OhlcvBar, QuoteSnapshot } from "@/lib/types";
import { apiGet, apiPost } from "@/lib/api";
import { loadWatchlist, saveWatchlist } from "@/lib/portfolio/store";
import { CandleChart } from "@/components/charts/CandleChart";
import { HeatmapMatrix } from "@/components/charts/HeatmapMatrix";
import { LineMultiChart } from "@/components/charts/LineMultiChart";
import { RangeChips } from "@/components/charts/RangeChips";
import { Sparkline } from "@/components/charts/Sparkline";
import type { ChartRange } from "@/components/charts/chartTheme";
import { useOhlcv } from "@/components/charts/useOhlcv";

type BatchPayload = {
  data: { quotes: QuoteSnapshot[]; errors: { symbol: string; error: string }[] };
  meta?: { provider?: string; latencyMs?: number; warnings?: string[] };
};

type CryptoMarketRow = {
  id: string;
  symbol: string;
  name: string;
  current_price: number | null;
  market_cap: number | null;
  total_volume: number | null;
  price_change_percentage_24h: number | null;
};

type CryptoMarketsPayload = {
  data: {
    markets: CryptoMarketRow[];
    attribution?: string;
    licenseNote?: string;
  };
};

type PanelPayload = {
  data: {
    ohlcvBySymbol: Record<string, OhlcvBar[]>;
    sparklineBySymbol: Record<string, { date: string; value: number }[]>;
    relative: {
      id: string;
      label: string;
      points: { date: string; value: number }[];
    }[];
    corr: { labels: string[]; matrix: number[][] };
    sourceNotes: Record<string, string>;
  };
  meta?: { latencyMs?: number; warnings?: string[] };
};

const DEFAULT_TAPE = [
  "SPY",
  "QQQ",
  "IWM",
  "AAPL",
  "MSFT",
  "NVDA",
  "TSLA",
  "META",
  "AMZN",
  "GOOGL",
  "BTC",
  "ETH",
];

const RANGE_TO_PANEL: Record<ChartRange, string> = {
  "1M": "1mo",
  "3M": "3mo",
  "1Y": "1y",
  "5Y": "5y",
};

function DeskCard({
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
    <div className={`border border-[#333] bg-[#050505] ${className}`}>
      <div className="flex items-center justify-between gap-2 border-b border-[#222] px-2.5 py-1">
        <h3 className="text-[10px] font-bold uppercase tracking-wide text-[#ff6600]">
          {title}
        </h3>
        {right}
      </div>
      <div className="p-2.5">{children}</div>
    </div>
  );
}

export function MarketsTab({
  symbol,
  onSymbolChange,
  onGoEquity,
  onStatus,
}: {
  symbol: string;
  onSymbolChange: (s: string) => void;
  onGoEquity?: () => void;
  onStatus?: (s: string) => void;
}) {
  const [watch, setWatch] = useState<string[]>([]);
  const [quotes, setQuotes] = useState<QuoteSnapshot[]>([]);
  const [cryptoMarkets, setCryptoMarkets] = useState<CryptoMarketRow[]>([]);
  const [cryptoNote, setCryptoNote] = useState("");
  const [panel, setPanel] = useState<PanelPayload["data"] | null>(null);
  const [panelError, setPanelError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [addSym, setAddSym] = useState("");
  const [chartRange, setChartRange] = useState<ChartRange>("3M");
  const panelSeq = useRef(0);

  // Hero candles: dedicated fetch (do not depend on panel race)
  const {
    bars: heroBars,
    sourceNote: heroNote,
    provider: heroProvider,
    loading: heroLoading,
    error: heroError,
  } = useOhlcv(symbol, chartRange);

  const activeQuote = useMemo(
    () => quotes.find((q) => q.symbol === symbol.toUpperCase()) || null,
    [quotes, symbol],
  );

  useEffect(() => {
    const w = loadWatchlist();
    setWatch(w.length ? w : DEFAULT_TAPE);
  }, []);

  async function refreshCrypto() {
    try {
      const res = await apiGet<CryptoMarketsPayload>(
        "/api/v1/crypto/markets?limit=12",
      );
      setCryptoMarkets(res.data.markets || []);
      setCryptoNote(
        [res.data.attribution, res.data.licenseNote]
          .filter(Boolean)
          .join(" | "),
      );
    } catch {
      setCryptoMarkets([]);
      setCryptoNote("CoinGecko markets unavailable");
    }
  }

  async function refreshPanel(list: string[], active: string, range: ChartRange) {
    const seq = ++panelSeq.current;
    const symbols = Array.from(
      new Set([active.toUpperCase(), ...list.map((s) => s.toUpperCase())]),
    ).slice(0, 14);
    try {
      const qs = new URLSearchParams({
        symbols: symbols.join(","),
        range: RANGE_TO_PANEL[range],
        active: active.toUpperCase(),
      });
      const res = await apiGet<PanelPayload>(
        `/api/v1/markets/panel?${qs.toString()}`,
      );
      if (seq !== panelSeq.current) return;
      setPanel(res.data);
      setPanelError(null);
    } catch (e) {
      if (seq !== panelSeq.current) return;
      setPanelError(e instanceof Error ? e.message : String(e));
      // keep previous panel - never wipe charts on a failed refresh
    }
  }

  async function refresh(list: string[]) {
    setLoading(true);
    try {
      const [res] = await Promise.all([
        apiPost<BatchPayload>("/api/v1/equity/quote", { symbols: list }),
        refreshCrypto(),
        refreshPanel(list, symbol, chartRange),
      ]);
      setQuotes(res.data.quotes || []);
      const warn = res.meta?.warnings?.[0];
      onStatus?.(
        `Markets | ${res.meta?.provider || "yahoo"} | ${res.meta?.latencyMs ?? "?"}ms${warn ? ` | ${warn}` : ""}`,
      );
    } catch (e) {
      onStatus?.(
        `Markets error: ${e instanceof Error ? e.message : String(e)}`,
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (watch.length) void refresh(watch);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watch.join(",")]);

  useEffect(() => {
    if (watch.length) void refreshPanel(watch, symbol, chartRange);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, chartRange]);

  const sorted = useMemo(
    () => [...quotes].sort((a, b) => b.changePct - a.changePct),
    [quotes],
  );
  const gainers = sorted.filter((q) => q.changePct > 0).slice(0, 6);
  const losers = [...sorted].filter((q) => q.changePct < 0).slice(-6).reverse();

  function persist(next: string[]) {
    setWatch(next);
    saveWatchlist(next);
  }

  function selectSym(s: string) {
    onSymbolChange(s);
  }

  const spark = (sym: string) =>
    panel?.sparklineBySymbol?.[sym.toUpperCase()] ||
    panel?.sparklineBySymbol?.[sym] ||
    [];

  return (
    <div className="space-y-2 p-2 md:p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-bold text-[#ff9500]">Markets</h2>
          <p className="text-[10px] text-[#555]">
            Native OHLCV market mosaic
          </p>
        </div>
        <div className="flex gap-2">
          <input
            value={addSym}
            onChange={(e) => setAddSym(e.target.value.toUpperCase())}
            placeholder="Add"
            className="w-24 rounded border border-[#444] bg-black px-2 py-1 font-mono text-xs text-[#ff8800]"
          />
          <button
            type="button"
            className="rounded border border-[#ff6600] px-2 py-1 text-xs text-[#ff8800]"
            onClick={() => {
              const s = addSym.trim().toUpperCase();
              if (s && !watch.includes(s)) persist([...watch, s]);
              setAddSym("");
            }}
          >
            + Watch
          </button>
          <button
            type="button"
            className="rounded bg-[#ff6600] px-3 py-1 text-xs font-bold text-black"
            onClick={() => void refresh(watch)}
            disabled={loading}
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Quote strip, hero chart, movers */}
      <div className="grid gap-2 xl:grid-cols-12">
        <DeskCard
          title={`${symbol.toUpperCase()} | Chart`}
          className="xl:col-span-8"
          right={<RangeChips value={chartRange} onChange={setChartRange} />}
        >
          {activeQuote && (
            <div className="mb-2 flex flex-wrap items-end gap-4 border-b border-[#1a1a1a] pb-2 font-mono text-xs">
              <div>
                <div className="text-[9px] uppercase text-[#555]">Last</div>
                <div className="text-xl font-bold text-[#ff9500]">
                  {activeQuote.price.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                  })}
                </div>
              </div>
              <div>
                <div className="text-[9px] uppercase text-[#555]">Chg</div>
                <div
                  className={
                    activeQuote.changePct >= 0
                      ? "text-emerald-400"
                      : "text-red-400"
                  }
                >
                  {activeQuote.change >= 0 ? "+" : ""}
                  {activeQuote.change.toFixed(2)} (
                  {activeQuote.changePct.toFixed(2)}%)
                </div>
              </div>
              <div>
                <div className="text-[9px] uppercase text-[#555]">High / Low</div>
                <div className="text-[#ccc]">
                  {activeQuote.high.toFixed(2)} / {activeQuote.low.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-[9px] uppercase text-[#555]">Volume</div>
                <div className="text-[#ccc]">
                  {(activeQuote.volume / 1e6).toFixed(2)}M
                </div>
              </div>
              <button
                type="button"
                className="ml-auto rounded border border-[#ff6600] px-2 py-1 text-[10px] text-[#ff8800]"
                onClick={() => onGoEquity?.()}
              >
                Open Equity to
              </button>
            </div>
          )}
          <CandleChart
            bars={heroBars}
            height={360}
            smaPeriods={[20, 50]}
            sourceNote={
              heroNote ||
              (heroProvider
                ? `${heroProvider} | SMA 20/50`
                : heroBars.length
                  ? "Native candles"
                  : undefined)
            }
            emptyLabel={
              heroLoading
                ? "Loading candles"
                : heroError
                  ? `Chart error: ${heroError}`
                  : "No OHLCV yet"
            }
          />
        </DeskCard>

        <div className="flex flex-col gap-2 xl:col-span-4">
          <DeskCard title="Top gainers">
            <ul className="space-y-1 font-mono text-[11px]">
              {gainers.map((q) => (
                <li key={q.symbol} className="flex items-center gap-2">
                  <button
                    type="button"
                    className="w-12 shrink-0 text-left text-[#ff8800]"
                    onClick={() => {
                      selectSym(q.symbol);
                      onGoEquity?.();
                    }}
                  >
                    {q.symbol}
                  </button>
                  <Sparkline values={spark(q.symbol)} height={22} width={56} />
                  <span className="ml-auto text-emerald-400">
                    +{q.changePct.toFixed(2)}%
                  </span>
                </li>
              ))}
              {!gainers.length && (
                <li className="text-[#555]">
                  {loading ? "" : "No gainers"}
                </li>
              )}
            </ul>
          </DeskCard>
          <DeskCard title="Top losers">
            <ul className="space-y-1 font-mono text-[11px]">
              {losers.map((q) => (
                <li key={q.symbol} className="flex items-center gap-2">
                  <button
                    type="button"
                    className="w-12 shrink-0 text-left text-[#ff8800]"
                    onClick={() => selectSym(q.symbol)}
                  >
                    {q.symbol}
                  </button>
                  <Sparkline values={spark(q.symbol)} height={22} width={56} />
                  <span className="ml-auto text-red-400">
                    {q.changePct.toFixed(2)}%
                  </span>
                </li>
              ))}
              {!losers.length && (
                <li className="text-[#555]">{loading ? "" : "No losers"}</li>
              )}
            </ul>
          </DeskCard>
          <DeskCard title="Crypto (CoinGecko)">
            {cryptoNote && (
              <p className="mb-1.5 text-[8px] leading-snug text-[#555]">
                {cryptoNote}
              </p>
            )}
            <ul className="max-h-48 space-y-0.5 overflow-auto font-mono text-[11px]">
              {cryptoMarkets.map((m) => {
                const pct = m.price_change_percentage_24h ?? 0;
                const sym = m.symbol.toUpperCase();
                return (
                  <li key={m.id} className="flex justify-between gap-2">
                    <button
                      type="button"
                      className="text-[#ff8800]"
                      onClick={() => selectSym(sym)}
                    >
                      {sym}
                    </button>
                    <span className="text-[#aaa]">
                      {m.current_price != null
                        ? m.current_price >= 100
                          ? m.current_price.toFixed(0)
                          : m.current_price.toFixed(2)
                        : "-"}
                    </span>
                    <span
                      className={
                        pct >= 0 ? "text-emerald-400" : "text-red-400"
                      }
                    >
                      {pct >= 0 ? "+" : ""}
                      {pct.toFixed(1)}%
                    </span>
                  </li>
                );
              })}
            </ul>
          </DeskCard>
        </div>

        <DeskCard title="Watchlist tape" className="xl:col-span-7">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] font-mono text-[11px]">
              <thead className="text-[#666]">
                <tr>
                  {["Symbol", "Last", "Chg%", "30d", "Vol"].map((h) => (
                    <th key={h} className="p-1 text-left font-normal">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {quotes.map((q) => (
                  <tr
                    key={q.symbol}
                    className={`border-t border-[#1a1a1a] ${
                      q.symbol === symbol.toUpperCase() ? "bg-[#1a0a00]" : ""
                    }`}
                  >
                    <td className="p-1">
                      <button
                        type="button"
                        className="text-[#ff8800] hover:underline"
                        onClick={() => {
                          selectSym(q.symbol);
                          onGoEquity?.();
                        }}
                      >
                        {q.symbol}
                      </button>
                    </td>
                    <td className="p-1">{q.price.toFixed(2)}</td>
                    <td
                      className={`p-1 ${q.changePct >= 0 ? "text-emerald-400" : "text-red-400"}`}
                    >
                      {q.changePct.toFixed(2)}%
                    </td>
                    <td className="p-1">
                      <Sparkline
                        values={spark(q.symbol)}
                        height={20}
                        width={64}
                      />
                    </td>
                    <td className="p-1 text-[#555]">
                      {(q.volume / 1e6).toFixed(2)}M
                    </td>
                  </tr>
                ))}
                {!quotes.length && (
                  <tr>
                    <td colSpan={5} className="p-4 text-center text-[#555]">
                      {loading ? "Loading tape" : "No quotes"}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </DeskCard>

        <DeskCard
          title={`Relative vs SPY (${chartRange})`}
          className="xl:col-span-5"
        >
          <LineMultiChart
            series={(panel?.relative || []).map((r) => ({
              id: r.id,
              label: r.label,
              points: r.points,
            }))}
            height={200}
            emptyLabel={
              panelError
                ? `Panel: ${panelError}`
                : loading
                  ? "Loading relative"
                  : "No relative series"
            }
          />
        </DeskCard>

        <DeskCard title="Return correlation" className="xl:col-span-12">
          <HeatmapMatrix
            labels={panel?.corr?.labels || []}
            matrix={panel?.corr?.matrix || []}
          />
        </DeskCard>
      </div>
    </div>
  );
}
