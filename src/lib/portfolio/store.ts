import type { HoldingLot, PaperPortfolio } from "@/lib/types";

export const PORTFOLIO_KEY = "tt_portfolio_v1";
export const WATCHLIST_KEY = "tt_watchlist_v1";

export function emptyPortfolio(cash = 10000): PaperPortfolio {
  return {
    cash,
    holdings: [],
    updatedAt: new Date().toISOString(),
  };
}

export function loadPortfolio(): PaperPortfolio {
  if (typeof window === "undefined") return emptyPortfolio();
  try {
    const raw = localStorage.getItem(PORTFOLIO_KEY);
    if (!raw) return emptyPortfolio();
    const parsed = JSON.parse(raw) as PaperPortfolio;
    if (!parsed || !Array.isArray(parsed.holdings)) return emptyPortfolio();
    return {
      cash: Number(parsed.cash) || 0,
      holdings: parsed.holdings.map(normalizeLot).filter(Boolean) as HoldingLot[],
      updatedAt: parsed.updatedAt || new Date().toISOString(),
    };
  } catch {
    return emptyPortfolio();
  }
}

function normalizeLot(h: HoldingLot): HoldingLot | null {
  if (!h?.symbol || !(h.qty > 0) || !(h.costBasis >= 0)) return null;
  return {
    id: h.id || crypto.randomUUID(),
    symbol: String(h.symbol).toUpperCase(),
    qty: Number(h.qty),
    costBasis: Number(h.costBasis),
    addedAt: h.addedAt || new Date().toISOString(),
    note: h.note,
  };
}

export function savePortfolio(p: PaperPortfolio): void {
  if (typeof window === "undefined") return;
  const next: PaperPortfolio = {
    ...p,
    updatedAt: new Date().toISOString(),
  };
  localStorage.setItem(PORTFOLIO_KEY, JSON.stringify(next));
}

export function loadWatchlist(): string[] {
  if (typeof window === "undefined") return ["AAPL", "MSFT", "NVDA", "BTC"];
  try {
    const raw = localStorage.getItem(WATCHLIST_KEY);
    if (!raw) return ["AAPL", "MSFT", "NVDA", "BTC"];
    const arr = JSON.parse(raw) as string[];
    if (!Array.isArray(arr)) return ["AAPL", "MSFT", "NVDA", "BTC"];
    return Array.from(
      new Set(arr.map((s) => String(s).toUpperCase()).filter(Boolean)),
    ).slice(0, 40);
  } catch {
    return ["AAPL", "MSFT", "NVDA", "BTC"];
  }
}

export function saveWatchlist(symbols: string[]): void {
  if (typeof window === "undefined") return;
  const cleaned = Array.from(
    new Set(symbols.map((s) => s.trim().toUpperCase()).filter(Boolean)),
  ).slice(0, 40);
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify(cleaned));
}

export function addHolding(
  portfolio: PaperPortfolio,
  input: { symbol: string; qty: number; costBasis: number; note?: string },
): PaperPortfolio {
  const symbol = input.symbol.trim().toUpperCase();
  const qty = Number(input.qty);
  const costBasis = Number(input.costBasis);
  if (!symbol || !(qty > 0) || !(costBasis >= 0)) return portfolio;

  const existing = portfolio.holdings.find((h) => h.symbol === symbol);
  let holdings: HoldingLot[];
  if (existing) {
    const totalQty = existing.qty + qty;
    const avg =
      (existing.costBasis * existing.qty + costBasis * qty) / totalQty;
    holdings = portfolio.holdings.map((h) =>
      h.symbol === symbol
        ? { ...h, qty: totalQty, costBasis: avg, note: input.note ?? h.note }
        : h,
    );
  } else {
    holdings = [
      ...portfolio.holdings,
      {
        id: crypto.randomUUID(),
        symbol,
        qty,
        costBasis,
        addedAt: new Date().toISOString(),
        note: input.note,
      },
    ];
  }
  return { ...portfolio, holdings };
}

export function removeHolding(
  portfolio: PaperPortfolio,
  id: string,
): PaperPortfolio {
  return {
    ...portfolio,
    holdings: portfolio.holdings.filter((h) => h.id !== id),
  };
}
