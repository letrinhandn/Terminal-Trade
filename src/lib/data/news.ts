import Parser from "rss-parser";
import type { NewsArticle } from "@/lib/types";

const FEEDS = [
  {
    name: "CoinDesk",
    url: "https://www.coindesk.com/arc/outboundfeeds/rss/",
    category: "crypto",
  },
  {
    name: "CoinTelegraph",
    url: "https://cointelegraph.com/rss",
    category: "crypto",
  },
  { name: "Decrypt", url: "https://decrypt.co/feed", category: "crypto" },
  {
    name: "MarketWatch",
    url: "https://feeds.marketwatch.com/marketwatch/topstories/",
    category: "markets",
  },
  {
    name: "TechCrunch",
    url: "https://techcrunch.com/feed/",
    category: "tech",
  },
  {
    name: "BBC Business",
    url: "https://feeds.bbci.co.uk/news/business/rss.xml",
    category: "macro",
  },
  {
    name: "Hacker News",
    url: "https://hnrss.org/frontpage",
    category: "tech",
  },
];

const parser = new Parser({ timeout: 8000 });

function scoreArticle(a: NewsArticle, q: string): number {
  const needle = q.toLowerCase();
  const hay = `${a.title} ${a.summary}`.toLowerCase();
  if (!needle) return 0;
  if (hay.includes(needle)) return 3;
  // token match (e.g. "apple" from company searches)
  const tokens = needle.split(/[^a-z0-9]+/).filter((t) => t.length > 2);
  return tokens.reduce((s, t) => (hay.includes(t) ? s + 1 : s), 0);
}

async function fetchGoogleNews(q: string): Promise<NewsArticle[]> {
  const url = `https://news.google.com/rss/search?q=${encodeURIComponent(
    `${q} stock OR shares OR earnings`,
  )}&hl=en-US&gl=US&ceid=US:en`;
  try {
    const parsed = await parser.parseURL(url);
    return (parsed.items || []).slice(0, 20).map((item) => ({
      title: item.title || "Untitled",
      summary: (item.contentSnippet || item.summary || "").slice(0, 280),
      link: item.link || "",
      published: item.isoDate || item.pubDate || new Date().toISOString(),
      source: "Google News",
      category: "markets",
    }));
  } catch {
    return [];
  }
}

export async function fetchNews(
  limit = 40,
  q?: string,
): Promise<NewsArticle[]> {
  const query = (q || "").trim();

  const batches = await Promise.allSettled(
    FEEDS.map(async (feed) => {
      const parsed = await parser.parseURL(feed.url);
      return (parsed.items || []).slice(0, 8).map((item) => ({
        title: item.title || "Untitled",
        summary: (item.contentSnippet || item.summary || "").slice(0, 280),
        link: item.link || "",
        published: item.isoDate || item.pubDate || new Date().toISOString(),
        source: feed.name,
        category: feed.category,
      }));
    }),
  );

  const articles: NewsArticle[] = [];
  for (const b of batches) {
    if (b.status === "fulfilled") articles.push(...b.value);
  }

  if (query) {
    const g = await fetchGoogleNews(query);
    articles.push(...g);
    const ranked = articles
      .map((a) => ({ a, s: scoreArticle(a, query) }))
      .filter((x) => x.s > 0)
      .sort(
        (x, y) =>
          y.s - x.s || +new Date(y.a.published) - +new Date(x.a.published),
      )
      .map((x) => x.a);
    // Dedup by title
    const seen = new Set<string>();
    const out: NewsArticle[] = [];
    for (const a of ranked) {
      const key = a.title.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(a);
      if (out.length >= limit) break;
    }
    if (out.length) return out;
    // Fallback: general feed if no keyword hits
  }

  return articles
    .sort((a, b) => +new Date(b.published) - +new Date(a.published))
    .slice(0, limit);
}
