"use client";

import type { ReactNode } from "react";

/** Dense equity widgets: orange brand, teal labels. */

export function Panel({
  title,
  children,
  className = "",
  bodyClassName = "",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section
      className={`flex min-h-0 flex-col overflow-hidden rounded-sm border border-[#2a2a2a] bg-[#0a0a0a] ${className}`}
    >
      <header className="shrink-0 border-b border-[#1f1f1f] px-3 py-2 text-[11px] font-semibold tracking-[0.06em] text-[#ff8c00]">
        {title}
      </header>
      <div
        className={`min-h-0 flex-1 overflow-auto p-3 [scrollbar-width:thin] [scrollbar-color:#333_transparent] ${bodyClassName}`}
      >
        {children}
      </div>
    </section>
  );
}

export function Kv({
  label,
  value,
  valueClass = "text-[#eee]",
}: {
  label: string;
  value: React.ReactNode;
  valueClass?: string;
}) {
  return (
    <div className="grid grid-cols-[auto_1fr] items-baseline gap-x-4 gap-y-0 py-1.5 text-[12px] leading-snug">
      <span className="text-[#5ec8c0]">{label}</span>
      <span className={`min-w-0 truncate text-right ${valueClass}`}>
        {value ?? "-"}
      </span>
    </div>
  );
}

