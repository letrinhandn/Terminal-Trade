import { cached } from "@/lib/platform/cache";
import { runProvider } from "@/lib/platform/run";
import { PlatformError, type PlatformResult } from "@/lib/platform/types";

export type FredObservation = { date: string; value: number | null };

export type FredSeriesResult = {
  seriesId: string;
  title: string;
  units: string;
  observations: FredObservation[];
};

function fredKey(): string {
  return process.env.FRED_API_KEY || "";
}

export function isFredConfigured(): boolean {
  return Boolean(fredKey());
}

/** Curated macro dashboard series. */
export const FRED_PRESETS: { id: string; label: string }[] = [
  { id: "GDP", label: "US GDP" },
  { id: "CPIAUCSL", label: "CPI All Urban" },
  { id: "UNRATE", label: "Unemployment Rate" },
  { id: "FEDFUNDS", label: "Fed Funds Rate" },
  { id: "T10Y2Y", label: "10Y-2Y Spread" },
  { id: "DGS10", label: "10Y Treasury" },
  { id: "VIXCLS", label: "VIX" },
  { id: "DTWEXBGS", label: "USD Broad Index" },
];

export async function fredSeries(
  seriesId: string,
  start?: string,
  end?: string,
): Promise<PlatformResult<FredSeriesResult>> {
  const key = fredKey();
  if (!key) {
    throw new PlatformError(
      "FRED_API_KEY not configured - get a free key at https://fred.stlouisfed.org/",
      400,
      "fred",
    );
  }
  const id = seriesId.toUpperCase();
  return runProvider("fred", () =>
    cached(`fred:${id}:${start || ""}:${end || ""}`, 900_000, async () => {
      const metaUrl = new URL("https://api.stlouisfed.org/fred/series");
      metaUrl.searchParams.set("series_id", id);
      metaUrl.searchParams.set("api_key", key);
      metaUrl.searchParams.set("file_type", "json");

      const obsUrl = new URL(
        "https://api.stlouisfed.org/fred/series/observations",
      );
      obsUrl.searchParams.set("series_id", id);
      obsUrl.searchParams.set("api_key", key);
      obsUrl.searchParams.set("file_type", "json");
      if (start) obsUrl.searchParams.set("observation_start", start);
      if (end) obsUrl.searchParams.set("observation_end", end);

      const [metaRes, obsRes] = await Promise.all([
        fetch(metaUrl.toString()),
        fetch(obsUrl.toString()),
      ]);
      if (!metaRes.ok) {
        throw new PlatformError(`FRED meta ${metaRes.status}`, 502, "fred");
      }
      if (!obsRes.ok) {
        throw new PlatformError(`FRED obs ${obsRes.status}`, 502, "fred");
      }
      const metaJson = (await metaRes.json()) as {
        seriess?: { title?: string; units?: string }[];
      };
      const obsJson = (await obsRes.json()) as {
        observations?: { date: string; value: string }[];
      };
      const s = metaJson.seriess?.[0];
      const observations: FredObservation[] = (obsJson.observations || [])
        .map((o) => ({
          date: o.date,
          value: o.value === "." ? null : Number(o.value),
        }))
        .filter((o) => o.value == null || Number.isFinite(o.value));

      return {
        seriesId: id,
        title: s?.title || id,
        units: s?.units || "",
        observations,
      };
    }),
  );
}
