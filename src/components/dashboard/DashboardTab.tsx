"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { NewsArticle, QuoteSnapshot } from "@/lib/types";

type DashRow = {
  id: string;
  label: string;
  price: number;
  change: number;
  changePct: number;
};

type Bundle = {
  data: {
    indices: DashRow[];
    forex: DashRow[];
    commodities: DashRow[];
    snapshot: DashRow[];
    ticker: DashRow[];
    focus: QuoteSnapshot | null;
    news: NewsArticle[];
    fearGreed: { value: number; label: string; source: string } | null;
    gainers: { symbol: string; price: number; changePct: number; name: string }[];
    losers: { symbol: string; price: number; changePct: number; name: string }[];
    breadth: {
      universe: string;
      up: number;
      down: number;
      flat: number;
      upPct: number;
      source: string;
    } | null;
  };
  meta?: { latencyMs?: number };
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
      <header className="flex shrink-0 items-center justify-between border-b border-[#1f1f1f] bg-[#111] px-2 py-1">
        <h3 className="text-[10px] font-semibold tracking-[0.1em] text-[#ff8c00]">
          {title}
        </h3>
      </header>
      <div className={`min-h-0 flex-1 overflow-auto ${bodyClassName}`}>
        {children}
      </div>
    </section>
  );
}

function pctClass(n: number) {
  return n > 0 ? "text-[#00e676]" : n < 0 ? "text-[#ff5252]" : "text-[#888]";
}

function fmtPx(n: number, decimals = 2) {
  if (!Number.isFinite(n)) return "-";
  if (Math.abs(n) >= 1000)
    return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return n.toFixed(decimals);
}

function QuoteTable({
  rows,
  decimals = 2,
  onPick,
}: {
  rows: DashRow[];
  decimals?: number;
  onPick?: (id: string) => void;
}) {
  return (
    <table className="w-full border-collapse font-mono text-[10px] leading-tight">
      <thead className="sticky top-0 bg-[#0a0a0a] text-[#666]">
        <tr>
          <th className="pb-1 text-left font-normal">Symbol</th>
          <th className="pb-1 text-right font-normal">Price</th>
          <th className="pb-1 text-right font-normal">Chg</th>
          <th className="pb-1 text-right font-normal">Chg%</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id} className="border-t border-[#1a1a1a] hover:bg-[#111]">
            <td className="py-[3px] pr-1">
              <button
                type="button"
                className="text-left text-[#ff8800] hover:underline"
                onClick={() => onPick?.(r.id)}
                title={r.id}
              >
                {r.label}
              </button>
            </td>
            <td className="py-[3px] text-right text-[#eee]">
              {fmtPx(r.price, decimals)}
            </td>
            <td className={`py-[3px] text-right ${pctClass(r.change)}`}>
              {r.change >= 0 ? "+" : ""}
              {fmtPx(r.change, decimals)}
            </td>
            <td className={`py-[3px] text-right ${pctClass(r.changePct)}`}>
              {r.changePct >= 0 ? "+" : ""}
              {r.changePct.toFixed(2)}%
            </td>
          </tr>
        ))}
        {!rows.length && (
          <tr>
            <td colSpan={4} className="py-4 text-center text-[#555]">
              No data
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
}

function FearGauge({ value, label }: { value: number; label: string }) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div className="space-y-1.5">
      <div className="flex items-end justify-between gap-2">
        <div className="font-mono text-xl font-bold leading-none text-[#ff9500]">
          {v}
          <span className="text-[10px] text-[#666]">/100</span>
        </div>
        <div className="text-right text-[10px] leading-tight text-[#aaa]">
          {label}
        </div>
      </div>
      <div className="h-1.5 w-full overflow-hidden bg-[#1a1a1a]">
        <div
          className="h-full"
          style={{
            width: `${v}%`,
            background:
              "linear-gradient(90deg, #ef4444 0%, #eab308 45%, #22c55e 100%)",
          }}
        />
      </div>
    </div>
  );
}

