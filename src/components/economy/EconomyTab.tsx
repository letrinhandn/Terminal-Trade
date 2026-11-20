"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet } from "@/lib/api";
import { EquityChart } from "@/components/charts/EquityChart";

type Preset = { id: string; label: string };
type SeriesEnv = {
  data: {
    seriesId: string;
    title: string;
    units: string;
    observations: { date: string; value: number | null }[];
  };
  meta?: { provider?: string; latencyMs?: number };
};

export function EconomyTab({ onStatus }: { onStatus?: (s: string) => void }) {
  const [presets, setPresets] = useState<Preset[]>([]);
  const [configured, setConfigured] = useState(false);
  const [seriesId, setSeriesId] = useState("UNRATE");
  const [title, setTitle] = useState("");
  const [units, setUnits] = useState("");
  const [points, setPoints] = useState<{ date: string; equity: number }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiGet<{ configured: boolean; presets: Preset[] }>(
      "/api/v1/economy/fred/series?list=1",
    )
      .then((r) => {
        setConfigured(r.configured);
        setPresets(r.presets || []);
      })
      .catch(() => setConfigured(false));
  }, []);

  useEffect(() => {
    if (!configured) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const start = new Date();
        start.setFullYear(start.getFullYear() - 10);
        const res = await apiGet<SeriesEnv>(
          `/api/v1/economy/fred/series?id=${encodeURIComponent(seriesId)}&start=${start.toISOString().slice(0, 10)}`,
        );
        if (cancelled) return;
        setTitle(res.data.title);
        setUnits(res.data.units);
        setPoints(
          res.data.observations
            .filter((o) => o.value != null)
            .map((o) => ({ date: o.date, equity: o.value as number })),
        );
        onStatus?.(
          `FRED ${seriesId} | ${res.meta?.latencyMs ?? "?"}ms | ${res.data.observations.length} obs`,
        );
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e));
          setPoints([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [seriesId, configured, onStatus]);

  const latest = useMemo(
    () => (points.length ? points[points.length - 1] : null),
    [points],
  );

  return (
    <div className="space-y-4 p-4">
      <div>
        <h2 className="text-lg font-bold text-[#ff9500]">Economy</h2>
        <p className="text-xs text-[#666]">
          FRED macro series
        </p>
      </div>

      {!configured && (
        <div className="border border-amber-800 bg-[#1a1000] p-4 text-sm text-amber-200">
          Set <code className="text-[#ff8800]">FRED_API_KEY</code> in{" "}
          <code>.env.local</code> (free at fred.stlouisfed.org) then restart the
          server.
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {presets.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => setSeriesId(p.id)}
            className={`rounded px-3 py-1.5 text-xs font-bold ${
              seriesId === p.id
                ? "bg-[#ff6600] text-black"
                : "border border-[#333] text-[#888]"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}
      {loading && <p className="text-sm text-[#666]">Loading series</p>}

      <div className="grid gap-3 lg:grid-cols-[220px_1fr]">
        <div className="border border-[#333] bg-[#0a0a0a] p-4">
          <div className="text-[10px] uppercase text-[#666]">Latest</div>
          <div className="font-mono text-2xl text-[#ff9500]">
            {latest ? latest.equity.toLocaleString() : "-"}
          </div>
          <div className="mt-1 text-xs text-[#888]">{title || seriesId}</div>
          <div className="text-[10px] text-[#555]">{units}</div>
          <div className="mt-2 font-mono text-[10px] text-[#666]">
            {latest?.date}
          </div>
        </div>
        <div className="border border-[#333] bg-black p-2">
          <EquityChart data={points} />
        </div>
      </div>
    </div>
  );
}
