import type { TabId } from "@/lib/types";
import { screenByAlias } from "@/lib/commands/registry";

/** Command phrase grammar. */

export type PhraseKind =
  | "none"
  | "help"
  | "scope"
  | "symbol_view"
  | "open"
  | "ticker";

export type SymbolView =
  | "chart"
  | "news"
  | "research"
  | "signals"
  | "options"
  | "portfolio";

export type Phrase = {
  kind: PhraseKind;
  symbols: string[];
  view?: SymbolView;
  tab?: TabId;
  scope?: "action" | "instrument" | "help";
  text?: string;
};

const VIEW_WORDS: Record<string, SymbolView> = {
  chart: "chart",
  charts: "chart",
  graph: "chart",
  price: "chart",
  candle: "chart",
  news: "news",
  headlines: "news",
  research: "research",
  fundamentals: "research",
  financials: "research",
  profile: "research",
  analysis: "research",
  overview: "research",
  equity: "research",
  signals: "signals",
  signal: "signals",
  technical: "signals",
  tech: "signals",
  options: "options",
  option: "options",
  chain: "options",
  portfolio: "portfolio",
  holdings: "portfolio",
  positions: "portfolio",
};

const OPEN_VERBS = new Set(["open", "go", "show", "goto"]);

export function isTickerLike(token: string): boolean {
  if (!/^\^?[A-Za-z0-9][A-Za-z0-9.=\-&]{0,14}$/.test(token)) return false;
  return /[A-Za-z]/.test(token);
}

export function viewToTab(view: SymbolView): TabId {
  switch (view) {
    case "chart":
      return "equity";
    case "news":
      return "news";
    case "research":
      return "equity";
    case "signals":
      return "signals";
    case "options":
      return "options";
    case "portfolio":
      return "portfolio";
  }
}

/** Strongest readings first. */
export function parsePhrases(input: string): Phrase[] {
  const text = input.trim();
  if (!text) return [];
  const out: Phrase[] = [];

  const first = text[0];
  if (first === "?" && text.length === 1) {
    out.push({ kind: "help", symbols: [] });
    return out;
  }
  if (first === ">" || first === "$" || first === "@" || first === "?") {
    out.push({
      kind: "scope",
      symbols: [],
      scope:
        first === ">" ? "action" : first === "?" ? "help" : "instrument",
      text: text.slice(1).trim(),
    });
  }

  const tokens = text.split(/\s+/).filter(Boolean);
  const lower = tokens.map((t) => t.toLowerCase());

  // open|go|show <screen|ticker >
  if (tokens.length >= 2 && OPEN_VERBS.has(lower[0])) {
    const rest = tokens.slice(1).join(" ");
    const screen = screenByAlias(rest) || screenByAlias(tokens[1]);
    if (screen?.tab) {
      out.push({ kind: "open", symbols: [], tab: screen.tab, text: rest });
    }
    if (isTickerLike(tokens[1]) && !screenByAlias(tokens[1])) {
      const viewWord = lower[2];
      const view = viewWord ? VIEW_WORDS[viewWord] : undefined;
      out.push({
        kind: view ? "symbol_view" : "ticker",
        symbols: [tokens[1].toUpperCase()],
        view,
        tab: view ? viewToTab(view) : "equity",
      });
    }
  }

  // AAPL chart | chart AAPL
  if (tokens.length === 2) {
    const [a, b] = lower;
    if (VIEW_WORDS[a] && isTickerLike(tokens[1]) && !screenByAlias(tokens[1])) {
      const view = VIEW_WORDS[a];
      out.push({
        kind: "symbol_view",
        symbols: [tokens[1].toUpperCase()],
        view,
        tab: viewToTab(view),
      });
    }
    if (VIEW_WORDS[b] && isTickerLike(tokens[0]) && !screenByAlias(tokens[0])) {
      const view = VIEW_WORDS[b];
      out.push({
        kind: "symbol_view",
        symbols: [tokens[0].toUpperCase()],
        view,
        tab: viewToTab(view),
      });
    }
  }

  // bare ticker
  if (tokens.length === 1 && isTickerLike(tokens[0]) && !screenByAlias(tokens[0])) {
    out.push({
      kind: "ticker",
      symbols: [tokens[0].toUpperCase()],
      tab: "equity",
    });
  }

  return out;
}