export function DashboardTab({
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
  const [bundle, setBundle] = useState<Bundle["data"] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await apiGet<Bundle>(
          `/api/v1/dashboard/overview?symbol=${encodeURIComponent(symbol)}`,
        );
        if (cancelled) return;
        setBundle(res.data);
        onStatus?.(
          `Dashboard | Yahoo | ${res.meta?.latencyMs ?? "?"}ms | ${res.data.indices.length} indices`,
        );
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [symbol, onStatus]);

  function pick(id: string) {
    const clean = id
      .replace("=X", "")
      .replace("-USD", "")
      .replace(/^\^/, "");
    if (id.startsWith("^")) {
      const map: Record<string, string> = {
        "^GSPC": "SPX",
        "^IXIC": "NASDAQ",
        "^VIX": "VIX",
      };
      onSymbolChange(map[id] || clean);
    } else if (id.includes("=X") || id.includes("=F")) {
      /* display only */
    } else {
      onSymbolChange(clean);
    }
  }

  const focus = bundle?.focus;
  const downPct = bundle?.breadth
    ? 100 - bundle.breadth.upPct
    : 0;

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-black">
      {/* Ticker ribbon */}
      <div className="shrink-0 overflow-hidden border-b border-[#222] bg-black">
        <div className="flex gap-5 overflow-x-auto px-2 py-1 font-mono text-[10px]">
          {(bundle?.ticker || []).map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => pick(t.id)}
              className="shrink-0 whitespace-nowrap"
            >
              <span className="text-[#888]">{t.label}</span>{" "}
              <span className="text-[#ddd]">{fmtPx(t.price)}</span>{" "}
              <span className={pctClass(t.changePct)}>
                {t.changePct >= 0 ? "+" : ""}
                {t.changePct.toFixed(2)}%
              </span>
            </button>
          ))}
          {loading && !bundle && (
            <span className="text-[#555]">Loading tape</span>
          )}
        </div>
      </div>

      {error && (
        <p className="shrink-0 px-2 py-1 text-[10px] text-red-400">{error}</p>
      )}

      {/* Mosaic: tables, pulse, quote, news, chart */}
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-1 p-1 lg:grid-cols-12 lg:grid-rows-2">
        <Panel title="Global Indices" className="lg:col-span-3">
          <QuoteTable rows={bundle?.indices || []} onPick={pick} />
        </Panel>
        <Panel title="Forex - Major Pairs" className="lg:col-span-3">
          <QuoteTable rows={bundle?.forex || []} decimals={4} />
        </Panel>
        <Panel title="Commodities" className="lg:col-span-3">
          <QuoteTable rows={bundle?.commodities || []} />
        </Panel>

        {/* Market Pulse - right column, spans both rows */}
        <Panel
          title="Market Pulse"
          className="lg:col-span-3 lg:row-span-2"
          bodyClassName="space-y-3 overflow-auto p-2"
        >
          <div>
            <div className="mb-1 text-[9px] tracking-wider text-[#666]">
              FEAR & GREED
            </div>
            {bundle?.fearGreed ? (
              <FearGauge
                value={bundle.fearGreed.value}
                label={bundle.fearGreed.label}
              />
            ) : (
              <p className="text-[10px] text-[#555]">Unavailable</p>
            )}
          </div>

          <div>
            <div className="mb-1 text-[9px] tracking-wider text-[#666]">
              MARKET BREADTH
            </div>
            {bundle?.breadth ? (
              <div className="space-y-1.5 font-mono text-[10px]">
                <div className="flex h-1.5 w-full overflow-hidden bg-[#1a1a1a]">
                  <div
                    className="h-full bg-[#00e676]"
                    style={{ width: `${bundle.breadth.upPct}%` }}
                  />
                  <div
                    className="h-full bg-[#ff5252]"
                    style={{ width: `${downPct}%` }}
                  />
                </div>
                <div className="flex justify-between text-[#aaa]">
                  <span className="text-[#00e676]">
                    Up {bundle.breadth.up}
                  </span>
                  <span>Flat {bundle.breadth.flat}</span>
                  <span className="text-[#ff5252]">
                    Down {bundle.breadth.down}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-[10px] text-[#555]">No tape</p>
            )}
          </div>

          <div>
            <div className="mb-1 text-[9px] tracking-wider text-[#666]">
              TOP GAINERS / LOSERS
            </div>
            <div className="grid grid-cols-2 gap-2 font-mono text-[10px]">
              <ul className="space-y-0.5">
                {(bundle?.gainers || []).map((g) => (
                  <li key={g.symbol} className="flex justify-between gap-1">
                    <button
                      type="button"
                      className="text-[#ff8800]"
                      onClick={() => onSymbolChange(g.symbol)}
                    >
                      {g.symbol}
                    </button>
                    <span className="text-[#00e676]">
                      +{g.changePct.toFixed(1)}%
                    </span>
                  </li>
                ))}
              </ul>
              <ul className="space-y-0.5">
                {(bundle?.losers || []).map((g) => (
                  <li key={g.symbol} className="flex justify-between gap-1">
                    <button
                      type="button"
                      className="text-[#ff8800]"
                      onClick={() => onSymbolChange(g.symbol)}
                    >
                      {g.symbol}
                    </button>
                    <span className="text-[#ff5252]">
                      {g.changePct.toFixed(1)}%
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div>
            <div className="mb-1 text-[9px] tracking-wider text-[#666]">
              GLOBAL SNAPSHOT
            </div>
            <ul className="space-y-0.5 font-mono text-[10px]">
              {(bundle?.snapshot || []).map((s) => (
                <li key={s.id} className="flex justify-between gap-2">
                  <span className="text-[#888]">{s.label}</span>
                  <span className="text-[#ddd]">{fmtPx(s.price)}</span>
                  <span className={pctClass(s.changePct)}>
                    {s.changePct >= 0 ? "+" : ""}
                    {s.changePct.toFixed(2)}%
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </Panel>

        <Panel title={`Quote: ${symbol}`} className="lg:col-span-3">
          {focus ? (
            <div className="flex h-full flex-col justify-between gap-2">
              <div>
                <div className="text-[10px] text-[#666]">{focus.name}</div>
                <div className="font-mono text-3xl font-bold leading-none text-[#ff9500]">
                  {fmtPx(focus.price)}
                </div>
                <div
                  className={`mt-1 font-mono text-xs ${pctClass(focus.changePct)}`}
                >
                  {focus.change >= 0 ? "+" : ""}
                  {fmtPx(focus.change)} ({focus.changePct >= 0 ? "+" : ""}
                  {focus.changePct.toFixed(2)}%)
                </div>
              </div>
              <div className="grid grid-cols-2 gap-x-3 gap-y-1 font-mono text-[10px] text-[#888]">
                <div>
                  Open{" "}
                  <span className="float-right text-[#eee]">
                    {fmtPx(focus.open ?? 0)}
                  </span>
                </div>
                <div>
                  High{" "}
                  <span className="float-right text-[#eee]">
                    {fmtPx(focus.high)}
                  </span>
                </div>
                <div>
                  Prev{" "}
                  <span className="float-right text-[#eee]">
                    {fmtPx(focus.previousClose ?? 0)}
                  </span>
                </div>
                <div>
                  Low{" "}
                  <span className="float-right text-[#eee]">
                    {fmtPx(focus.low)}
                  </span>
                </div>
                <div className="col-span-2">
                  Vol{" "}
                  <span className="float-right text-[#eee]">
                    {focus.volume.toLocaleString()}
                  </span>
                </div>
              </div>
              <button
                type="button"
                className="bg-[#ff6600] px-2 py-1 text-[10px] font-bold text-black"
                onClick={() => onGoEquity?.()}
              >
                OPEN EQUITY
              </button>
            </div>
          ) : (
            <p className="text-[10px] text-[#555]">
              {loading ? "Loading" : "No quote"}
            </p>
          )}
        </Panel>

        <Panel title="Market News" className="lg:col-span-4">
          <ul className="space-y-1.5 text-[10px]">
            {(bundle?.news || []).map((a) => (
              <li
                key={a.link + a.title}
                className="border-b border-[#1a1a1a] pb-1"
              >
                <div className="font-mono text-[9px] text-[#555]">
                  {a.source} | {a.published?.slice(0, 16)}
                </div>
                <a
                  href={a.link}
                  target="_blank"
                  rel="noreferrer"
                  className="leading-snug text-[#ccc] hover:text-[#ff8800]"
                >
                  {a.title}
                </a>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Live TV" className="lg:col-span-2" bodyClassName="p-0">
          <div className="flex h-full min-h-[160px] flex-col bg-black">
            <iframe
              title="Yahoo Finance Live"
              className="min-h-[140px] w-full flex-1 border-0"
              src="https://www.youtube.com/embed/live_stream?channel=UCEAZeUIeJs0IjQiqTCdVSIg"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        </Panel>
      </div>
    </div>
  );
}
