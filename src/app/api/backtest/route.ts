import { NextRequest, NextResponse } from "next/server";
import {
  fetchCryptoOhlcv,
  isCryptoSymbol,
} from "@/lib/data/crypto";
import { fetchOhlcv } from "@/lib/data/yahoo";
import { runStrategy, STRATEGY_IDS, type StrategyId } from "@/lib/strategies/builtins";
import { runBacktest } from "@/lib/backtest/engine";

export const maxDuration = 60;

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const symbol = String(body.symbol || "AAPL").toUpperCase();
    const start = String(body.start || "2023-01-01");
    const end = body.end ? String(body.end) : undefined;
    const strategy = String(body.strategy || "MACD") as StrategyId;
    const initialCapital = Number(body.initialCapital ?? 10000);
    const commission = Number(body.commission ?? 0.001);

    if (!STRATEGY_IDS.includes(strategy)) {
      return NextResponse.json({ error: `Unknown strategy ${strategy}` }, { status: 400 });
    }

    const bars = isCryptoSymbol(symbol)
      ? (await fetchCryptoOhlcv(symbol, start, end)).bars
      : await fetchOhlcv(symbol, start, end);
    if (!bars.length) {
      return NextResponse.json({ error: "No OHLCV data" }, { status: 404 });
    }
    const signaled = runStrategy(strategy, bars);
    const result = runBacktest(signaled, {
      strategy,
      symbol,
      initialCapital,
      commission,
    });
    return NextResponse.json(result);
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : String(e) }, { status: 500 });
  }
}
