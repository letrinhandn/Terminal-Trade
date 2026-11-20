import { NextRequest } from "next/server";
import { fetchNews } from "@/lib/data/news";
import { runProvider } from "@/lib/platform/run";
import { fail, ok } from "@/lib/platform/json";

export const maxDuration = 60;

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q") || undefined;
  const limit = Math.min(
    Math.max(Number(req.nextUrl.searchParams.get("limit") || 40), 1),
    80,
  );
  try {
    const result = await runProvider("rss", async () => ({
      articles: await fetchNews(limit, q),
      q: q ?? null,
    }));
    return ok(result);
  } catch (e) {
    return fail(e);
  }
}
