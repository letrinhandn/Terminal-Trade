import type { OptionContract } from "@/lib/types";

const BASE = "https://www.deribit.com/api/v2";

async function deribitGet<T>(
  method: string,
  params: Record<string, string | number | boolean>,
): Promise<T> {
  const url = new URL(`${BASE}/${method}`);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)));
  const res = await fetch(url.toString(), { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`Deribit ${res.status}`);
  const json = (await res.json()) as { result: T; error?: unknown };
  if (json.error) throw new Error(JSON.stringify(json.error));
  return json.result;
}

function parseExpiry(
  instrument: string,
): { expiry: string; strike: number; optionType: "C" | "P" } | null {
  const parts = instrument.split("-");
  if (parts.length < 4) return null;
  const expStr = parts[1];
  const strike = Number(parts[2]);
  const optionType = parts[3] as "C" | "P";
  const m = expStr.match(/^(\d{1,2})([A-Z]{3})(\d{2})$/i);
  if (!m) return null;
  const months: Record<string, number> = {
    JAN: 0,
    FEB: 1,
    MAR: 2,
    APR: 3,
    MAY: 4,
    JUN: 5,
    JUL: 6,
    AUG: 7,
    SEP: 8,
    OCT: 9,
    NOV: 10,
    DEC: 11,
  };
  const year = 2000 + Number(m[3]);
  const dt = new Date(Date.UTC(year, months[m[2].toUpperCase()], Number(m[1])));
  return { expiry: dt.toISOString().slice(0, 10), strike, optionType };
}

type BookSummary = {
  instrument_name: string;
  mark_price?: number;
  underlying_price?: number;
  /** book summary uses bid_price / ask_price */
  bid_price?: number;
  ask_price?: number;
  best_bid_price?: number;
  best_ask_price?: number;
  mark_iv?: number;
  volume?: number;
  open_interest?: number;
};

type Ticker = {
  instrument_name: string;
  mark_price?: number;
  mark_iv?: number;
  best_bid_price?: number;
  best_ask_price?: number;
  underlying_price?: number;
  open_interest?: number;
  stats?: { volume?: number };
  greeks?: { delta?: number; gamma?: number; theta?: number; vega?: number };
};

function mapSummary(s: BookSummary): OptionContract | null {
  const parsed = parseExpiry(s.instrument_name);
  if (!parsed) return null;
  const bid = s.bid_price ?? s.best_bid_price ?? null;
  const ask = s.ask_price ?? s.best_ask_price ?? null;
  return {
    instrument: s.instrument_name,
    expiry: parsed.expiry,
    strike: parsed.strike,
    optionType: parsed.optionType,
    markPrice: s.mark_price ?? null,
    bid,
    ask,
    // Deribit mark_iv is already in percent (e.g. 47.5)
    iv: s.mark_iv != null ? s.mark_iv / 100 : null,
    delta: null,
    gamma: null,
    theta: null,
    vega: null,
    underlyingPrice: s.underlying_price ?? null,
    volume: s.volume ?? null,
    openInterest: s.open_interest ?? null,
  };
}

async function mapPool<T, R>(
  items: T[],
  concurrency: number,
  fn: (item: T) => Promise<R>,
): Promise<R[]> {
  const out: R[] = new Array(items.length);
  let i = 0;
  async function worker() {
    while (i < items.length) {
      const idx = i++;
      out[idx] = await fn(items[idx]);
    }
  }
  await Promise.all(
    Array.from({ length: Math.min(concurrency, items.length) }, () => worker()),
  );
  return out;
}

/** Enrich front-expiry near-ATM contracts with ticker greeks (book summary has none). */
async function enrichGreeks(contracts: OptionContract[]): Promise<void> {
  if (!contracts.length) return;
  const und =
    contracts.find((c) => c.underlyingPrice != null)?.underlyingPrice ?? null;
  const expiries = Array.from(new Set(contracts.map((c) => c.expiry))).sort();
  const front = expiries.slice(0, 2);
  let candidates = contracts.filter((c) => front.includes(c.expiry));
  if (und != null && und > 0) {
    const band = candidates.filter(
      (c) => Math.abs(c.strike - und) / und <= 0.25,
    );
    if (band.length >= 8) candidates = band;
  }
  // Prefer open interest, then volume
  candidates = candidates
    .slice()
    .sort(
      (a, b) =>
        (b.openInterest ?? 0) - (a.openInterest ?? 0) ||
        (b.volume ?? 0) - (a.volume ?? 0),
    )
    .slice(0, 48);

  const byName = new Map(contracts.map((c) => [c.instrument, c]));
  await mapPool(candidates, 8, async (c) => {
    try {
      const t = await deribitGet<Ticker>("public/ticker", {
        instrument_name: c.instrument,
      });
      const row = byName.get(c.instrument);
      if (!row) return;
      if (t.greeks) {
        row.delta = t.greeks.delta ?? null;
        row.gamma = t.greeks.gamma ?? null;
        row.theta = t.greeks.theta ?? null;
        row.vega = t.greeks.vega ?? null;
      }
      if (t.best_bid_price != null) row.bid = t.best_bid_price;
      if (t.best_ask_price != null) row.ask = t.best_ask_price;
      if (t.mark_price != null) row.markPrice = t.mark_price;
      if (t.mark_iv != null) row.iv = t.mark_iv / 100;
      if (t.underlying_price != null) row.underlyingPrice = t.underlying_price;
      if (t.open_interest != null) row.openInterest = t.open_interest;
      if (t.stats?.volume != null) row.volume = t.stats.volume;
    } catch {
      // skip ticker failures; keep book summary row
    }
  });
}

export async function fetchLiveChain(
  currency: "BTC" | "ETH" = "BTC",
  opts?: { enrichGreeks?: boolean },
): Promise<OptionContract[]> {
  const summaries = await deribitGet<BookSummary[]>(
    "public/get_book_summary_by_currency",
    { currency, kind: "option" },
  );

  const out: OptionContract[] = [];
  for (const s of summaries) {
    const row = mapSummary(s);
    if (row) out.push(row);
  }

  out.sort(
    (a, b) => a.expiry.localeCompare(b.expiry) || a.strike - b.strike,
  );

  if (opts?.enrichGreeks !== false) {
    await enrichGreeks(out);
  }

  return out;
}
