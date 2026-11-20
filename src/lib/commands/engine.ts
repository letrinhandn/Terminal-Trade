import type { CommandAction, TabId } from "@/lib/types";
import {
  allRegistryItems,
  screenByAlias,
  type CommandItem,
} from "@/lib/commands/registry";
import { scoreMatch } from "@/lib/commands/rank";
import { parsePhrases, isTickerLike, type Phrase } from "@/lib/commands/phrase";
import { bumpUsage, usageBoost } from "@/lib/commands/usage";

export type SuggestionRow = {
  key: string;
  item?: CommandItem;
  phrase?: Phrase;
  title: string;
  subtitle: string;
  group: string;
  shortcut?: string;
  score: number;
  /** Text to put in the bar when selected via Tab / click-fill */
  fill: string;
};

const GROUP_ORDER: Record<string, number> = {
  instrument: 0,
  screen: 1,
  action: 2,
  help: 3,
  data: 4,
};

export function searchCommands(query: string, limit = 12): SuggestionRow[] {
  const q = query.trim();
  if (!q) {
    // Empty box: top screens + help
    return allRegistryItems()
      .filter((i) => i.group === "screen" || i.id === "action:help")
      .slice(0, 8)
      .map((item) => ({
        key: item.id,
        item,
        title: item.title,
        subtitle: item.subtitle,
        group: item.group,
        shortcut: item.shortcut,
        score: 50 + (item.priority || 0) + usageBoost(item.id) / 100,
        fill: item.aliases[0] || item.title,
      }))
      .sort((a, b) => b.score - a.score);
  }

  const rows: SuggestionRow[] = [];

  // Phrase intents (AAPL chart, open portfolio)
  for (const phrase of parsePhrases(q)) {
    if (phrase.kind === "help") {
      rows.push({
        key: "phrase:help",
        phrase,
        title: "Help",
        subtitle: "Show command reference",
        group: "help",
        score: 110,
        fill: "HELP",
      });
    } else if (phrase.kind === "open" && phrase.tab) {
      rows.push({
        key: `phrase:open:${phrase.tab}`,
        phrase,
        title: `Open ${phrase.tab}`,
        subtitle: "Navigate to desk",
        group: "screen",
        score: 105,
        fill: phrase.tab.toUpperCase(),
      });
    } else if (
      (phrase.kind === "symbol_view" || phrase.kind === "ticker") &&
      phrase.symbols[0]
    ) {
      const sym = phrase.symbols[0];
      const view = phrase.view || "research";
      rows.push({
        key: `phrase:${sym}:${view}`,
        phrase,
        title: `${sym} | ${view}`,
        subtitle: `Load ${sym} to ${phrase.tab || "equity"}`,
        group: "instrument",
        score: phrase.kind === "symbol_view" ? 108 : 102,
        fill: phrase.view ? `${sym} ${phrase.view}` : sym,
      });
    } else if (phrase.kind === "scope" && phrase.scope === "help") {
      rows.push({
        key: "phrase:scope-help",
        phrase: { kind: "help", symbols: [] },
        title: "Help",
        subtitle: phrase.text || "Command help",
        group: "help",
        score: 100,
        fill: "HELP",
      });
    }
  }

  // Registry fuzzy/prefix
  for (const item of allRegistryItems()) {
    const base = scoreMatch(q, {
      title: item.title,
      aliases: item.aliases,
      keywords: item.keywords,
      description: item.subtitle,
      id: item.id,
    });
    if (base <= 0) continue;
    const score =
      base * 100 +
      usageBoost(item.id) +
      (item.priority || 0) * 10;
    rows.push({
      key: item.id,
      item,
      title: item.title,
      subtitle: item.subtitle,
      group: item.group,
      shortcut: item.shortcut,
      score,
      fill: item.aliases[0]?.toUpperCase() || item.title,
    });
  }

  // Bare ticker only when the whole query is one ticker token
  const tokens = q.split(/\s+/).filter(Boolean);
  if (
    tokens.length === 1 &&
    isTickerLike(tokens[0]) &&
    !screenByAlias(tokens[0])
  ) {
    const sym = tokens[0].toUpperCase();
    if (!rows.some((r) => r.key.startsWith(`phrase:${sym}`))) {
      rows.push({
        key: `ticker:${sym}`,
        phrase: { kind: "ticker", symbols: [sym], tab: "equity" },
        title: sym,
        subtitle: "Load symbol to Equity",
        group: "instrument",
        score: 10_200,
        fill: sym,
      });
    }
  }

  // Dedupe by key, keep highest score
  const map = new Map<string, SuggestionRow>();
  for (const r of rows) {
    const prev = map.get(r.key);
    if (!prev || r.score > prev.score) map.set(r.key, r);
  }

  return Array.from(map.values())
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return (GROUP_ORDER[a.group] ?? 9) - (GROUP_ORDER[b.group] ?? 9);
    })
    .slice(0, limit);
}

export function resolveSuggestion(row: SuggestionRow): CommandAction {
  if (row.item?.action === "help" || row.phrase?.kind === "help") {
    bumpUsage(row.item?.id || "action:help");
    return { type: "help" };
  }
  if (row.item?.action === "focus_cmd") {
    return { type: "noop" };
  }
  if (row.phrase) {
    const p = row.phrase;
    if (p.kind === "open" && p.tab) {
      bumpUsage(`screen:${p.tab}`);
      return { type: "tab", tab: p.tab };
    }
    if ((p.kind === "symbol_view" || p.kind === "ticker") && p.symbols[0]) {
      bumpUsage(`sym:${p.symbols[0]}`);
      return {
        type: "tab",
        tab: p.tab || "equity",
        symbol: p.symbols[0],
        view: p.view,
      };
    }
  }
  if (row.item?.tab) {
    bumpUsage(row.item.id);
    return { type: "tab", tab: row.item.tab, section: row.item.section };
  }
  return { type: "noop" };
}

/** Resolve raw input: phrase, registry, then ticker. */
export function resolveCommand(raw: string): CommandAction {
  const text = raw.trim();
  if (!text) return { type: "noop" };
  if (text === "?" || /^help$/i.test(text)) return { type: "help" };

  const hits = searchCommands(text, 5);
  if (hits[0] && hits[0].score >= 75) {
    // Prefer phrase/instrument when scores are close
    const best = hits[0];
    return resolveSuggestion(best);
  }

  const parts = text.toUpperCase().split(/\s+/);
  const screen = screenByAlias(parts[0]) || screenByAlias(parts[parts.length - 1]);
  if (screen?.tab && parts.length === 1) {
    bumpUsage(screen.id);
    return { type: "tab", tab: screen.tab };
  }
  if (parts.length >= 2) {
    const asScreen = screenByAlias(parts[parts.length - 1]);
    if (asScreen?.tab && isTickerLike(parts[0]) && !screenByAlias(parts[0])) {
      bumpUsage(asScreen.id);
      return { type: "tab", tab: asScreen.tab, symbol: parts[0] };
    }
    const firstScreen = screenByAlias(parts[0]);
    if (firstScreen?.tab) {
      bumpUsage(firstScreen.id);
      return {
        type: "tab",
        tab: firstScreen.tab,
        symbol:
          parts[1] && isTickerLike(parts[1]) && !screenByAlias(parts[1])
            ? parts[1]
            : undefined,
      };
    }
  }
  if (isTickerLike(parts[0])) {
    return { type: "symbol", symbol: parts[0], tab: "equity" as TabId };
  }
  return { type: "noop", message: `Unknown: ${text}` };
}
