import YahooFinance from "yahoo-finance2";
import type { OhlcvBar, QuoteSnapshot } from "@/lib/types";

const yf = new YahooFinance({ suppressNotices: ["yahooSurvey"] });

const CRYPTO = new Set([
  "BTC",
  "ETH",
  "SOL",
  "DOGE",
  "AVAX",
  "ADA",
  "DOT",
  "LINK",
  "XRP",
  "LTC",
  "BNB",
  "MATIC",
  "NEAR",
  "ATOM",
]);

export function formatYahooSymbol(symbol: string): string {
  const s = symbol.trim().toUpperCase();
  if (!s) throw new Error("Symbol is required");
  if (s.includes("-") || s.startsWith("^")) return s;
  if (CRYPTO.has(s)) return `${s}-USD`;
  const indices: Record<string, string> = {
    SPX: "^GSPC",
    DJI: "^DJI",
    NASDAQ: "^IXIC",
    IXIC: "^IXIC",
    VIX: "^VIX",
    NDX: "^NDX",
    RUT: "^RUT",
  };
  return indices[s] ?? s;
}

export async function fetchQuote(symbol: string): Promise<QuoteSnapshot> {
  const ysym = formatYahooSymbol(symbol);
  const q = await yf.quote(ysym);
  const price = Number(q.regularMarketPrice ?? 0);
  if (!Number.isFinite(price) || price <= 0) {
    throw new Error(`No quote for ${symbol}`);
  }
  const prev = Number(q.regularMarketPreviousClose ?? price);
  const change = price - prev;
  return {
    symbol: symbol.toUpperCase(),
    name: String(q.shortName || q.longName || symbol),
    price,
    change,
    changePct: prev ? (change / prev) * 100 : 0,
    open: Number(q.regularMarketOpen ?? price),
    previousClose: prev,
    high: Number(q.regularMarketDayHigh ?? price),
    low: Number(q.regularMarketDayLow ?? price),
    volume: Number(q.regularMarketVolume ?? 0),
    marketCap: q.marketCap != null ? Number(q.marketCap) : undefined,
    peRatio: q.trailingPE != null ? Number(q.trailingPE) : undefined,
    forwardPE: q.forwardPE != null ? Number(q.forwardPE) : undefined,
    sector:
      (q as { sector?: string }).sector ||
      (q as { quoteType?: string }).quoteType ||
      undefined,
    industry: (q as { industry?: string }).industry || undefined,
  };
}

export async function fetchOhlcv(
  symbol: string,
  start: string,
  end?: string,
): Promise<OhlcvBar[]> {
  const ysym = formatYahooSymbol(symbol);
  const period2 = end || new Date().toISOString().slice(0, 10);
  if (start > period2) {
    throw new Error("Start date must be before end date");
  }
  const result = await yf.chart(ysym, {
    period1: start,
    period2,
    interval: "1d",
  });
  const bars = (result.quotes || [])
    .filter((b) => b.close != null && Number.isFinite(Number(b.close)))
    .map((b) => ({
      date: new Date(b.date).toISOString().slice(0, 10),
      open: Number(b.open ?? b.close),
      high: Number(b.high ?? b.close),
      low: Number(b.low ?? b.close),
      close: Number(b.close),
      volume: Number(b.volume ?? 0),
    }));
  if (!bars.length) {
    throw new Error(`No OHLCV bars for ${symbol}`);
  }
  return bars;
}

export async function fetchFundamentals(symbol: string) {
  const ysym = formatYahooSymbol(symbol);
  const summary = await yf.quoteSummary(ysym, {
    modules: [
      "summaryDetail",
      "defaultKeyStatistics",
      "price",
      "summaryProfile",
    ],
  });
  const profile = summary.summaryProfile as
    | { sector?: string; industry?: string; longBusinessSummary?: string }
    | undefined;
  return {
    symbol: symbol.toUpperCase(),
    sector: profile?.sector ?? null,
    industry: profile?.industry ?? null,
    summary: profile?.longBusinessSummary ?? null,
    price: summary.price ?? null,
    summaryDetail: summary.summaryDetail ?? null,
    defaultKeyStatistics: summary.defaultKeyStatistics ?? null,
  };
}

