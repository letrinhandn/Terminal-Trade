import type { MarkedHolding } from "@/lib/types";

export type PortfolioRisk = {
  equity: number;
  invested: number;
  cash: number;
  pnl: number;
  pnlPct: number;
  /** Annualized vol proxy from position day% dispersion (rough). */
  volProxy: number;
  sharpeProxy: number;
  /** Parametric 95% 1-day VaR on invested book using volProxy. */
  var95_1d: number;
  herfindahl: number;
  maxWeight: number;
  maxWeightSymbol: string | null;
  positions: number;
};

/** Lightweight desk risk metrics for paper books (not regulatory VaR). */
export function computePortfolioRisk(
  cash: number,
  marked: MarkedHolding[],
): PortfolioRisk {
  const invested = marked.reduce((a, r) => a + r.marketValue, 0);
  const cost = marked.reduce((a, r) => a + r.costValue, 0);
  const equity = cash + invested;
  const pnl = invested - cost;
  const pnlPct = cost ? (pnl / cost) * 100 : 0;

  const weights = marked.map((m) => (equity > 0 ? m.marketValue / equity : 0));
  const herfindahl = weights.reduce((a, w) => a + w * w, 0);
  let maxWeight = 0;
  let maxWeightSymbol: string | null = null;
  for (const m of marked) {
    if (m.weight > maxWeight) {
      maxWeight = m.weight;
      maxWeightSymbol = m.symbol;
    }
  }

  // Day-return dispersion → crude annualized vol
  const dayRets = marked.map((m) => m.changePct / 100);
  const mean =
    dayRets.length > 0
      ? dayRets.reduce((a, b) => a + b, 0) / dayRets.length
      : 0;
  const variance =
    dayRets.length > 1
      ? dayRets.reduce((a, r) => a + (r - mean) ** 2, 0) / (dayRets.length - 1)
      : 0;
  const dailyVol = Math.sqrt(variance);
  const volProxy = dailyVol * Math.sqrt(252) * 100;
  const sharpeProxy =
    dailyVol > 0 ? (mean / dailyVol) * Math.sqrt(252) : 0;
  const var95_1d = invested * dailyVol * 1.65;

  return {
    equity,
    invested,
    cash,
    pnl,
    pnlPct,
    volProxy,
    sharpeProxy,
    var95_1d,
    herfindahl,
    maxWeight,
    maxWeightSymbol,
    positions: marked.length,
  };
}
