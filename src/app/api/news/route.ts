import { NextRequest, NextResponse } from "next/server";
import { fetchNews } from "@/lib/data/news";

export const maxDuration = 60;

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q") || undefined;
  const limitRaw = Number(req.nextUrl.searchParams.get("limit") || 40);
  const limit = Number.isFinite(limitRaw)
    ? Math.min(Math.max(limitRaw, 1), 80)
    : 40;
  try {
    const articles = await fetchNews(limit, q);
    return NextResponse.json({ articles, q: q ?? null });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : String(e) },
      { status: 500 },
    );
  }
}