function fmt(v: unknown): string {
  if (v == null) return "-";
  if (typeof v === "object" && v && "raw" in (v as object)) {
    return fmt((v as { raw: unknown }).raw);
  }
  if (typeof v === "object" && v && "fmt" in (v as object)) {
    return String((v as { fmt: unknown }).fmt);
  }
  if (typeof v === "number") {
    if (!Number.isFinite(v)) return "-";
    if (Math.abs(v) >= 1e12) return `${(v / 1e12).toFixed(2)}T`;
    if (Math.abs(v) >= 1e9) return `${(v / 1e9).toFixed(2)}B`;
    if (Math.abs(v) >= 1e6) return `${(v / 1e6).toFixed(2)}M`;
    if (Math.abs(v) < 1 && Math.abs(v) > 0) return v.toFixed(4);
    return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  if (typeof v === "string") return v;
  try {
    return JSON.stringify(v);
  } catch {
    return String(v);
  }
}

export function pick(obj: unknown, path: string): unknown {
  if (!obj || typeof obj !== "object") return undefined;
  const parts = path.split(".");
  let cur: unknown = obj;
  for (const p of parts) {
    if (!cur || typeof cur !== "object") return undefined;
    cur = (cur as Record<string, unknown>)[p];
  }
  return cur;
}

export function StatGrid({
  rows,
}: {
  rows: {
    label: string;
    path?: string;
    value?: unknown;
    src?: unknown;
    tone?: "up" | "down" | "neutral";
  }[];
}) {
  return (
    <div className="divide-y divide-[#1a1a1a]">
      {rows.map((r) => {
        const val = r.value ?? (r.path && r.src ? pick(r.src, r.path) : undefined);
        const isNode =
          typeof val === "object" &&
          val !== null &&
          "$$typeof" in (val as object);
        const tone =
          r.tone ||
          (typeof val === "number"
            ? val > 0
              ? "up"
              : val < 0
                ? "down"
                : "neutral"
            : "neutral");
        const valueClass =
          tone === "up"
            ? "text-emerald-400"
            : tone === "down"
              ? "text-red-400"
              : "text-[#eee]";
        return (
          <Kv
            key={r.label}
            label={r.label}
            value={isNode ? (val as ReactNode) : fmt(val)}
            valueClass={valueClass}
          />
        );
      })}
    </div>
  );
}

export function StatementTable({
  rows,
  fields,
}: {
  rows: Record<string, unknown>[];
  fields: { key: string; label: string }[];
}) {
  const slice = rows.slice(0, 4);
  if (!slice.length) {
    return <p className="text-xs text-[#666]">No statement rows</p>;
  }
  const dates = slice.map((r) => {
    const end = r.endDate as { fmt?: string; raw?: number } | string | undefined;
    if (typeof end === "string") return end.slice(0, 10);
    if (end && typeof end === "object" && end.fmt)
      return String(end.fmt).slice(0, 10);
    return "-";
  });
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[480px] text-[11px]">
        <thead className="text-[#40e0d0]">
          <tr>
            <th className="p-1 text-left font-normal">Field</th>
            {dates.map((d) => (
              <th key={d} className="p-1 text-right font-normal">
                {d}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {fields.map((f) => (
            <tr key={f.key} className="border-t border-[#1a1a1a]">
              <td className="p-1 text-[#40e0d0]">{f.label}</td>
              {slice.map((r, i) => (
                <td key={i} className="p-1 text-right text-[#ddd]">
                  {fmt(r[f.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function JsonList({
  title,
  items,
  mapItem,
}: {
  title?: string;
  items: unknown;
  mapItem: (item: Record<string, unknown>, i: number) => React.ReactNode;
}) {
  const arr = Array.isArray(items)
    ? items
    : items &&
        typeof items === "object" &&
        Array.isArray((items as { ownershipList?: unknown }).ownershipList)
      ? ((items as { ownershipList: unknown[] }).ownershipList as unknown[])
      : items &&
          typeof items === "object" &&
          Array.isArray((items as { holders?: unknown }).holders)
        ? ((items as { holders: unknown[] }).holders as unknown[])
        : items &&
            typeof items === "object" &&
            Array.isArray((items as { transactions?: unknown }).transactions)
          ? ((items as { transactions: unknown[] }).transactions as unknown[])
          : items &&
              typeof items === "object" &&
              Array.isArray((items as { filings?: unknown }).filings)
            ? ((items as { filings: unknown[] }).filings as unknown[])
            : items &&
                typeof items === "object" &&
                Array.isArray((items as { history?: unknown }).history)
              ? ((items as { history: unknown[] }).history as unknown[])
              : [];
  if (!arr.length) {
    return <p className="text-xs text-[#666]">No {title || "rows"}</p>;
  }
  return (
    <ul className="space-y-2">
      {arr.slice(0, 12).map((it, i) => (
        <li
          key={i}
          className="border-b border-[#1a1a1a] pb-2 text-[11px] text-[#ccc]"
        >
          {mapItem((it || {}) as Record<string, unknown>, i)}
        </li>
      ))}
    </ul>
  );
}

function num(v: unknown): number {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string" && v.trim() && Number.isFinite(Number(v)))
    return Number(v);
  if (v && typeof v === "object" && "raw" in (v as object))
    return num((v as { raw: unknown }).raw);
  return 0;
}

function asDate(v: unknown): string {
  if (v == null) return "-";
  if (Array.isArray(v) && v.length) return asDate(v[0]);
  if (typeof v === "number") {
    const ms = v < 1e12 ? v * 1000 : v;
    return new Date(ms).toISOString().slice(0, 10);
  }
  if (typeof v === "string") {
    const d = Date.parse(v);
    return Number.isFinite(d) ? new Date(d).toISOString().slice(0, 10) : v.slice(0, 10);
  }
  if (v && typeof v === "object" && "fmt" in (v as object))
    return String((v as { fmt: unknown }).fmt).slice(0, 10);
  return "-";
}

/** Analyst recommendation trend - stacked bars, not raw JSON. */
export function RecommendationBars({
  trend,
}: {
  trend: unknown;
}) {
  const rows = Array.isArray(trend)
    ? trend
    : trend &&
        typeof trend === "object" &&
        Array.isArray((trend as { trend?: unknown }).trend)
      ? ((trend as { trend: Record<string, unknown>[] }).trend as Record<
          string,
          unknown
        >[])
      : [];
  if (!rows.length) {
    return <p className="text-xs text-[#666]">No recommendation trend</p>;
  }
  return (
    <div className="space-y-3">
      {rows.slice(0, 6).map((r, i) => {
        const sb = num(r.strongBuy);
        const b = num(r.buy);
        const h = num(r.hold);
        const s = num(r.sell);
        const ss = num(r.strongSell);
        const total = sb + b + h + s + ss || 1;
        const pct = (n: number) => `${((n / total) * 100).toFixed(0)}%`;
        return (
          <div key={String(r.period || i)} className="space-y-1">
            <div className="flex justify-between font-mono text-[10px] text-[#888]">
              <span className="text-[#ff8800]">{String(r.period || "-")}</span>
              <span>
                Buy {sb + b} | Hold {h} | Sell {s + ss}
              </span>
            </div>
            <div className="flex h-2.5 w-full overflow-hidden bg-[#1a1a1a]">
              <div className="bg-emerald-600" style={{ width: pct(sb) }} title={`Strong buy ${sb}`} />
              <div className="bg-emerald-400" style={{ width: pct(b) }} title={`Buy ${b}`} />
              <div className="bg-yellow-500" style={{ width: pct(h) }} title={`Hold ${h}`} />
              <div className="bg-orange-500" style={{ width: pct(s) }} title={`Sell ${s}`} />
              <div className="bg-red-500" style={{ width: pct(ss) }} title={`Strong sell ${ss}`} />
            </div>
            <div className="grid grid-cols-5 gap-1 font-mono text-[9px] text-[#666]">
              <span className="text-emerald-500">SB {sb}</span>
              <span className="text-emerald-400">B {b}</span>
              <span className="text-yellow-500">H {h}</span>
              <span className="text-orange-400">S {s}</span>
              <span className="text-red-400">SS {ss}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function EarningsQuarterTable({
  quarterly,
}: {
  quarterly: unknown;
}) {
  const rows = Array.isArray(quarterly) ? quarterly : [];
  if (!rows.length) {
    return <p className="text-xs text-[#666]">No quarterly earnings</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[420px] border-collapse font-mono text-[10px]">
        <thead className="text-[#5ec8c0]">
          <tr>
            {["Quarter", "Actual", "Estimate", "Diff", "Surprise%", "Reported"].map(
              (h) => (
                <th key={h} className="p-1 text-left font-normal">
                  {h}
                </th>
              ),
            )}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 12).map((r, i) => {
            const row = (r || {}) as Record<string, unknown>;
            const surprise = num(row.surprisePct);
            return (
              <tr key={i} className="border-t border-[#1a1a1a]">
                <td className="p-1 text-[#ff8800]">
                  {String(row.date || row.calendarQuarter || "-")}
                </td>
                <td className="p-1">{fmt(row.actual)}</td>
                <td className="p-1">{fmt(row.estimate)}</td>
                <td className="p-1">{fmt(row.difference)}</td>
                <td
                  className={`p-1 ${
                    surprise > 0
                      ? "text-emerald-400"
                      : surprise < 0
                        ? "text-red-400"
                        : "text-[#aaa]"
                  }`}
                >
                  {fmt(row.surprisePct)}
                  {row.surprisePct != null ? "%" : ""}
                </td>
                <td className="p-1 text-[#888]">{asDate(row.reportedDate)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function CalendarEventCards({
  events,
}: {
  events: unknown;
}) {
  if (!events || typeof events !== "object") {
    return <p className="text-xs text-[#666]">No calendar events</p>;
  }
  const e = events as Record<string, unknown>;
  const earn =
    e.earnings && typeof e.earnings === "object"
      ? (e.earnings as Record<string, unknown>)
      : {};
  const earnDates = Array.isArray(earn.earningsDate)
    ? earn.earningsDate
    : earn.earningsDate
      ? [earn.earningsDate]
      : [];
  const callDates = Array.isArray(earn.earningsCallDate)
    ? earn.earningsCallDate
    : earn.earningsCallDate
      ? [earn.earningsCallDate]
      : [];

  return (
    <div className="space-y-2">
      <StatGrid
        rows={[
          {
            label: "Next earnings",
            value: earnDates.map(asDate).filter((d) => d !== "-").join(", ") || "-",
          },
          {
            label: "Earnings call",
            value: callDates.map(asDate).filter((d) => d !== "-").join(", ") || "-",
          },
          {
            label: "EPS avg / low / high",
            value: `${fmt(earn.earningsAverage)} / ${fmt(earn.earningsLow)} / ${fmt(earn.earningsHigh)}`,
          },
          {
            label: "Rev avg",
            value: fmt(earn.revenueAverage),
          },
          {
            label: "Ex-dividend",
            value: asDate(e.exDividendDate),
          },
          {
            label: "Dividend date",
            value: asDate(e.dividendDate),
          },
          {
            label: "Estimate?",
            value: earn.isEarningsDateEstimate === true ? "Yes" : earn.isEarningsDateEstimate === false ? "No" : "-",
          },
        ]}
      />
    </div>
  );
}

export function SecFilingsList({ filings }: { filings: unknown }) {
  const list =
    Array.isArray(filings)
      ? filings
      : filings &&
          typeof filings === "object" &&
          Array.isArray((filings as { filings?: unknown }).filings)
        ? ((filings as { filings: unknown[] }).filings as unknown[])
        : [];
  if (!list.length) {
    return (
      <p className="text-xs text-[#666]">
        No SEC filings in this Yahoo bundle
      </p>
    );
  }
  return (
    <ul className="space-y-2">
      {list.slice(0, 15).map((raw, i) => {
        const f = (raw || {}) as Record<string, unknown>;
        const url = typeof f.edgarUrl === "string" ? f.edgarUrl : null;
        return (
          <li key={i} className="border-b border-[#1a1a1a] pb-2 text-[11px]">
            <div className="flex flex-wrap gap-2 font-mono text-[9px] text-[#666]">
              <span className="text-[#ff8800]">{asDate(f.date)}</span>
              <span className="text-[#5ec8c0]">{String(f.type || "-")}</span>
            </div>
            {url ? (
              <a
                href={url}
                target="_blank"
                rel="noreferrer"
                className="text-[#ccc] hover:text-[#ff8800]"
              >
                {String(f.title || "Filing")}
              </a>
            ) : (
              <span className="text-[#ccc]">{String(f.title || "Filing")}</span>
            )}
          </li>
        );
      })}
    </ul>
  );
}

export { fmt, asDate, num };
