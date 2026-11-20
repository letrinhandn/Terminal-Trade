import type { BacktestResult, TradeResult } from "@/lib/types";
import type { Bar } from "@/lib/strategies/builtins";

export function runBacktest(
  bars: Bar[],
  opts: {
    strategy: string;
    symbol: string;
    initialCapital?: number;
    commission?: number;
    slippage?: number;
  },
): BacktestResult {
  const initialCapital = opts.initialCapital ?? 10_000;
  const commission = opts.commission ?? 0.001;
  const slippage = opts.slippage ?? 0.0005;

  let capital = initialCapital;
  let inPosition = false;
  let entryPrice = 0;
  let entryDate = "";
  let shares = 0;
  const trades: TradeResult[] = [];
  const equityCurve: { date: string; equity: number }[] = [];
  let peak = initialCapital;
  let maxDrawdown = 0;
  const returns: number[] = [];

  for (let i = 0; i < bars.length; i++) {
    const bar = bars[i];
    const signal = bar.signal ?? 0;
    const price = bar.close;
    const exec =
      signal !== 0 ? price * (1 + slippage * Math.sign(signal)) : price;

    if (signal === 1 && !inPosition) {
      inPosition = true;
      entryPrice = exec;
      entryDate = bar.date;
      capital *= 1 - commission;
      shares = capital / entryPrice;
    } else if (signal === -1 && inPosition) {
      const exitPrice = exec;
      const proceeds = shares * exitPrice * (1 - commission);
      const pnl = proceeds - capital;
      const retPct = ((exitPrice - entryPrice) / entryPrice) * 100;
      trades.push({
        entryDate,
        exitDate: bar.date,
        entryPrice,
        exitPrice,
        returnPct: retPct,
        profitLoss: pnl,
      });
      returns.push(retPct / 100);
      capital = proceeds;
      inPosition = false;
      shares = 0;
    }

    const equity = inPosition ? shares * price : capital;
    equityCurve.push({ date: bar.date, equity });
    peak = Math.max(peak, equity);
    maxDrawdown = Math.min(maxDrawdown, (equity - peak) / peak);
  }

  // mark-to-market if still open
  if (inPosition && bars.length) {
    const last = bars[bars.length - 1];
    const exitPrice = last.close;
    const proceeds = shares * exitPrice * (1 - commission);
    trades.push({
      entryDate,
      exitDate: last.date,
      entryPrice,
      exitPrice,
      returnPct: ((exitPrice - entryPrice) / entryPrice) * 100,
      profitLoss: proceeds - (shares * entryPrice),
    });
    capital = proceeds;
  }

  const finalCapital = equityCurve.at(-1)?.equity ?? capital;
  const totalReturn = ((finalCapital - initialCapital) / initialCapital) * 100;
  const wins = trades.filter((t) => t.returnPct > 0);
  const winRate = trades.length ? (wins.length / trades.length) * 100 : 0;

  const avg =
    returns.length ? returns.reduce((a, b) => a + b, 0) / returns.length : 0;
  const std =
    returns.length > 1
      ? Math.sqrt(
          returns.reduce((a, r) => a + (r - avg) ** 2, 0) / (returns.length - 1),
        )
      : 0;
  const downside = returns.filter((r) => r < 0);
  const downStd =
    downside.length > 1
      ? Math.sqrt(downside.reduce((a, r) => a + r ** 2, 0) / (downside.length - 1))
      : 0;
  const sharpe = std > 0 ? (avg / std) * Math.sqrt(252) : 0;
  const sortino = downStd > 0 ? (avg / downStd) * Math.sqrt(252) : 0;

  return {
    strategy: opts.strategy,
    symbol: opts.symbol,
    totalReturn,
    finalCapital,
    numTrades: trades.length,
    winRate,
    maxDrawdown: maxDrawdown * 100,
    sharpeRatio: sharpe,
    sortinoRatio: sortino,
    trades,
    equityCurve,
    metrics: {
      total_return: +totalReturn.toFixed(2),
      final_capital: +finalCapital.toFixed(2),
      num_trades: trades.length,
      win_rate: +winRate.toFixed(2),
      max_drawdown: +(maxDrawdown * 100).toFixed(2),
      sharpe_ratio: +sharpe.toFixed(3),
      sortino_ratio: +sortino.toFixed(3),
    },
  };
}
