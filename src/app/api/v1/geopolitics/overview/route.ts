import { NextResponse } from "next/server";
import { fetchQuote, fetchOhlcv } from "@/lib/data/yahoo";
import { cached } from "@/lib/platform/cache";
import { fail, ok } from "@/lib/platform/json";
import { runProvider } from "@/lib/platform/run";

export const maxDuration = 60;

/** Macro risk desk: Yahoo + GDELT/RSS only. Scores = headline/market proxies, not intel. */
const THREAT = [
  { symbol: "VIX", label: "VIX Fear", yahoo: "^VIX" },
  { symbol: "DXY", label: "DXY Dollar", yahoo: "DX-Y.NYB" },
  { symbol: "GLD", label: "Gold ETF", yahoo: "GLD" },
  { symbol: "USO", label: "Oil ETF", yahoo: "USO" },
  { symbol: "BTC", label: "Bitcoin", yahoo: "BTC-USD" },
  { symbol: "TLT", label: "Long Bonds", yahoo: "TLT" },
  { symbol: "NSEI", label: "Nifty 50", yahoo: "^NSEI" },
];

const SECTORS = [
  { symbol: "XLE", label: "Energy", yahoo: "XLE" },
  { symbol: "ITA", label: "Defense", yahoo: "ITA" },
  { symbol: "XLK", label: "Tech", yahoo: "XLK" },
  { symbol: "XLF", label: "Finance", yahoo: "XLF" },
  { symbol: "XLB", label: "Materials", yahoo: "XLB" },
  { symbol: "SPY", label: "Broad", yahoo: "SPY" },
];

const ROUTE_KEYS = [
  { name: "Strait of Hormuz", re: /hormuz/i, threat: "Military / blockade" },
  { name: "Strait of Malacca", re: /malacca/i, threat: "Piracy / chokepoint" },
  { name: "Suez Canal", re: /suez/i, threat: "Disruption" },
  { name: "Taiwan Strait", re: /taiwan/i, threat: "Military" },
  { name: "Red Sea", re: /red sea|houthi/i, threat: "Shipping attacks" },
];

const FOCUS = [
  { id: "INDIA", key: "F1", re: /\b(india|indian|delhi|modi|galwan|lac)\b/i },
  { id: "CHINA", key: "F2", re: /\b(china|chinese|beijing|pla|xi jinping)\b/i },
  { id: "PAKISTAN", key: "F3", re: /\b(pakistan|pakistani|islamabad)\b/i },
  { id: "USA", key: "F4", re: /\b(united states|\bu\.?s\.?\b|washington|pentagon)\b/i },
  { id: "RUSSIA", key: "F5", re: /\b(russia|russian|moscow|kremlin|putin)\b/i },
  { id: "IRAN", key: "F6", re: /\b(iran|iranian|tehran)\b/i },
  { id: "QUAD", key: "F7", re: /\b(quad|aukus)\b/i },
  { id: "BRICS", key: "F8", re: /\b(brics)\b/i },
  { id: "TAIWAN", key: "F9", re: /\b(taiwan|taipei)\b/i },
  { id: "UKRAINE", key: "F10", re: /\b(ukraine|kyiv|zelensky)\b/i },
  { id: "ISRAEL", key: "F11", re: /\b(israel|gaza|hamas|hezbollah)\b/i },
  { id: "CYBER", key: "F12", re: /\b(cyber|ransomware|hack|malware)\b/i },
];

const COUNTRY_ROWS = [
  { name: "Russia", re: /\b(russia|russian|moscow|kremlin)\b/i },
  { name: "China", re: /\b(china|chinese|beijing|pla)\b/i },
  { name: "Iran", re: /\b(iran|iranian|tehran)\b/i },
  { name: "N. Korea", re: /\b(north korea|dprk|pyongyang)\b/i },
  { name: "USA", re: /\b(united states|\bu\.?s\.?\b|washington|pentagon)\b/i },
  { name: "India", re: /\b(india|indian|delhi|modi)\b/i },
  { name: "Pakistan", re: /\b(pakistan|pakistani)\b/i },
  { name: "Ukraine", re: /\b(ukraine|kyiv)\b/i },
  { name: "Israel", re: /\b(israel|gaza|hamas)\b/i },
  { name: "Taiwan", re: /\b(taiwan|taipei)\b/i },
];

