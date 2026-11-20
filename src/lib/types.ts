export type TabId =
  | "dashboard"
  | "markets"
  | "equity"
  | "signals"
  | "portfolio"
  | "economy"
  | "news"
  | "ideas"
  | "options"
  | "nodes"
  | "geopolitics";

export type OverviewSub = "market" | "info" | "fin";
export type IdeasFilter = "all" | "stocks" | "etfs" | "crypto";

/** Legacy lab UI types (kept for unused lab components). */
export type BacktestSub = "run" | "manager" | "editor";
export type OptionsSub = "chain" | "vol" | "strategy" | "greeks";

export interface QuoteSnapshot {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePct: number;
  open?: number;
  previousClose?: number;
  high: number;
  low: number;
  volume: number;
  marketCap?: number;
  peRatio?: number;
  forwardPE?: number;
  sector?: string;
  industry?: string;
}

export interface OhlcvBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TradeResult {
  entryDate: string;
  exitDate: string;
  entryPrice: number;
  exitPrice: number;
  returnPct: number;
  profitLoss: number;
}

export interface BacktestResult {
  strategy: string;
  symbol: string;
  totalReturn: number;
  finalCapital: number;
  numTrades: number;
  winRate: number;
  maxDrawdown: number;
  sharpeRatio: number;
  sortinoRatio: number;
  trades: TradeResult[];
  equityCurve: { date: string; equity: number }[];
  metrics: Record<string, number | string>;
}

export interface NewsArticle {
  title: string;
  summary: string;
  link: string;
  published: string;
  source: string;
  category: string;
}

export interface OptionContract {
  instrument: string;
  expiry: string;
  strike: number;
  optionType: "C" | "P";
  markPrice: number | null;
  bid: number | null;
  ask: number | null;
  iv: number | null;
  delta: number | null;
  gamma: number | null;
  theta: number | null;
  vega: number | null;
  underlyingPrice: number | null;
  volume: number | null;
  openInterest: number | null;
}

export type SignalSide = "bullish" | "bearish" | "neutral";

export interface MarketSignal {
  id: string;
  label: string;
  side: SignalSide;
  strength: number;
  asOf: string;
  detail: string;
  replayStrategy?: "MACD" | "RSI";
}

export interface SignalsResponse {
  symbol: string;
  asOf: string;
  price: number;
  changePct1m: number | null;
  signals: MarketSignal[];
  score: number;
}

export interface HoldingLot {
  id: string;
  symbol: string;
  qty: number;
  costBasis: number;
  addedAt: string;
  note?: string;
}

export interface PaperPortfolio {
  cash: number;
  holdings: HoldingLot[];
  updatedAt: string;
}

export interface MarkedHolding extends HoldingLot {
  name: string;
  price: number;
  changePct: number;
  marketValue: number;
  costValue: number;
  pnl: number;
  pnlPct: number;
  weight: number;
}

export type UniverseKind = "stock" | "etf" | "crypto";

export interface UniverseMember {
  symbol: string;
  name: string;
  kind: UniverseKind;
}

export interface IdeaRow {
  symbol: string;
  name: string;
  kind: UniverseKind;
  price: number;
  changePct: number;
  changePct1m: number | null;
  score: number;
  signals: MarketSignal[];
  riskFlags: string[];
}

export type CommandView =
  | "chart"
  | "news"
  | "research"
  | "signals"
  | "options"
  | "portfolio";

export interface CommandAction {
  type: "help" | "tab" | "symbol" | "noop";
  tab?: TabId;
  overviewSub?: OverviewSub;
  section?: string;
  view?: CommandView;
  symbol?: string;
  message?: string;
}
