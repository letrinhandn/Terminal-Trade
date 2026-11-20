"use client";

import { useEffect, useState } from "react";
import type { NewsArticle } from "@/lib/types";
import { apiGet } from "@/lib/api";

type Env = {
  data: { articles: NewsArticle[]; q: string | null };
  meta?: { provider?: string; latencyMs?: number };
};

export function NewsTab({
  symbol,
  onSymbolChange,
  onStatus,
}: {
  symbol: string;
  onSymbolChange: (s: string) => void;
  onStatus?: (s: string) => void;
}) {
  const [q, setQ] = useState(symbol);
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setQ(symbol), [symbol]);

  async function load(query: string) {
    setLoading(true);
    setError(null);
    try {
      const res = await apiGet<Env>(
        `/api/v1/news?q=${encodeURIComponent(query)}&limit=50`,
      );
      setArticles(res.data.articles || []);
      onStatus?.(
        `News | ${res.meta?.provider || "rss"} | ${res.data.articles?.length ?? 0} | ${res.meta?.latencyMs ?? "?"}ms`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(symbol);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol]);

  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-[#ff9500]">News Monitor</h2>
          <p className="text-xs text-[#666]">
            RSS and Google News monitor
          </p>
        </div>
        <div className="flex gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                const s = q.trim().toUpperCase();
                onSymbolChange(s);
                void load(s);
              }
            }}
            className="rounded border border-[#ff6600] bg-black px-2 py-1 font-mono text-sm text-[#ff8800]"
          />
          <button
            type="button"
            className="rounded bg-[#ff6600] px-3 py-1 text-sm font-bold text-black"
            onClick={() => {
              const s = q.trim().toUpperCase();
              onSymbolChange(s);
              void load(s);
            }}
          >
            Filter
          </button>
        </div>
      </div>

      {loading && <p className="text-sm text-[#666]">Fetching</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}

      <ul className="divide-y divide-[#222] border border-[#333]">
        {articles.map((a, i) => (
          <li key={`${a.link}-${i}`} className="bg-[#050505] p-3 hover:bg-[#0a0a0a]">
            <a
              href={a.link}
              target="_blank"
              rel="noreferrer"
              className="text-sm font-medium text-[#ff8800] hover:underline"
            >
              {a.title}
            </a>
            <div className="mt-1 font-mono text-[10px] text-[#666]">
              {a.source} | {a.category} |{" "}
              {new Date(a.published).toLocaleString()}
            </div>
            {a.summary && (
              <p className="mt-1 text-xs text-[#999] line-clamp-2">{a.summary}</p>
            )}
          </li>
        ))}
        {!loading && !articles.length && (
          <li className="p-6 text-center text-[#666]">No articles</li>
        )}
      </ul>
    </div>
  );
}