type Headline = {
  title: string;
  url: string;
  seendate: string;
  source: string;
  domain: string;
};

async function fetchGdelt(): Promise<Headline[]> {
  const q = encodeURIComponent(
    '(conflict OR sanction OR military OR war OR cyberattack OR "strait of hormuz" OR taiwan OR ukraine)',
  );
  const url = `https://api.gdeltproject.org/api/v2/doc/doc?query=${q}&mode=ArtList&maxrecords=60&format=json&sort=DateDesc`;
  const res = await fetch(url, {
    headers: { Accept: "application/json" },
    next: { revalidate: 300 },
  });
  if (!res.ok) throw new Error(`GDELT ${res.status}`);
  const raw = (await res.json()) as {
    articles?: {
      title?: string;
      url?: string;
      seendate?: string;
      sourcecountry?: string;
      domain?: string;
    }[];
  };
  return (raw.articles || []).map((a) => ({
    title: a.title || "Untitled",
    url: a.url || "#",
    seendate: a.seendate || "",
    source: a.sourcecountry || "-",
    domain: a.domain || "",
  }));
}

function dailyReturns(closes: number[]): number[] {
  const out: number[] = [];
  for (let i = 1; i < closes.length; i++) {
    const p = closes[i - 1];
    out.push(p ? (closes[i] - p) / p : 0);
  }
  return out;
}

function pearson(a: number[], b: number[]): number {
  const n = Math.min(a.length, b.length);
  if (n < 5) return 0;
  const aa = a.slice(-n);
  const bb = b.slice(-n);
  const ma = aa.reduce((s, x) => s + x, 0) / n;
  const mb = bb.reduce((s, x) => s + x, 0) / n;
  let num = 0;
  let da = 0;
  let db = 0;
  for (let i = 0; i < n; i++) {
    const xa = aa[i] - ma;
    const xb = bb[i] - mb;
    num += xa * xb;
    da += xa * xa;
    db += xb * xb;
  }
  const den = Math.sqrt(da * db);
  return den ? num / den : 0;
}

function classifyHeadline(title: string): {
  level: "FLASH" | "URGENT" | "WATCH";
  tag: string;
} {
  if (/war|missile|invasion|attack|strike|nuclear/i.test(title))
    return { level: "FLASH", tag: "MIL" };
  if (/sanction|embargo|tariff|default|crisis/i.test(title))
    return { level: "URGENT", tag: "ECO" };
  if (/cyber|hack|ransomware/i.test(title))
    return { level: "URGENT", tag: "CYB" };
  if (/election|coup|protest|parliament/i.test(title))
    return { level: "WATCH", tag: "POL" };
  return { level: "WATCH", tag: "OSINT" };
}

function bucketScore(titles: string[], re: RegExp): number {
  const hits = titles.filter((t) => re.test(t)).length;
  return Math.min(10, Number((hits * 1.4).toFixed(1)));
}

function normalizeSeries(closes: number[]): number[] {
  if (!closes.length) return [];
  const base = closes[0] || 1;
  return closes.map((c) => Number(((c / base) * 100).toFixed(2)));
}

