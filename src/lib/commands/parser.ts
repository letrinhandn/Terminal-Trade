import type { TabId } from "@/lib/types";
import { resolveCommand } from "@/lib/commands/engine";

export { resolveCommand, searchCommands, resolveSuggestion } from "@/lib/commands/engine";
export type { SuggestionRow } from "@/lib/commands/engine";

/** @deprecated prefer resolveCommand - kept for call sites */
export function parseCommand(raw: string) {
  return resolveCommand(raw);
}

export const FKEY_TABS: { key: string; id: TabId; label: string }[] = [
  { key: "F1", id: "dashboard", label: "DASHBOARD" },
  { key: "F2", id: "markets", label: "MARKETS" },
  { key: "F3", id: "equity", label: "EQUITY" },
  { key: "F4", id: "signals", label: "SIGNALS" },
  { key: "F5", id: "portfolio", label: "PORTFOLIO" },
  { key: "F6", id: "economy", label: "ECONOMY" },
  { key: "F7", id: "news", label: "NEWS" },
  { key: "F8", id: "geopolitics", label: "GEO" },
  { key: "", id: "nodes", label: "NODES" },
  { key: "", id: "ideas", label: "IDEAS" },
  { key: "", id: "options", label: "OPTIONS" },
];

export const HELP_TEXT = `TERMINAL TRADE COMMAND PANEL

Focus: Ctrl+K or /
Enter run, Up/Down select, Tab fill, Esc close

F1 Dashboard  F2 Markets  F3 Equity  F4 Signals
F5 Portfolio  F6 Economy  F7 News  F8 Geo
Also: Nodes, Ideas, Options

Screens
  DASH HOME, MKT MKTS, EQ RSRCH, SIG
  PF PORT, ECO FRED, NWS, GEO, NODES
  IDEAS SCRN, OP

Phrases
  AAPL              load symbol in Equity
  AAPL CHART NEWS   symbol and desk
  AAPL EQ, NVDA SIG symbol and screen
  OPEN PORTFOLIO    switch desk
  HELP or ?         this reference

Data
  Yahoo, CoinGecko, Coinbase, FRED, GDELT, Deribit, alternative.me

Research helpers only. Not investment advice.`;

/** Legacy flat suggestions (CommandPanel uses searchCommands). */
export const COMMAND_SUGGESTIONS = [
  "HELP - Command reference",
  "DASH - Dashboard",
  "MKT - Markets",
  "EQ - Equity",
  "SIG - Signals",
  "PF - Portfolio",
  "ECO - Economy",
  "NWS - News",
  "GEO - Geopolitics",
  "NODES - Workflow",
  "IDEAS - Screener",
  "OP - Options",
  "AAPL CHART - Equity chart",
  "AAPL NEWS - News for AAPL",
];