const RESEARCH_MODULES = [
  "summaryProfile",
  "assetProfile",
  "summaryDetail",
  "defaultKeyStatistics",
  "financialData",
  "price",
  "incomeStatementHistory",
  "incomeStatementHistoryQuarterly",
  "balanceSheetHistory",
  "balanceSheetHistoryQuarterly",
  "cashflowStatementHistory",
  "cashflowStatementHistoryQuarterly",
  "earnings",
  "earningsHistory",
  "earningsTrend",
  "calendarEvents",
  "upgradeDowngradeHistory",
  "institutionOwnership",
  "fundOwnership",
  "majorHoldersBreakdown",
  "insiderHolders",
  "insiderTransactions",
  "netSharePurchaseActivity",
  "secFilings",
  "recommendationTrend",
] as const;

/** Equity research pack via Yahoo quoteSummary. */
export async function fetchYahooResearchBundle(symbol: string) {
  const ysym = formatYahooSymbol(symbol);
  try {
    const summary = await yf.quoteSummary(ysym, {
      // Cast: yahoo-finance2 QuoteSummaryModules union
      modules: [...RESEARCH_MODULES] as Parameters<
        typeof yf.quoteSummary
      >[1] extends { modules?: infer M }
        ? M extends (infer U)[] | "all" | undefined
          ? U[]
          : never
        : never,
    });
    return {
      symbol: symbol.toUpperCase(),
      raw: summary as Record<string, unknown>,
    };
  } catch {
    // Some symbols reject ESG/ownership modules - fall back to core set
    const summary = await yf.quoteSummary(ysym, {
      modules: [
        "summaryProfile",
        "summaryDetail",
        "defaultKeyStatistics",
        "financialData",
        "price",
        "incomeStatementHistory",
        "balanceSheetHistory",
        "cashflowStatementHistory",
        "earnings",
        "earningsHistory",
        "calendarEvents",
      ],
    });
    return {
      symbol: symbol.toUpperCase(),
      raw: summary as Record<string, unknown>,
    };
  }
}

function asRows(node: unknown, nestedKey: string): Record<string, unknown>[] {
  if (!node || typeof node !== "object") return [];
  const inner = (node as Record<string, unknown>)[nestedKey];
  return Array.isArray(inner) ? (inner as Record<string, unknown>[]) : [];
}

export async function fetchFinancialStatements(
  symbol: string,
  period: "annual" | "quarterly" = "annual",
) {
  const { raw } = await fetchYahooResearchBundle(symbol);
  const incomeKey =
    period === "annual"
      ? "incomeStatementHistory"
      : "incomeStatementHistoryQuarterly";
  const balanceKey =
    period === "annual" ? "balanceSheetHistory" : "balanceSheetHistoryQuarterly";
  const cashKey =
    period === "annual"
      ? "cashflowStatementHistory"
      : "cashflowStatementHistoryQuarterly";

  return {
    symbol: symbol.toUpperCase(),
    period,
    income: asRows(raw[incomeKey], "incomeStatementHistory"),
    balance: asRows(raw[balanceKey], "balanceSheetStatements"),
    cashflow: asRows(raw[cashKey], "cashflowStatements"),
    financialData: raw.financialData ?? null,
  };
}

export async function fetchEarningsPack(symbol: string) {
  const { raw } = await fetchYahooResearchBundle(symbol);
  return {
    symbol: symbol.toUpperCase(),
    earnings: raw.earnings ?? null,
    earningsHistory: raw.earningsHistory ?? null,
    earningsTrend: raw.earningsTrend ?? null,
    recommendationTrend: raw.recommendationTrend ?? null,
    upgradeDowngradeHistory: raw.upgradeDowngradeHistory ?? null,
  };
}

export async function fetchCalendarPack(symbol: string) {
  const { raw } = await fetchYahooResearchBundle(symbol);
  return {
    symbol: symbol.toUpperCase(),
    calendarEvents: raw.calendarEvents ?? null,
    earnings: raw.earnings ?? null,
  };
}

export async function fetchOwnershipPack(symbol: string) {
  const { raw } = await fetchYahooResearchBundle(symbol);
  return {
    symbol: symbol.toUpperCase(),
    majorHoldersBreakdown: raw.majorHoldersBreakdown ?? null,
    institutionOwnership: raw.institutionOwnership ?? null,
    fundOwnership: raw.fundOwnership ?? null,
    insiderHolders: raw.insiderHolders ?? null,
    insiderTransactions: raw.insiderTransactions ?? null,
    defaultKeyStatistics: raw.defaultKeyStatistics ?? null,
  };
}

export async function fetchEsgPack(symbol: string) {
  const { raw } = await fetchYahooResearchBundle(symbol);
  return {
    symbol: symbol.toUpperCase(),
    esgScores: raw.esgScores ?? null,
    summaryProfile: raw.summaryProfile ?? null,
  };
}
