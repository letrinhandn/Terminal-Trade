import type { TabId } from "@/lib/types";

/** Command registry item model. */
export type CommandGroup =
  | "screen"
  | "action"
  | "help"
  | "instrument"
  | "data";

export type CommandItem = {
  id: string;
  title: string;
  group: CommandGroup;
  aliases: string[];
  keywords: string[];
  subtitle: string;
  shortcut?: string;
  /** Navigate to tab when activated */
  tab?: TabId;
  /** Optional section hint inside a desk */
  section?: string;
  /** Pure action id (help, refresh) */
  action?: "help" | "focus_cmd";
  priority?: number;
};

/** Screen aliases for the command panel. */
export const SCREEN_SEED: CommandItem[] = [
  {
    id: "screen:dashboard",
    title: "Dashboard",
    group: "screen",
    aliases: ["dash", "home", "overview", "main", "dashboard"],
    keywords: ["summary", "widgets", "pulse", "indices"],
    subtitle: "Open Dashboard desk",
    shortcut: "F1",
    tab: "dashboard",
    priority: 10,
  },
  {
    id: "screen:markets",
    title: "Markets",
    group: "screen",
    aliases: ["mkt", "mkts", "markets", "market", "live"],
    keywords: ["quotes", "heatmap", "movers", "crypto"],
    subtitle: "Open Markets desk",
    shortcut: "F2",
    tab: "markets",
  },
  {
    id: "screen:equity",
    title: "Equity Research",
    group: "screen",
    aliases: ["eq", "equity", "rsrch", "research"],
    keywords: ["fundamentals", "company", "candles", "profile"],
    subtitle: "Open Equity research",
    shortcut: "F3",
    tab: "equity",
  },
  {
    id: "screen:signals",
    title: "Signals",
    group: "screen",
    aliases: ["sig", "signal", "signals", "tech"],
    keywords: ["technical", "indicators", "momentum"],
    subtitle: "Open Signals desk",
    shortcut: "F4",
    tab: "signals",
  },
  {
    id: "screen:portfolio",
    title: "Portfolio",
    group: "screen",
    aliases: ["pf", "port", "portfolio", "holdings"],
    keywords: ["positions", "pnl", "book", "nav"],
    subtitle: "Open Portfolio desk",
    shortcut: "F5",
    tab: "portfolio",
  },
  {
    id: "screen:economy",
    title: "Economy",
    group: "screen",
    aliases: ["eco", "econ", "economics", "fred"],
    keywords: ["macro", "gdp", "inflation", "indicators"],
    subtitle: "Open Economy / FRED",
    shortcut: "F6",
    tab: "economy",
  },
  {
    id: "screen:news",
    title: "News",
    group: "screen",
    aliases: ["nws", "news", "headlines", "feed"],
    keywords: ["articles", "wire", "rss"],
    subtitle: "Open News monitor",
    shortcut: "F7",
    tab: "news",
  },
  {
    id: "screen:geopolitics",
    title: "Geopolitics",
    group: "screen",
    aliases: ["geo", "geopolitics", "politics", "risk"],
    keywords: ["conflict", "sanctions", "macro risk"],
    subtitle: "Open Geopolitics desk",
    shortcut: "F8",
    tab: "geopolitics",
  },
  {
    id: "screen:nodes",
    title: "Node Editor",
    group: "screen",
    aliases: ["nodes", "node", "workflow"],
    keywords: ["visual", "correlation", "canvas"],
    subtitle: "Open Nodes workflow",
    tab: "nodes",
  },
  {
    id: "screen:ideas",
    title: "Screener / Ideas",
    group: "screen",
    aliases: ["ideas", "idea", "scrn", "screener", "screen", "rec"],
    keywords: ["filter", "scan", "universe"],
    subtitle: "Open Ideas screener",
    tab: "ideas",
  },
  {
    id: "screen:options",
    title: "Options",
    group: "screen",
    aliases: ["op", "opt", "options", "fno", "chain"],
    keywords: ["deribit", "greeks", "vol"],
    subtitle: "Open Options desk",
    tab: "options",
  },
];

export const ACTION_SEED: CommandItem[] = [
  {
    id: "action:help",
    title: "Help",
    group: "help",
    aliases: ["help", "?"],
    keywords: ["commands", "reference", "docs"],
    subtitle: "Show command reference",
    action: "help",
    priority: 20,
  },
  {
    id: "action:focus_cmd",
    title: "Focus command bar",
    group: "action",
    aliases: ["cmd", "command"],
    keywords: ["search", "palette"],
    subtitle: "Focus the command input (Ctrl+K)",
    shortcut: "Ctrl+K",
    action: "focus_cmd",
  },
];

export function allRegistryItems(): CommandItem[] {
  return [...SCREEN_SEED, ...ACTION_SEED];
}

export function screenByAlias(token: string): CommandItem | undefined {
  const t = token.trim().toLowerCase();
  return SCREEN_SEED.find(
    (s) =>
      s.aliases.some((a) => a.toLowerCase() === t) ||
      s.title.toLowerCase() === t ||
      s.id === `screen:${t}`,
  );
}
