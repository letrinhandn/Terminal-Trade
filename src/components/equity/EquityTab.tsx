"use client";

import { useEffect, useState } from "react";
import type { QuoteSnapshot } from "@/lib/types";
import { apiGet } from "@/lib/api";
import { CandleChart } from "@/components/charts/CandleChart";
import { RangeChips } from "@/components/charts/RangeChips";
import { TradeVizChord } from "@/components/charts/TradeVizChord";
import {
  type ChartRange,
} from "@/components/charts/chartTheme";
import { useOhlcv } from "@/components/charts/useOhlcv";
import {
  JsonList,
  Panel,
  StatGrid,
  StatementTable,
  fmt,
  pick,
  RecommendationBars,
  EarningsQuarterTable,
  CalendarEventCards,
  SecFilingsList,
} from "@/components/equity/EquityWidgets";

type EquitySub =
  | "overview"
  | "financials"
  | "analysis"
  | "ownership"
  | "peers"
  | "calendar"
  | "esg";

type Envelope<T> = {
  data: T;
  meta?: { provider?: string; latencyMs?: number; warnings?: string[] };
};

type OverviewData = {
  quote: QuoteSnapshot;
  widgets: Record<string, unknown>;
  finnhub?: {
    profile?: Record<string, unknown>;
    metrics?: { metric?: Record<string, unknown> };
    recommendations?: unknown;
    price_targets?: Record<string, unknown>;
    peers?: string[];
  } | null;
};

const SUBS: { id: EquitySub; label: string }[] = [
  { id: "overview", label: "OVERVIEW" },
  { id: "financials", label: "FINANCIALS" },
  { id: "analysis", label: "ANALYSIS" },
  { id: "ownership", label: "OWNERSHIP" },
  { id: "peers", label: "PEERS" },
  { id: "calendar", label: "CALENDAR" },
  { id: "esg", label: "ESG" },
];

const INCOME_FIELDS = [
  { key: "totalRevenue", label: "Revenue" },
  { key: "grossProfit", label: "Gross profit" },
  { key: "operatingIncome", label: "Operating income" },
  { key: "netIncome", label: "Net income" },
  { key: "ebit", label: "EBIT" },
];

const BALANCE_FIELDS = [
  { key: "totalAssets", label: "Total assets" },
  { key: "totalLiab", label: "Total liabilities" },
  { key: "totalStockholderEquity", label: "Equity" },
  { key: "cash", label: "Cash" },
  { key: "longTermDebt", label: "LT debt" },
];

const CF_FIELDS = [
  { key: "totalCashFromOperatingActivities", label: "CFO" },
  { key: "capitalExpenditures", label: "CapEx" },
  { key: "totalCashflowsFromInvestingActivities", label: "CFI" },
  { key: "totalCashFromFinancingActivities", label: "CFF" },
];

function pct(v: unknown): string {
  if (typeof v !== "number" || !Number.isFinite(v)) return "-";
  // Finnhub often returns already as percent; Yahoo ratios as fractions
  const n = Math.abs(v) <= 1 ? v * 100 : v;
  return `${n.toFixed(2)}%`;
}

