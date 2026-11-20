import YahooFinance from "yahoo-finance2";
import type { OptionContract } from "@/lib/types";
import { formatYahooSymbol } from "@/lib/data/yahoo";

const yf = new YahooFinance({ suppressNotices: ["yahooSurvey"] });

type YahooOpt = {
  contractSymbol?: string;
  strike?: number;
  lastPrice?: number;
  bid?: number;
  ask?: number;
  volume?: number;
  openInterest?: number;
  impliedVolatility?: number;
  expiration?: Date | string | number;
};

function toExpiry(v: Date | string | number | undefined): string {
  if (v == null) return "";
  const d = v instanceof Date ? v : new Date(v);
  if (Number.isNaN(d.getTime())) return "";
  return d.toISOString().slice(0, 10);
}

function saneIv(iv: number | undefined): number | null {
  if (iv == null || !Number.isFinite(iv)) return null;
  // Yahoo often returns near-zero junk for stale / deep ITM rows
  if (iv < 0.001 || iv > 5) return null;
  return iv;
}

function mapSide(
  rows: YahooOpt[] | undefined,
  optionType: "C" | "P",
  underlyingPrice: number | null,
): OptionContract[] {
  const out: OptionContract[] = [];
  for (const r of rows || []) {
    const strike = Number(r.strike);
    if (!Number.isFinite(strike)) continue;
    out.push({
      instrument: r.contractSymbol || `${optionType}-${strike}`,
      expiry: toExpiry(r.expiration),
      strike,
      optionType,
      markPrice: r.lastPrice ?? null,
      bid: r.bid ?? null,
      ask: r.ask ?? null,
      iv: saneIv(r.impliedVolatility),
      delta: null,
      gamma: null,
      theta: null,
      vega: null,
      underlyingPrice,
      volume: r.volume ?? null,
      openInterest: r.openInterest ?? null,
    });
  }
  return out;
}

/**
 * Equity / ETF options via Yahoo Finance (free).
 * No greeks from Yahoo. IV may be missing on stale contracts.
 */
export async function fetchYahooOptionsChain(
  symbol: string,
  date?: Date,
): Promise<{
  symbol: string;
  underlyingPrice: number | null;
  expirations: string[];
  contracts: OptionContract[];
}> {
  const ysym = formatYahooSymbol(symbol);
  const raw = date
    ? await yf.options(ysym, { date })
    : await yf.options(ysym);

  const quotePrice = Number(
    (raw as { quote?: { regularMarketPrice?: number } }).quote
      ?.regularMarketPrice,
  );
  const underlyingPrice =
    Number.isFinite(quotePrice) && quotePrice > 0 ? quotePrice : null;

  const expirations = ((raw.expirationDates as (Date | string)[]) || [])
    .map((d) => toExpiry(d))
    .filter(Boolean);

  const slices = (raw.options || []) as {
    calls?: YahooOpt[];
    puts?: YahooOpt[];
  }[];

  const contracts: OptionContract[] = [];
  for (const slice of slices) {
    contracts.push(...mapSide(slice.calls, "C", underlyingPrice));
    contracts.push(...mapSide(slice.puts, "P", underlyingPrice));
  }

  contracts.sort(
    (a, b) => a.expiry.localeCompare(b.expiry) || a.strike - b.strike,
  );

  return {
    symbol: symbol.toUpperCase(),
    underlyingPrice,
    expirations,
    contracts,
  };
}