export async function GET() {
  try {
    const warnings: string[] = [];
    const indicators: {
      symbol: string;
      label: string;
      price: number;
      changePct: number;
    }[] = [];

    for (const t of THREAT) {
      try {
        const q = await cached(`geo:q:${t.symbol}`, 60_000, () =>
          fetchQuote(t.yahoo || t.symbol),
        );
        indicators.push({
          symbol: t.symbol,
          label: t.label,
          price: q.price,
          changePct: q.changePct,
        });
      } catch (e) {
        warnings.push(
          `${t.symbol}: ${e instanceof Error ? e.message : String(e)}`,
        );
      }
    }

    const sectors: {
      symbol: string;
      label: string;
      price: number;
      changePct: number;
      volume: number;
    }[] = [];
    for (const s of SECTORS) {
      try {
        const q = await cached(`geo:sec:${s.symbol}`, 60_000, () =>
          fetchQuote(s.yahoo),
        );
        sectors.push({
          symbol: s.symbol,
          label: s.label,
          price: q.price,
          changePct: q.changePct,
          volume: q.volume,
        });
      } catch {
        warnings.push(`Sector skip ${s.symbol}`);
      }
    }

    let stream: Headline[] = [];
    try {
      stream = await cached("geo:gdelt", 300_000, fetchGdelt);
    } catch (e) {
      warnings.push(`GDELT: ${e instanceof Error ? e.message : String(e)}`);
      try {
        const { fetchNews } = await import("@/lib/data/news");
        const news = await cached("geo:rss-fallback", 300_000, () =>
          fetchNews(50, "geopolitics OR sanctions OR conflict OR war"),
        );
        stream = (news || []).slice(0, 40).map((a) => ({
          title: a.title,
          url: a.link,
          seendate: a.published || "",
          source: a.source || "RSS",
          domain: a.category || "",
        }));
        if (stream.length) warnings.push("Headlines via RSS fallback");
      } catch (e2) {
        warnings.push(
          `RSS fallback: ${e2 instanceof Error ? e2.message : String(e2)}`,
        );
      }
    }

    const titles = stream.map((a) => a.title);
    const intel = stream.map((a) => {
      const c = classifyHeadline(a.title);
      const focusHit =
        FOCUS.find((f) => f.re.test(a.title))?.id ||
        (a.source !== "-" && a.source !== "RSS" ? a.source.slice(0, 8) : "GEN");
      return {
        ...a,
        level: c.level,
        tag: c.tag,
        focus: focusHit,
      };
    });

    const countryMatrix = COUNTRY_ROWS.map((c) => {
      const related = titles.filter((t) => c.re.test(t));
      const mil = bucketScore(related, /military|army|missile|troop|war|strike|nuclear|weapon/i);
      const eco = bucketScore(related, /sanction|trade|tariff|economy|oil|bank|currency/i);
      const pol = bucketScore(related, /election|parliament|diplomacy|summit|coup|protest/i);
      const trd = bucketScore(related, /trade|export|import|shipping|port|tariff/i);
      const san = bucketScore(related, /sanction|embargo|blacklist/i);
      const tot = Number(
        (((mil + eco + pol + trd + san) / 5) || 0).toFixed(1),
      );
      return {
        name: c.name,
        mil,
        eco,
        pol,
        tot,
        trd,
        san,
        mentions: related.length,
      };
    }).filter((r) => r.mentions > 0 || ["USA", "China", "Russia", "India"].includes(r.name));

    const focusCounts = FOCUS.map((f) => ({
      id: f.id,
      key: f.key,
      mentions: titles.filter((t) => f.re.test(t)).length,
    }));

    const routes = ROUTE_KEYS.map((r) => {
      const hits = stream.filter((a) => r.re.test(a.title));
      return {
        name: r.name,
        threat: r.threat,
        mentions: hits.length,
        risk: Math.min(10, hits.length * 2),
        sample: hits[0]?.title || null,
      };
    });

    const by = Object.fromEntries(indicators.map((i) => [i.symbol, i.changePct]));
    const clamp = (n: number) => Math.max(5, Math.min(95, n));
    const radar = {
      Terror: clamp(20 + bucketScore(titles, /terror|attack|bomb/i) * 8),
      Military: clamp(30 + Math.abs(by.VIX || 0) * 2 + bucketScore(titles, /military|war|missile/i) * 6),
      Economic: clamp(30 + Math.abs(by.DXY || 0) * 4 + bucketScore(titles, /sanction|tariff|default/i) * 6),
      Cyber: clamp(15 + bucketScore(titles, /cyber|hack|ransomware/i) * 10),
      Nuclear: clamp(10 + bucketScore(titles, /nuclear|icbm|warhead/i) * 12),
      Climate: clamp(15 + bucketScore(titles, /climate|flood|drought|hurricane/i) * 8),
    };
    const globalRisk = Number(
      (
        Object.values(radar).reduce((a, b) => a + b, 0) /
        Object.values(radar).length /
        10
      ).toFixed(2),
    );

    const start = new Date();
    start.setUTCDate(start.getUTCDate() - 35);
    const startStr = start.toISOString().slice(0, 10);
    const seriesDefs = [
      { id: "VIX", label: "Vol", color: "#22c55e", yahoo: "^VIX" },
      { id: "USO", label: "Energy", color: "#ef4444", yahoo: "USO" },
      { id: "GLD", label: "Safehaven", color: "#eab308", yahoo: "GLD" },
      { id: "BTC", label: "Crypto", color: "#38bdf8", yahoo: "BTC-USD" },
      { id: "TLT", label: "Bonds", color: "#a855f7", yahoo: "TLT" },
    ];
    const series: {
      id: string;
      label: string;
      color: string;
      dates: string[];
      values: number[];
    }[] = [];
    const rets: Record<string, number[]> = {};
    for (const s of seriesDefs) {
      try {
        const bars = await cached(`geo:ohlcv:${s.id}:${startStr}`, 600_000, () =>
          fetchOhlcv(s.yahoo, startStr),
        );
        const closes = bars.map((b) => b.close);
        series.push({
          id: s.id,
          label: s.label,
          color: s.color,
          dates: bars.map((b) => b.date.slice(0, 10)),
          values: normalizeSeries(closes),
        });
        rets[s.id] = dailyReturns(closes);
      } catch {
        warnings.push(`Series skip ${s.id}`);
      }
    }

    const corrLabels = seriesDefs.map((s) => s.id).filter((id) => (rets[id]?.length || 0) > 10);
    const corrMatrix = corrLabels.map((a) =>
      corrLabels.map((b) =>
        a === b ? 1 : Number(pearson(rets[a], rets[b]).toFixed(3)),
      ),
    );

    // Sector vs VIX corr proxy for market impact
    let vixRets: number[] = rets.VIX || [];
    if (!vixRets.length) {
      try {
        const bars = await cached(`geo:ohlcv:VIX:${startStr}`, 600_000, () =>
          fetchOhlcv("^VIX", startStr),
        );
        vixRets = dailyReturns(bars.map((b) => b.close));
      } catch {
        /* ignore */
      }
    }
    const marketImpact: {
      symbol: string;
      label: string;
      price: number;
      changePct: number;
      volume: number;
      corr: number;
      impl: string;
    }[] = [];
    for (const s of sectors) {
      let corr = 0;
      try {
        const bars = await cached(`geo:ohlcv:${s.symbol}:${startStr}`, 600_000, () =>
          fetchOhlcv(s.symbol, startStr),
        );
        corr = Number(
          pearson(dailyReturns(bars.map((b) => b.close)), vixRets).toFixed(2),
        );
      } catch {
        corr = 0;
      }
      marketImpact.push({
        ...s,
        corr,
        impl:
          Math.abs(s.changePct) >= 1.5
            ? "Elevated move"
            : Math.abs(s.changePct) >= 0.5
              ? "Mild move"
              : "Quiet",
      });
    }

    const sanctions = titles.filter((t) => /sanction|embargo/i.test(t)).length;
    const conflicts = titles.filter((t) =>
      /war|conflict|invasion|missile|strike/i.test(t),
    ).length;

    const focusId = "INDIA";
    const focusHeadlines = intel.filter((a) => FOCUS.find((f) => f.id === focusId)?.re.test(a.title));
    const focusPanel = {
      id: focusId,
      headlines: focusHeadlines.slice(0, 8),
      mentions: focusHeadlines.length,
      note: "Headline keyword hits for this focus. Not a risk rating.",
    };

    return ok(
      await runProvider(
        "yahoo",
        async () => ({
          indicators,
          intel,
          stream: intel,
          radar,
          globalRisk,
          stats: {
            conflicts,
            sanctions,
            alerts: intel.length,
          },
          countryMatrix,
          focusCounts,
          routes,
          series,
          corr: { labels: corrLabels, matrix: corrMatrix },
          marketImpact,
          focusPanel,
          attribution:
            "Yahoo quotes and OHLCV, GDELT or RSS headlines, keyword proxies for countries and routes",
        }),
        warnings,
      ),
    );
  } catch (e) {
    return fail(e);
  }
}

export async function HEAD() {
  return NextResponse.json({ ok: true });
}