export function EquityTab({
  symbol,
  onSymbolChange,
  onStatus,
  onGoSignals,
  onGoNews,
}: {
  symbol: string;
  onSymbolChange: (s: string) => void;
  onStatus?: (s: string) => void;
  onGoSignals?: () => void;
  onGoNews?: () => void;
}) {
  const [local, setLocal] = useState(symbol);
  const [sub, setSub] = useState<EquitySub>("overview");
  const [period, setPeriod] = useState<"annual" | "quarterly">("annual");
  const [chartRange, setChartRange] = useState<ChartRange>("1Y");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { bars: candleBars, loading: candleLoading } = useOhlcv(
    symbol,
    chartRange,
  );

  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [financials, setFinancials] = useState<Record<string, unknown> | null>(
    null,
  );
  const [earnings, setEarnings] = useState<Record<string, unknown> | null>(null);
  const [calendar, setCalendar] = useState<Record<string, unknown> | null>(null);
  const [ownership, setOwnership] = useState<Record<string, unknown> | null>(
    null,
  );
  const [esg, setEsg] = useState<Record<string, unknown> | null>(null);

  useEffect(() => setLocal(symbol), [symbol]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        if (sub === "overview" || sub === "peers") {
          const res = await apiGet<Envelope<OverviewData>>(
            `/api/v1/equity/overview?symbol=${encodeURIComponent(symbol)}`,
          );
          if (!cancelled) {
            setOverview(res.data);
            onStatus?.(
              `Equity ${sub} | ${res.meta?.provider} | ${res.meta?.latencyMs ?? "?"}ms`,
            );
          }
        } else if (sub === "financials") {
          const res = await apiGet<Envelope<Record<string, unknown>>>(
            `/api/v1/equity/fundamental?symbol=${encodeURIComponent(symbol)}&period=${period}`,
          );
          if (!cancelled) {
            setFinancials(res.data);
            onStatus?.(
              `Financials ${period} | ${res.meta?.provider} | ${res.meta?.latencyMs ?? "?"}ms`,
            );
          }
        } else if (sub === "analysis") {
          const res = await apiGet<Envelope<Record<string, unknown>>>(
            `/api/v1/equity/earnings?symbol=${encodeURIComponent(symbol)}`,
          );
          if (!cancelled) {
            setEarnings(res.data);
            onStatus?.(
              `Analysis | ${res.meta?.provider} | ${res.meta?.latencyMs ?? "?"}ms`,
            );
          }
        } else if (sub === "calendar") {
          const res = await apiGet<Envelope<Record<string, unknown>>>(
            `/api/v1/equity/calendar?symbol=${encodeURIComponent(symbol)}`,
          );
          if (!cancelled) {
            setCalendar(res.data);
            onStatus?.(
              `Calendar | ${res.meta?.provider} | ${res.meta?.latencyMs ?? "?"}ms`,
            );
          }
        } else if (sub === "ownership") {
          const res = await apiGet<Envelope<Record<string, unknown>>>(
            `/api/v1/equity/ownership?symbol=${encodeURIComponent(symbol)}`,
          );
          if (!cancelled) {
            setOwnership(res.data);
            onStatus?.(
              `Ownership | ${res.meta?.provider} | ${res.meta?.latencyMs ?? "?"}ms`,
            );
          }
        } else if (sub === "esg") {
          const res = await apiGet<Envelope<Record<string, unknown>>>(
            `/api/v1/equity/esg?symbol=${encodeURIComponent(symbol)}`,
          );
          if (!cancelled) {
            setEsg(res.data);
            onStatus?.(
              `ESG | ${res.meta?.provider} | ${res.meta?.latencyMs ?? "?"}ms`,
            );
          }
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [symbol, sub, period, onStatus]);

  const quote = overview?.quote;
  const w = overview?.widgets;
  const fh = overview?.finnhub;
  const metric = fh?.metrics?.metric;
  const targets = fh?.price_targets;
  const up = (quote?.changePct ?? 0) >= 0;

  return (
    <div className="flex min-h-full flex-col bg-black">
      {/* Research header */}
      <div className="border-b border-[#2a2a2a] bg-[#050505] px-4 py-3">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-baseline gap-3">
            <h2 className="font-display text-lg font-bold text-[#ff8c00]">
              Equity Research: {symbol}
            </h2>
            {quote && (
              <>
                <span className="font-mono text-2xl text-white">
                  ${quote.price.toFixed(2)}
                </span>
                <span
                  className={`font-mono text-sm ${up ? "text-emerald-400" : "text-red-400"}`}
                >
                  {up ? "+" : ""}
                  {quote.change.toFixed(2)} ({up ? "+" : ""}
                  {quote.changePct.toFixed(2)}%)
                </span>
                <span className="font-mono text-[11px] text-[#888]">
                  Vol {fmt(quote.volume)} | H {quote.high.toFixed(2)} / L{" "}
                  {quote.low.toFixed(2)}
                </span>
              </>
            )}
          </div>
          <div className="flex flex-wrap items-end gap-2">
            <input
              value={local}
              onChange={(e) => setLocal(e.target.value.toUpperCase())}
              onKeyDown={(e) => {
                if (e.key === "Enter")
                  onSymbolChange(local.trim().toUpperCase());
              }}
              className="w-28 rounded border border-[#ff8c00] bg-black px-2 py-1 font-mono text-sm text-[#ff8c00]"
            />
            <button
              type="button"
              className="rounded bg-[#ff8c00] px-3 py-1 text-xs font-bold text-black"
              onClick={() => onSymbolChange(local.trim().toUpperCase())}
            >
              Load
            </button>
            <button
              type="button"
              className="rounded border border-[#333] px-2 py-1 text-[10px] text-[#40e0d0]"
              onClick={onGoSignals}
            >
              TECHNICALS
            </button>
            <button
              type="button"
              className="rounded border border-[#333] px-2 py-1 text-[10px] text-[#40e0d0]"
              onClick={onGoNews}
            >
              NEWS
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-1 border-b border-[#222] pb-0">
          {SUBS.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setSub(s.id)}
              className={`border-b-2 px-3 py-2 text-[11px] font-bold tracking-wide ${
                sub === s.id
                  ? "border-[#ff8c00] text-[#ff8c00]"
                  : "border-transparent text-[#888] hover:text-[#40e0d0]"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <p className="px-4 py-2 text-sm text-[#666]">Loading research</p>
      )}
      {error && <p className="px-4 py-2 text-sm text-red-400">{error}</p>}

      <div className="flex-1 space-y-3 p-3">
        {sub === "overview" && overview && (
          <>
            <div className="grid gap-3 lg:grid-cols-12">
              {/* Left columns */}
              <div className="space-y-3 lg:col-span-3">
                <Panel title="Today's Trading">
                  <StatGrid
                    rows={[
                      { label: "Open", value: quote?.open?.toFixed(2) },
                      { label: "High", value: quote?.high?.toFixed(2) },
                      { label: "Low", value: quote?.low?.toFixed(2) },
                      {
                        label: "Prev Close",
                        value: quote?.previousClose?.toFixed(2),
                      },
                      { label: "Volume", value: fmt(quote?.volume) },
                    ]}
                  />
                </Panel>
                <Panel title="Valuation">
                  <StatGrid
                    rows={[
                      { label: "Market Cap", value: fmt(quote?.marketCap) },
                      { label: "P/E Ratio", value: quote?.peRatio?.toFixed(2) },
                      {
                        label: "FWD P/E",
                        value:
                          quote?.forwardPE?.toFixed(2) ??
                          fmt(pick(w?.summaryDetail, "forwardPE")),
                      },
                      {
                        label: "PEG Ratio",
                        value: fmt(
                          metric?.pegRatio ?? pick(w?.keyStats, "pegRatio"),
                        ),
                      },
                      {
                        label: "P/B Ratio",
                        value: fmt(
                          metric?.pb ?? pick(w?.keyStats, "priceToBook"),
                        ),
                      },
                      {
                        label: "Div Yield",
                        value: pct(
                          pick(w?.summaryDetail, "dividendYield") ??
                            metric?.dividendYieldIndicatedAnnual,
                        ),
                      },
                      {
                        label: "Beta",
                        value: fmt(
                          pick(w?.summaryDetail, "beta") ?? metric?.beta,
                        ),
                      },
                    ]}
                  />
                </Panel>
                <Panel title="Share Stats">
                  <StatGrid
                    rows={[
                      {
                        label: "Shares Out",
                        path: "sharesOutstanding",
                        src: w?.keyStats,
                      },
                      {
                        label: "Float",
                        path: "floatShares",
                        src: w?.keyStats,
                      },
                      {
                        label: "Insiders",
                        value: pct(
                          pick(w?.keyStats, "heldPercentInsiders") ??
                            metric?.insiderOwnership,
                        ),
                      },
                      {
                        label: "Institutions",
                        value: pct(
                          pick(w?.keyStats, "heldPercentInstitutions") ??
                            metric?.institutionalOwnership,
                        ),
                      },
                      {
                        label: "Short %",
                        value: pct(
                          pick(w?.keyStats, "shortPercentOfFloat") ??
                            metric?.shortPercentOutstanding,
                        ),
                      },
                    ]}
                  />
                </Panel>
              </div>

              {/* Center chart: native candles */}
              <Panel title="Charting" className="min-h-[420px] lg:col-span-6">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <RangeChips value={chartRange} onChange={setChartRange} />
                  <span className="font-mono text-[9px] text-[#666]">
                    SMA 20 / 50
                    {candleLoading ? " loading" : ""}
                  </span>
                </div>
                <CandleChart
                  bars={candleBars}
                  height={380}
                  smaPeriods={[20, 50]}
                  emptyLabel={
                    candleLoading ? "Loading candles" : "No OHLCV for this symbol"
                  }
                />
              </Panel>

              {/* Right cards */}
              <div className="space-y-3 lg:col-span-3">
                <Panel title="Analyst Targets">
                  <StatGrid
                    rows={[
                      {
                        label: "High",
                        value: fmt(
                          targets?.targetHigh ??
                            pick(w?.financialData, "targetHighPrice"),
                        ),
                      },
                      {
                        label: "Mean",
                        value: fmt(
                          targets?.targetMean ??
                            pick(w?.financialData, "targetMeanPrice"),
                        ),
                      },
                      {
                        label: "Low",
                        value: fmt(
                          targets?.targetLow ??
                            pick(w?.financialData, "targetLowPrice"),
                        ),
                      },
                      {
                        label: "Rec",
                        value: String(
                          pick(w?.financialData, "recommendationKey") ??
                            (Array.isArray(fh?.recommendations)
                              ? (fh?.recommendations[0] as { buy?: number })
                                  ?.buy != null
                                ? "see Analysis"
                                : "-"
                              : "-"),
                        ),
                      },
                    ]}
                  />
                </Panel>
                <Panel title="52 Week Range">
                  <StatGrid
                    rows={[
                      {
                        label: "High",
                        value: fmt(pick(w?.summaryDetail, "fiftyTwoWeekHigh")),
                      },
                      {
                        label: "Low",
                        value: fmt(pick(w?.summaryDetail, "fiftyTwoWeekLow")),
                      },
                      {
                        label: "Avg Vol",
                        value: fmt(
                          pick(w?.summaryDetail, "averageVolume") ??
                            pick(w?.keyStats, "averageVolume"),
                        ),
                      },
                    ]}
                  />
                </Panel>
                <Panel title="Profitability">
                  <StatGrid
                    rows={[
                      {
                        label: "Gross Margin",
                        value: pct(
                          pick(w?.financialData, "grossMargins") ??
                            metric?.grossMarginTTM,
                        ),
                      },
                      {
                        label: "Oper. Margin",
                        value: pct(
                          pick(w?.financialData, "operatingMargins") ??
                            metric?.operatingMarginTTM,
                        ),
                      },
                      {
                        label: "Profit Margin",
                        value: pct(
                          pick(w?.financialData, "profitMargins") ??
                            metric?.netProfitMarginTTM,
                        ),
                      },
                      {
                        label: "ROA",
                        value: pct(
                          pick(w?.financialData, "returnOnAssets") ??
                            metric?.roaTTM,
                        ),
                      },
                      {
                        label: "ROE",
                        value: pct(
                          pick(w?.financialData, "returnOnEquity") ??
                            metric?.roeTTM,
                        ),
                      },
                    ]}
                  />
                </Panel>
                <Panel title="Growth Rates">
                  <StatGrid
                    rows={[
                      {
                        label: "Revenue",
                        value: pct(
                          pick(w?.financialData, "revenueGrowth") ??
                            metric?.revenueGrowthTTMYoy,
                        ),
                        tone: "neutral",
                      },
                      {
                        label: "Earnings",
                        value: pct(
                          pick(w?.financialData, "earningsGrowth") ??
                            metric?.epsGrowthTTMYoy,
                        ),
                        tone: "neutral",
                      },
                    ]}
                  />
                </Panel>
              </div>
            </div>

            {/* Bottom: overview + Trade Viz + info */}
            <div className="grid gap-3 lg:grid-cols-12 lg:items-stretch">
              <Panel
                title="Company Overview"
                className="lg:col-span-5"
                bodyClassName="max-h-[320px]"
              >
                <p className="text-[13px] leading-[1.55] text-[#cfcfcf]">
                  {String(
                    pick(w?.profile, "longBusinessSummary") ??
                      pick(fh?.profile, "finnhubIndustry") ??
                      "-",
                  )}
                </p>
              </Panel>
              <Panel title="Trade Viz" className="lg:col-span-4">
                <TradeVizChord size={280} />
              </Panel>
              <Panel title="Company Info" className="lg:col-span-3">
                <StatGrid
                  rows={[
                    {
                      label: "Employees",
                      value: fmt(
                        pick(w?.profile, "fullTimeEmployees") ??
                          pick(fh?.profile, "employeeTotal"),
                      ),
                    },
                    {
                      label: "Sector",
                      value: String(
                        pick(w?.profile, "sector") ??
                          pick(fh?.profile, "finnhubIndustry") ??
                          "-",
                      ),
                    },
                    {
                      label: "Country",
                      value: String(
                        pick(w?.profile, "country") ??
                          pick(fh?.profile, "country") ??
                          "-",
                      ),
                    },
                    {
                      label: "Website",
                      value: (() => {
                        const url = String(
                          pick(w?.profile, "website") ??
                            pick(fh?.profile, "weburl") ??
                            "",
                        );
                        if (!url || url === "-") return "-";
                        const host = url
                          .replace(/^https?:\/\//, "")
                          .replace(/\/$/, "");
                        return (
                          <a
                            href={url.startsWith("http") ? url : `https://${url}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[#ff8800] hover:underline"
                          >
                            {host}
                          </a>
                        );
                      })(),
                    },
                  ]}
                />
              </Panel>
            </div>
          </>
        )}

        {sub === "financials" && financials && (
          <div className="space-y-3">
            <div className="flex gap-1">
              {(["annual", "quarterly"] as const).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPeriod(p)}
                  className={`rounded px-2 py-1 text-[10px] font-bold uppercase ${
                    period === p ? "bg-[#333] text-[#ff8c00]" : "text-[#666]"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
            <div className="grid gap-3 xl:grid-cols-3">
              <Panel title={`Income (${period})`}>
                <StatementTable
                  rows={(financials.income as Record<string, unknown>[]) || []}
                  fields={INCOME_FIELDS}
                />
              </Panel>
              <Panel title={`Balance (${period})`}>
                <StatementTable
                  rows={(financials.balance as Record<string, unknown>[]) || []}
                  fields={BALANCE_FIELDS}
                />
              </Panel>
              <Panel title={`Cash flow (${period})`}>
                <StatementTable
                  rows={(financials.cashflow as Record<string, unknown>[]) || []}
                  fields={CF_FIELDS}
                />
              </Panel>
            </div>
          </div>
        )}

        {sub === "analysis" && earnings && (
          <div className="grid gap-3 lg:grid-cols-2">
            <Panel title="Earnings history">
              <JsonList
                title="history"
                items={
                  pick(earnings.earningsHistory, "history") ||
                  earnings.earningsHistory
                }
                mapItem={(it) => {
                  const surprise = Number(it.surprisePercent ?? 0);
                  return (
                    <div className="font-mono text-[11px]">
                      <span className="text-[#40e0d0]">
                        {String(it.period || pick(it, "quarter") || "-")}
                      </span>{" "}
                      | EPS {fmt(it.epsActual)} vs est {fmt(it.epsEstimate)}
                      <span
                        className={
                          surprise > 0
                            ? " text-emerald-400"
                            : surprise < 0
                              ? " text-red-400"
                              : " text-[#666]"
                        }
                      >
                        {" "}
                        ({surprise > 0 ? "+" : ""}
                        {(surprise * 100).toFixed(1)}%)
                      </span>
                    </div>
                  );
                }}
              />
            </Panel>
            <Panel title="Analyst recommendations">
              <RecommendationBars trend={earnings.recommendationTrend} />
              {(() => {
                const fh = earnings.finnhub as
                  | { recommendations?: unknown }
                  | null
                  | undefined;
                if (!fh || !Array.isArray(fh.recommendations)) return null;
                return (
                  <div className="mt-4 border-t border-[#1a1a1a] pt-3">
                    <div className="mb-2 text-[10px] tracking-wider text-[#666]">
                      FINNHUB TREND
                    </div>
                    <RecommendationBars trend={fh.recommendations} />
                  </div>
                );
              })()}
            </Panel>
          </div>
        )}

        {sub === "ownership" && ownership && (
          <div className="grid gap-3 lg:grid-cols-2">
            <Panel title="Major holders">
              <StatGrid
                rows={[
                  {
                    label: "Insiders %",
                    path: "insidersPercentHeld",
                    src: ownership.majorHoldersBreakdown,
                  },
                  {
                    label: "Institutions %",
                    path: "institutionsPercentHeld",
                    src: ownership.majorHoldersBreakdown,
                  },
                  {
                    label: "Institutions float %",
                    path: "institutionsFloatPercentHeld",
                    src: ownership.majorHoldersBreakdown,
                  },
                ]}
              />
            </Panel>
            <Panel title="Institutional (top)">
              <JsonList
                title="institutions"
                items={ownership.institutionOwnership}
                mapItem={(it) => (
                  <div>
                    <div className="text-[#ff8c00]">
                      {String(pick(it, "organization") ?? "-")}
                    </div>
                    <div className="font-mono text-[10px] text-[#888]">
                      pct {String(pick(it, "pctHeld") ?? "-")}
                    </div>
                  </div>
                )}
              />
            </Panel>
          </div>
        )}

        {sub === "peers" && overview && (
          <Panel title="Peers (Finnhub)">
            <div className="flex flex-wrap gap-2">
              {(fh?.peers || []).length ? (
                (fh?.peers || []).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => onSymbolChange(p)}
                    className="rounded border border-[#333] px-3 py-2 font-mono text-xs text-[#40e0d0] hover:border-[#ff8c00] hover:text-[#ff8c00]"
                  >
                    {p}
                  </button>
                ))
              ) : (
                <p className="text-xs text-[#666]">
                  No peers. Set FINNHUB_API_KEY for peer data.
                </p>
              )}
            </div>
          </Panel>
        )}

        {sub === "calendar" && calendar && (
          <div className="grid gap-3 lg:grid-cols-2">
            <Panel title="Calendar events">
              <CalendarEventCards events={calendar.calendarEvents} />
            </Panel>
            <Panel title="Earnings (quarterly)">
              <EarningsQuarterTable
                quarterly={pick(calendar.earnings, "earningsChart.quarterly")}
              />
            </Panel>
          </div>
        )}

        {sub === "esg" && esg && (
          <div className="grid gap-3 lg:grid-cols-2">
            <Panel title="Governance & profile">
              <p className="mb-2 text-[10px] text-[#666]">
                {String(esg.note || "")}
              </p>
              {esg.assetProfile ? (
                <StatGrid
                  rows={[
                    {
                      label: "Industry",
                      path: "industry",
                      src: esg.assetProfile,
                    },
                    {
                      label: "Sector",
                      path: "sector",
                      src: esg.assetProfile,
                    },
                    {
                      label: "Employees",
                      path: "fullTimeEmployees",
                      src: esg.assetProfile,
                    },
                    {
                      label: "Audit risk",
                      path: "auditRisk",
                      src: esg.assetProfile,
                    },
                    {
                      label: "Board risk",
                      path: "boardRisk",
                      src: esg.assetProfile,
                    },
                    {
                      label: "Comp risk",
                      path: "compensationRisk",
                      src: esg.assetProfile,
                    },
                    {
                      label: "Shareholder rights",
                      path: "shareHolderRightsRisk",
                      src: esg.assetProfile,
                    },
                    {
                      label: "Overall risk",
                      path: "overallRisk",
                      src: esg.assetProfile,
                    },
                  ]}
                />
              ) : (
                <p className="text-xs text-[#666]">
                  No governance profile from Yahoo for this symbol.
                </p>
              )}
              {esg.netSharePurchaseActivity &&
              typeof esg.netSharePurchaseActivity === "object" ? (
                <div className="mt-3 border-t border-[#1a1a1a] pt-2">
                  <div className="mb-1 text-[10px] tracking-wider text-[#666]">
                    INSIDER ACTIVITY
                  </div>
                  <StatGrid
                    rows={[
                      {
                        label: "Period",
                        path: "period",
                        src: esg.netSharePurchaseActivity,
                      },
                      {
                        label: "Buy count",
                        path: "buyInfoCount",
                        src: esg.netSharePurchaseActivity,
                      },
                      {
                        label: "Sell count",
                        path: "sellInfoCount",
                        src: esg.netSharePurchaseActivity,
                      },
                      {
                        label: "Net shares",
                        path: "netInfoShares",
                        src: esg.netSharePurchaseActivity,
                      },
                    ]}
                  />
                </div>
              ) : null}
            </Panel>
            <Panel title="SEC filings">
              <SecFilingsList filings={esg.secFilings} />
            </Panel>
          </div>
        )}
      </div>
    </div>
  );
}
