import YahooFinance from "yahoo-finance2";
import { fetchNews } from "@/lib/data/news";
import { fetchQuote } from "@/lib/data/yahoo";
import type { NewsArticle, QuoteSnapshot } from "@/lib/types";

const yf = new YahooFinance({ suppressNotices: ["yahooSurvey"] });

export const DASH_INDICES = [
  { id: "^GSPC", label: "S&P 500" },
  { id: "^DJI", label: "Dow" },
  { id: "^IXIC", label: "Nasdaq" },
  { id: "^RUT", label: "Russell 2000" },
  { id: "^N225", label: "Nikkei 225" },
  { id: "^HSI", label: "Hang Seng" },
  { id: "^FTSE", label: "FTSE 100" },
  { id: "^GDAXI", label: "DAX" },
  { id: "^FCHI", label: "CAC 40" },
  { id: "^BSESN", label: "Sensex" },
  { id: "^NSEI", label: "Nifty 50" },
  { id: "^AXJO", label: "ASX 200" },
];

export const DASH_FOREX = [
  { id: "EURUSD=X", label: "EUR/USD" },
  { id: "GBPUSD=X", label: "GBP/USD" },
  { id: "USDJPY=X", label: "USD/JPY" },
  { id: "AUDUSD=X", label: "AUD/USD" },
  { id: "USDCAD=X", label: "USD/CAD" },
  { id: "USDCHF=X", label: "USD/CHF" },
  { id: "NZDUSD=X", label: "NZD/USD" },
  { id: "EURJPY=X", label: "EUR/JPY" },
];

export const DASH_COMMODITIES = [
  { id: "CL=F", label: "Crude WTI" },
  { id: "BZ=F", label: "Brent" },
  { id: "GC=F", label: "Gold" },
  { id: "SI=F", label: "Silver" },
  { id: "HG=F", label: "Copper" },
  { id: "PL=F", label: "Platinum" },
  { id: "PA=F", label: "Palladium" },
  { id: "NG=F", label: "Nat Gas" },
];

export const DASH_SNAPSHOT = [
  { id: "^VIX", label: "VIX" },
  { id: "^TNX", label: "US 10Y" },
  { id: "DX-Y.NYB", label: "DXY" },
  { id: "GC=F", label: "Gold" },
  { id: "CL=F", label: "Oil" },
  { id: "BTC-USD", label: "BTC" },
];

export const DASH_TICKER = [
  "^GSPC",
  "^DJI",
  "^IXIC",
  "^RUT",
  "^GDAXI",
  "^N225",
  "TSLA",
  "NVDA",
  "AAPL",
  "MSFT",
  "AMD",
  "INTC",
  "BTC-USD",
];

export type DashRow = {
  id: string;
  label: string;
  price: number;
  change: number;
  changePct: number;
};

async function quoteRow(
  id: string,
  label: string,
): Promise<DashRow | null> {
  try {
    const q = await yf.quote(id);
    const price = Number(q.regularMarketPrice ?? 0);
    if (!Number.isFinite(price) || price <= 0) return null;
    const prev = Number(q.regularMarketPreviousClose ?? price);
    const change = price - prev;
    const changePct =
      q.regularMarketChangePercent != null
        ? Number(q.regularMarketChangePercent)
        : prev
          ? (change / prev) * 100
          : 0;
    return {
      id,
      label: label || String(q.shortName || id),
      price,
      change,
      changePct,
    };
  } catch {
    return null;
  }
}

async function batchRows(
  defs: { id: string; label: string }[],
): Promise<DashRow[]> {
  const settled = await Promise.all(
    defs.map((d) => quoteRow(d.id, d.label)),
  );
  return settled.filter(Boolean) as DashRow[];
}

async function fetchFearGreed(): Promise<{
  value: number;
  label: string;
  source: string;
} | null> {
  try {
    const res = await fetch("https://api.alternative.me/fng/?limit=1", {
      next: { revalidate: 3600 },
    });
    if (!res.ok) throw new Error(String(res.status));
    const body = (await res.json()) as {
      data?: { value?: string; value_classification?: string }[];
    };
    const row = body.data?.[0];
    if (!row?.value) return null;
    return {
      value: Number(row.value),
      label: row.value_classification || "",
      source: "alternative.me Crypto Fear & Greed",
    };
  } catch {
    return null;
  }
}

async function screenMovers(kind: "day_gainers" | "day_losers", count = 5) {
  try {
    const res = await yf.screener({ scrIds: kind, count });
    const quotes =
      (res as unknown as {
        quotes?: {
          symbol?: string;
          regularMarketPrice?: number;
          regularMarketChangePercent?: number;
          shortName?: string;
        }[];
      }).quotes || [];
    return quotes.slice(0, count).map((q) => ({
      symbol: String(q.symbol || ""),
      price: Number(q.regularMarketPrice ?? 0),
      changePct: Number(q.regularMarketChangePercent ?? 0),
      name: String(q.shortName || q.symbol || ""),
    }));
  } catch {
    return [];
  }
}

/** Breadth proxy: share of ticker tape advancing (real quotes, not NYSE official). */
function breadthFromTape(rows: DashRow[]) {
  if (!rows.length) return null;
  const up = rows.filter((r) => r.changePct > 0).length;
  const down = rows.filter((r) => r.changePct < 0).length;
  const flat = rows.length - up - down;
  return {
    universe: "Dashboard tape",
    up,
    down,
    flat,
    upPct: (up / rows.length) * 100,
    source: "Advance/decline of loaded Yahoo tape (not official NYSE breadth)",
  };
}

export type DashboardBundle = {
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
  breadth: ReturnType<typeof breadthFromTape>;
};

export async function fetchDashboardBundle(
  focusSymbol = "AAPL",
): Promise<DashboardBundle> {
  const [
    indices,
    forex,
    commodities,
    snapshot,
    ticker,
    focus,
    news,
    fearGreed,
    gainers,
    losers,
  ] = await Promise.all([
    batchRows(DASH_INDICES),
    batchRows(DASH_FOREX),
    batchRows(DASH_COMMODITIES),
    batchRows(DASH_SNAPSHOT),
    batchRows(
      DASH_TICKER.map((id) => ({
        id,
        label: id.replace("=X", "").replace("-USD", "").replace("^", ""),
      })),
    ),
    fetchQuote(focusSymbol).catch(() => null),
    fetchNews(12).catch(() => [] as NewsArticle[]),
    fetchFearGreed(),
    screenMovers("day_gainers", 5),
    screenMovers("day_losers", 5),
  ]);

  return {
    indices,
    forex,
    commodities,
    snapshot,
    ticker,
    focus,
    news,
    fearGreed,
    gainers,
    losers,
    breadth: breadthFromTape(ticker),
  };
}
