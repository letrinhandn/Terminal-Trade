import type { IdeaRow, MarketSignal, UniverseKind, UniverseMember } from "@/lib/types";
import { scoreFromSignals } from "@/lib/signals/engine";

export function riskFlagsFromSignals(
  signals: MarketSignal[],
  changePct1m: number | null,
): string[] {
  const flags: string[] = [];
  const bearish = signals.filter((s) => s.side === "bearish");
  const bullish = signals.filter((s) => s.side === "bullish");
  if (bearish.some((s) => s.id.includes("overbought"))) flags.push("Overbought");
  if (bearish.some((s) => s.id.includes("volume") && s.side === "bearish")) {
    flags.push("Volume selloff");
  }
  if (changePct1m != null && changePct1m <= -15) flags.push("Deep 1M drawdown");
  if (changePct1m != null && changePct1m >= 25) flags.push("Extended run");
  if (bullish.length >= 3 && bearish.length === 0) flags.push("Crowded bullish");
  if (bearish.length >= 3 && bullish.length === 0) flags.push("Heavy bearish");
  return flags;
}

export function buildIdeaRow(
  member: UniverseMember,
  opts: {
    price: number;
    changePct: number;
    changePct1m: number | null;
    signals: MarketSignal[];
  },
): IdeaRow {
  return {
    symbol: member.symbol,
    name: member.name,
    kind: member.kind,
    price: opts.price,
    changePct: opts.changePct,
    changePct1m: opts.changePct1m,
    score: scoreFromSignals(opts.signals),
    signals: opts.signals.slice(0, 4),
    riskFlags: riskFlagsFromSignals(opts.signals, opts.changePct1m),
  };
}

export function filterIdeas(
  rows: IdeaRow[],
  kind: "all" | UniverseKind,
): IdeaRow[] {
  const filtered =
    kind === "all" ? rows : rows.filter((r) => r.kind === kind);
  return filtered.sort((a, b) => b.score - a.score);
}
