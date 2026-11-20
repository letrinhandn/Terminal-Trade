"use client";

import { useEffect, useState } from "react";
import type { NewsArticle, OverviewSub, QuoteSnapshot } from "@/lib/types";
import { apiGet } from "@/lib/api";
import { CandleChart } from "@/components/charts/CandleChart";
import { useOhlcv } from "@/components/charts/useOhlcv";

type Fundamentals = {
  sector: string | null;
  industry: string | null;
  summary: string | null;
  summaryDetail: Record<string, unknown> | null;
  defaultKeyStatistics: Record<string, unknown> | null;
};

export function OverviewTab({
  symbol,
  sub,
  onSymbolChange,
  onSubChange,
}: {
  symbol: string;
  sub: OverviewSub;
  onSymbolChange: (s: string) => void;
  onSubChange: (s: OverviewSub) => void;
}) {
  const [quote, setQuote] = useState<QuoteSnapshot | null>(null);
  const [fundamentals, setFundamentals] = useState<Fundamentals | null>(null);
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [company, setCompany] = useState<Record<string, unknown> | null>(null);
  const [financials, setFinancials] = useState<Record<string, unknown> | null>(
    null,
  );
  const [freq, setFreq] = useState<"annual" | "quarterly">("annual");
  const [log, setLog] = useState<string[]>([]);
  const [localSym, setLocalSym] = useState(symbol);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { bars: candleBars, sourceNote: candleNote } = useOhlcv(symbol, "1Y");

  useEffect(() => setLocalSym(symbol), [symbol]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [q, f, n] = await Promise.all([
          apiGet<QuoteSnapshot>(`/api/quote?symbol=${encodeURIComponent(symbol)}`),
          apiGet<Fundamentals>(
            `/api/fundamentals?symbol=${encodeURIComponent(symbol)}`,
          ),
          apiGet<{ articles: NewsArticle[] }>(
            `/api/news?q=${encodeURIComponent(symbol)}`,
          ),
        ]);
        if (cancelled) return;
        setQuote(q);
        setFundamentals(f);
        setNews(n.articles || []);
        setLog((L) =>
          [`${new Date().toLocaleTimeString()} Loaded ${symbol}`, ...L].slice(
            0,
            40,
          ),
        );
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e));
          setLog((L) => [`Error: ${e}`, ...L]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [symbol]);

  useEffect(() => {
    if (sub !== "info") return;
    let cancelled = false;
    setCompany(null);
    apiGet<Record<string, unknown>>(
      `/api/company?symbol=${encodeURIComponent(symbol)}`,
    )
      .then((d) => {
        if (!cancelled) setCompany(d);
      })
      .catch((e) => {
        if (!cancelled) {
          setCompany({
            error: e instanceof Error ? e.message : String(e),
            configured: !String(e).includes("not configured"),
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [symbol, sub]);

  useEffect(() => {
    if (sub !== "fin") return;
    let cancelled = false;
    setFinancials(null);
    apiGet<Record<string, unknown>>(
      `/api/financials?symbol=${encodeURIComponent(symbol)}&freq=${freq}`,
    )
      .then((d) => {
        if (!cancelled) setFinancials(d);
      })
      .catch((e) => {
        if (!cancelled) {
          setFinancials({
            error: e instanceof Error ? e.message : String(e),
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [symbol, sub, freq]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-[#333] bg-[#111] px-3 py-2">
        {(["market", "info", "fin"] as OverviewSub[]).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSubChange(s)}
            className={`rounded px-3 py-1 text-xs font-bold uppercase ${
              sub === s ? "bg-[#ff6600] text-black" : "bg-[#1a1a1a] text-[#aaa]"
            }`}
          >
            {s === "fin" ? "Financials" : s}
          </button>
        ))}
        <form
          className="ml-auto flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            const next = localSym.trim().toUpperCase();
            if (next) onSymbolChange(next);
          }}
        >
          <input
            value={localSym}
            onChange={(e) => setLocalSym(e.target.value.toUpperCase())}
            className="rounded border border-[#ff6600] bg-black px-2 py-1 font-mono text-sm text-[#ff8800]"
          />
          <button
            type="submit"
            className="rounded bg-[#ff6600] px-3 py-1 text-xs font-bold text-black"
          >
            Load
          </button>
        </form>
      </div>

      {error && (
        <div className="border-b border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      {sub === "market" && (
        <div className="grid flex-1 gap-3 p-3 lg:grid-cols-[220px_1fr_280px]">
          <aside className="space-y-3">
            <Panel title="PRICE">
              {loading && !quote ? (
                <p className="text-sm text-[#888]">Loading</p>
              ) : quote ? (
                <div className="font-mono text-sm">
                  <div className="text-xl font-bold text-[#ff9500]">
                    {quote.price.toFixed(2)}
                  </div>
                  <div
                    className={
                      quote.change >= 0 ? "text-emerald-400" : "text-red-400"
                    }
                  >
                    {quote.change.toFixed(2)} ({quote.changePct.toFixed(2)}%)
                  </div>
                  <div className="mt-2 text-[#aaa]">{quote.name}</div>
                  <div className="mt-1 text-xs text-[#888]">
                    H {quote.high.toFixed(2)} / L {quote.low.toFixed(2)}
                  </div>
                  <div className="text-xs text-[#888]">
                    Vol {quote.volume.toLocaleString()}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-[#888]">No quote</p>
              )}
            </Panel>
            <Panel title="FUNDAMENTALS">
              <div className="font-mono text-xs text-[#bbb] space-y-1">
                <div>Sector: {fundamentals?.sector ?? "-"}</div>
                <div>Industry: {fundamentals?.industry ?? "-"}</div>
                <div>
                  Mkt Cap:{" "}
                  {quote?.marketCap != null
                    ? quote.marketCap.toLocaleString()
                    : "-"}
                </div>
                <div>PE: {quote?.peRatio != null ? quote.peRatio.toFixed(2) : "-"}</div>
              </div>
            </Panel>
          </aside>
          <section className="min-h-[420px] overflow-hidden rounded border border-[#ff6600] p-2">
            <CandleChart
              bars={candleBars}
              height={400}
              smaPeriods={[20, 50]}
              sourceNote={candleNote}
            />
          </section>
          <aside>
            <Panel title="LIVE NEWS">
              <ul className="max-h-[70vh] space-y-2 overflow-auto text-xs">
                {news.map((a) => (
                  <li key={a.link + a.title} className="border-b border-[#222] pb-2">
                    <a
                      href={a.link}
                      target="_blank"
                      rel="noreferrer"
                      className="font-semibold text-[#ff8800] hover:underline"
                    >
                      {a.title}
                    </a>
                    <div className="text-[#666]">
                      {a.source} | {new Date(a.published).toLocaleString()}
                    </div>
                  </li>
                ))}
                {!news.length && (
                  <li className="text-[#666]">No articles yet</li>
                )}
              </ul>
            </Panel>
          </aside>
        </div>
      )}

      {sub === "info" && (
        <div className="p-4">
          <Panel title="COMPANY INFO (Finnhub)">
            {!company ? (
              <p className="text-sm text-[#888]">Loading</p>
            ) : company.error ? (
              <p className="text-sm text-[#ff8800]">{String(company.error)}</p>
            ) : (
              <p className="text-xs text-[#888]">
                Use Equity (F3) for company data.
                data. Raw dump removed.
              </p>
            )}
          </Panel>
        </div>
      )}

      {sub === "fin" && (
        <div className="space-y-3 p-4">
          <div className="flex gap-2">
            {(["annual", "quarterly"] as const).map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFreq(f)}
                className={`rounded px-3 py-1 text-xs font-bold uppercase ${
                  freq === f ? "bg-[#ff6600] text-black" : "bg-[#1a1a1a] text-[#aaa]"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
          <Panel title="FINANCIAL STATEMENTS">
            {!financials ? (
              <p className="text-sm text-[#888]">Loading</p>
            ) : financials.error ? (
              <p className="text-sm text-[#ff8800]">{String(financials.error)}</p>
            ) : (
              <p className="text-xs text-[#888]">
                Use Equity Financials for statements.
              </p>
            )}
          </Panel>
        </div>
      )}

      <div className="border-t border-[#333] bg-[#0a0a0a] px-3 py-2 font-mono text-[11px] text-[#888]">
        {log[0] || "Overview ready"}
      </div>
    </div>
  );
}

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded border-2 border-[#ff6600] bg-black">
      <div className="border-b border-[#ff6600] px-3 py-2 text-xs font-bold tracking-wide text-[#ff6600]">
        {title}
      </div>
      <div className="p-3">{children}</div>
    </div>
  );
}
