import type { PaperPortfolio } from "@/lib/types";

export type LedgerTx = {
  id: string;
  date: string;
  symbol: string;
  type: "BUY" | "SELL" | "CASH" | "DIV";
  qty: number;
  price: number;
  total: number;
  note?: string;
};

export const LEDGER_KEY = "tt_ledger_v2";
export const NAV_SNAP_KEY = "tt_nav_snaps_v1";
export const DEMO_FLAG = "tt_demo_seeded_v2";

export function loadLedger(): LedgerTx[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(LEDGER_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw) as LedgerTx[];
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

export function saveLedger(txs: LedgerTx[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(LEDGER_KEY, JSON.stringify(txs.slice(0, 500)));
}

export function appendLedger(tx: Omit<LedgerTx, "id">): LedgerTx[] {
  const next = [{ ...tx, id: crypto.randomUUID() }, ...loadLedger()];
  saveLedger(next);
  return next;
}

export type NavSnap = { date: string; equity: number };

export function loadNavSnaps(): NavSnap[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(NAV_SNAP_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as NavSnap[];
  } catch {
    return [];
  }
}

export function pushNavSnap(equity: number): NavSnap[] {
  if (typeof window === "undefined") return [];
  const day = new Date().toISOString().slice(0, 10);
  const prev = loadNavSnaps().filter((s) => s.date !== day);
  const next = [...prev, { date: day, equity }].slice(-365);
  localStorage.setItem(NAV_SNAP_KEY, JSON.stringify(next));
  return next;
}

/**
 * Demo paper book (sample quantities and prices).
 */
const DEMO_TXS: Omit<LedgerTx, "id">[] = [
  { date: "2024-01-15", symbol: "AAPL", type: "BUY", qty: 15, price: 178.5, total: 2677.5, note: "Core tech" },
  { date: "2024-01-15", symbol: "MSFT", type: "BUY", qty: 12, price: 375.2, total: 4502.4, note: "Cloud/AI" },
  { date: "2024-02-01", symbol: "GOOGL", type: "BUY", qty: 8, price: 141.8, total: 1134.4, note: "Search + AI" },
  { date: "2024-02-01", symbol: "NVDA", type: "BUY", qty: 10, price: 480.0, total: 4800.0, note: "GPU/AI" },
  { date: "2024-02-15", symbol: "AMZN", type: "BUY", qty: 6, price: 178.25, total: 1069.5, note: "E-comm + AWS" },
  { date: "2024-03-01", symbol: "TSLA", type: "BUY", qty: 5, price: 245.0, total: 1225.0, note: "EV" },
  { date: "2024-03-01", symbol: "JPM", type: "BUY", qty: 20, price: 195.5, total: 3910.0, note: "Financials" },
  { date: "2024-03-15", symbol: "JNJ", type: "BUY", qty: 15, price: 155.75, total: 2336.25, note: "Healthcare" },
  { date: "2024-04-01", symbol: "XOM", type: "BUY", qty: 25, price: 105.3, total: 2632.5, note: "Energy" },
  { date: "2024-04-01", symbol: "V", type: "BUY", qty: 10, price: 280.0, total: 2800.0, note: "Payments" },
  { date: "2024-04-15", symbol: "UNH", type: "BUY", qty: 4, price: 525.6, total: 2102.4, note: "Health insurance" },
  { date: "2024-05-01", symbol: "PG", type: "BUY", qty: 12, price: 158.9, total: 1906.8, note: "Staples" },
];

export function seedDemoPortfolioIfEmpty(
  load: () => PaperPortfolio,
  save: (p: PaperPortfolio) => void,
): PaperPortfolio {
  const p = load();
  if (typeof window === "undefined") return p;
  if (p.holdings.length) {
    localStorage.setItem(DEMO_FLAG, "1");
    return p;
  }

  const costSpent = DEMO_TXS.reduce((a, t) => a + t.total, 0);
  const seeded: PaperPortfolio = {
    cash: Math.max(0, 35000 - costSpent),
    updatedAt: new Date().toISOString(),
    holdings: DEMO_TXS.map((t) => ({
      id: crypto.randomUUID(),
      symbol: t.symbol,
      qty: t.qty,
      costBasis: t.price,
      addedAt: `${t.date}T00:00:00Z`,
    })),
  };
  save(seeded);
  if (!loadLedger().length) {
    saveLedger(DEMO_TXS.map((t) => ({ ...t, id: crypto.randomUUID() })));
  }
  localStorage.setItem(DEMO_FLAG, "1");
  return seeded;
}
