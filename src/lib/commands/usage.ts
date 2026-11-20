const KEY = "tt_cmd_usage_v1";

type UsageMap = Record<string, { count: number; last: number }>;

function load(): UsageMap {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(localStorage.getItem(KEY) || "{}") as UsageMap;
  } catch {
    return {};
  }
}

function save(m: UsageMap) {
  if (typeof window === "undefined") return;
  localStorage.setItem(KEY, JSON.stringify(m));
}

export function bumpUsage(id: string) {
  const m = load();
  const prev = m[id] || { count: 0, last: 0 };
  m[id] = { count: prev.count + 1, last: Date.now() };
  save(m);
}

/** Usage boost: frequency plus 7-day half-life recency. */
export function usageBoost(id: string, now = Date.now()): number {
  const u = load()[id];
  if (!u) return 0;
  const freq = Math.min(300, Math.floor(80 * Math.log2(1 + u.count)));
  const ageDays = (now - u.last) / 86_400_000;
  const recency = Math.floor(300 * Math.pow(0.5, ageDays / 7));
  return Math.min(600, freq + recency);
}
