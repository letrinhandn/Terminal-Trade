import { NextRequest, NextResponse } from "next/server";
import { unstable_cache } from "next/cache";
import {
  fetchCryptoOhlcv,
  isCryptoSymbol,
} from "@/lib/data/crypto";
import { fetchOhlcv } from "@/lib/data/yahoo";
import { IDEAS_UNIVERSE } from "@/lib/ideas/universe";
import { buildIdeaRow, filterIdeas } from "@/lib/ideas/rank";
import { changePctLookback, detectSignals } from "@/lib/signals/engine";
import type { IdeaRow, UniverseKind } from "@/lib/types";

export const maxDuration = 60;

function startDaysAgo(days: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - days);
  return d.toISOString().slice(0, 10);
}

async function loadBars(symbol: string, start: string) {
  if (isCryptoSymbol(symbol)) {
    return (await fetchCryptoOhlcv(symbol, start)).bars;
  }
  return fetchOhlcv(symbol, start);
}

async function screenUniverse(): Promise<IdeaRow[]> {
  const rows: IdeaRow[] = [];
  const start = startDaysAgo(400);
  // Cap concurrent pressure: process in small chunks
  const chunkSize = 5;
  for (let i = 0; i < IDEAS_UNIVERSE.length; i += chunkSize) {
    const chunk = IDEAS_UNIVERSE.slice(i, i + chunkSize);
    const settled = await Promise.allSettled(
      chunk.map(async (member) => {
        const bars = await loadBars(member.symbol, start);
        const signals = detectSignals(bars);
        const last = bars[bars.length - 1];
        const prev = bars[bars.length - 2] ?? last;
        const changePct = prev.close
          ? ((last.close - prev.close) / prev.close) * 100
          : 0;
        return buildIdeaRow(member, {
          price: last.close,
          changePct,
          changePct1m: changePctLookback(bars, 21),
          signals,
        });
      }),
    );
    for (const s of settled) {
      if (s.status === "fulfilled") rows.push(s.value);
    }
  }
  return rows.sort((a, b) => b.score - a.score);
}

const getCachedIdeas = unstable_cache(screenUniverse, ["ideas-screen-v2-crypto"], {
  revalidate: 600,
});

export async function GET(req: NextRequest) {
  const kindParam = (req.nextUrl.searchParams.get("kind") || "all").toLowerCase();
  const kind =
    kindParam === "stock" || kindParam === "etf" || kindParam === "crypto"
      ? (kindParam as UniverseKind)
      : "all";
  const force = req.nextUrl.searchParams.get("force") === "1";

  try {
    const all = force ? await screenUniverse() : await getCachedIdeas();
    const ideas = filterIdeas(all, kind);
    return NextResponse.json({
      generatedAt: new Date().toISOString(),
      kind,
      count: ideas.length,
      ideas,
      disclaimer:
        "Rules-based research helper only - not investment advice.",
    });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : String(e) },
      { status: 500 },
    );
  }
}
