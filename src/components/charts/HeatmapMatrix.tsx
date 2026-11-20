"use client";

/** Correlation / return matrix (green-red cells). */
export function HeatmapMatrix({
  labels,
  matrix,
  title,
}: {
  labels: string[];
  /** matrix[i][j] in [-1, 1] */
  matrix: number[][];
  title?: string;
}) {
  if (!labels.length || !matrix.length) {
    return (
      <div className="p-4 text-center text-xs text-[#555]">No matrix data</div>
    );
  }

  return (
    <div className="overflow-x-auto">
      {title && (
        <h3 className="mb-2 text-[10px] font-bold uppercase tracking-wide text-[#ff6600]">
          {title}
        </h3>
      )}
      <table className="w-full min-w-[240px] border-collapse font-mono text-[9px]">
        <thead>
          <tr>
            <th className="p-1 text-left text-[#555]" />
            {labels.map((l) => (
              <th key={l} className="p-1 text-center font-normal text-[#888]">
                {l}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {labels.map((row, i) => (
            <tr key={row}>
              <td className="p-1 text-[#888]">{row}</td>
              {labels.map((col, j) => {
                const v = matrix[i]?.[j] ?? 0;
                return (
                  <td
                    key={`${row}-${col}`}
                    className="p-1 text-center text-black"
                    style={{ background: corrColor(v) }}
                    title={`${row} × ${col}: ${v.toFixed(2)}`}
                  >
                    {v.toFixed(2)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function corrColor(v: number): string {
  const t = Math.max(-1, Math.min(1, v));
  if (t >= 0) {
    const a = 0.15 + t * 0.75;
    return `rgba(34, 197, 94, ${a})`;
  }
  const a = 0.15 + Math.abs(t) * 0.75;
  return `rgba(239, 68, 68, ${a})`;
}
