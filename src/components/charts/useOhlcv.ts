"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { OhlcvBar } from "@/lib/types";
import {
  type ChartRange,
  startFromRange,
} from "@/components/charts/chartTheme";

type HistPayload = {
  data: {
    symbol: string;
    bars: OhlcvBar[];
    sourceNote?: string;
  };
  meta?: { provider?: string };
};

export function useOhlcv(symbol: string, range: ChartRange) {
  const [bars, setBars] = useState<OhlcvBar[]>([]);
  const [sourceNote, setSourceNote] = useState<string | undefined>();
  const [provider, setProvider] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const start = startFromRange(range);
    setLoading(true);
    setError(null);
    void (async () => {
      try {
        const res = await apiGet<HistPayload>(
          `/api/v1/equity/price/historical?symbol=${encodeURIComponent(symbol)}&start=${start}`,
        );
        if (cancelled) return;
        setBars(res.data.bars || []);
        setSourceNote(res.data.sourceNote);
        setProvider(res.meta?.provider);
      } catch (e) {
        if (cancelled) return;
        setBars([]);
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [symbol, range]);

  return { bars, sourceNote, provider, loading, error };
}
