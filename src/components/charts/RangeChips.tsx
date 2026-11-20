"use client";

import type { ChartRange } from "@/components/charts/chartTheme";

const RANGES: ChartRange[] = ["1M", "3M", "1Y", "5Y"];

export function RangeChips({
  value,
  onChange,
}: {
  value: ChartRange;
  onChange: (r: ChartRange) => void;
}) {
  return (
    <div className="flex gap-1">
      {RANGES.map((r) => (
        <button
          key={r}
          type="button"
          onClick={() => onChange(r)}
          className={`rounded px-2 py-0.5 font-mono text-[10px] ${
            value === r
              ? "bg-[#ff6600] font-bold text-black"
              : "border border-[#333] text-[#888] hover:border-[#ff6600] hover:text-[#ff8800]"
          }`}
        >
          {r}
        </button>
      ))}
    </div>
  );
}
