"use client";

import { useMemo, useState } from "react";
import { apiGet } from "@/lib/api";
import { HeatmapMatrix } from "@/components/charts/HeatmapMatrix";
import type { OhlcvBar } from "@/lib/types";

type NodeKind = "start" | "source" | "merge" | "corr" | "out" | "trigger";

type NodeDef = {
  id: string;
  kind: NodeKind;
  typeId: string;
  label: string;
  symbol?: string;
  period?: string;
  interval?: string;
  x: number;
  y: number;
};

const PALETTE: { category: string; items: { typeId: string; label: string; kind: NodeKind }[] }[] =
  [
    {
      category: "Control Flow",
      items: [
        { typeId: "flow.merge", label: "Merge", kind: "merge" },
        { typeId: "flow.split", label: "Split", kind: "merge" },
        { typeId: "flow.if", label: "IF/Else", kind: "merge" },
        { typeId: "flow.loop", label: "Loop", kind: "merge" },
      ],
    },
    {
      category: "Triggers",
      items: [
        { typeId: "trigger.manual", label: "Manual Trigger", kind: "trigger" },
        { typeId: "trigger.schedule", label: "Schedule", kind: "trigger" },
        { typeId: "trigger.price", label: "Price Alert", kind: "trigger" },
      ],
    },
    {
      category: "Market Data",
      items: [
        { typeId: "market.get_historical", label: "Historical OHLCV", kind: "source" },
        { typeId: "market.get_quote", label: "Get Quote", kind: "source" },
      ],
    },
    {
      category: "Analytics",
      items: [
        { typeId: "analytics.correlation", label: "Correlation", kind: "corr" },
        { typeId: "analytics.output", label: "Output", kind: "out" },
      ],
    },
  ];

const TEMPLATE: NodeDef[] = [
  { id: "start", kind: "start", typeId: "trigger.manual", label: "Start", x: 40, y: 160 },
  {
    id: "spy",
    kind: "source",
    typeId: "market.get_historical",
    label: "SPY",
    symbol: "SPY",
    period: "1y",
    interval: "1d",
    x: 200,
    y: 60,
  },
  {
    id: "xlk",
    kind: "source",
    typeId: "market.get_historical",
    label: "XLK (Tech)",
    symbol: "XLK",
    period: "1y",
    interval: "1d",
    x: 200,
    y: 160,
  },
  {
    id: "xlf",
    kind: "source",
    typeId: "market.get_historical",
    label: "XLF (Finance)",
    symbol: "XLF",
    period: "1y",
    interval: "1d",
    x: 200,
    y: 260,
  },
  { id: "merge", kind: "merge", typeId: "flow.merge", label: "Merge", x: 380, y: 160 },
  {
    id: "corr",
    kind: "corr",
    typeId: "analytics.correlation",
    label: "Correlation",
    x: 540,
    y: 160,
  },
  { id: "out", kind: "out", typeId: "analytics.output", label: "Output", x: 700, y: 160 },
];

const EDGES: [string, string][] = [
  ["start", "spy"],
  ["start", "xlk"],
  ["start", "xlf"],
  ["spy", "merge"],
  ["xlk", "merge"],
  ["xlf", "merge"],
  ["merge", "corr"],
  ["corr", "out"],
];

function pearson(a: number[], b: number[]): number {
  const n = Math.min(a.length, b.length);
  if (n < 5) return 0;
  const aa = a.slice(-n);
  const bb = b.slice(-n);
  const ma = aa.reduce((s, x) => s + x, 0) / n;
  const mb = bb.reduce((s, x) => s + x, 0) / n;
  let num = 0;
  let da = 0;
  let db = 0;
  for (let i = 0; i < n; i++) {
    const xa = aa[i] - ma;
    const xb = bb[i] - mb;
    num += xa * xb;
    da += xa * xa;
    db += xb * xb;
  }
  const den = Math.sqrt(da * db);
  return den ? num / den : 0;
}

const TOOLBAR = [
  "NEW",
  "SAVE",
  "LOAD",
  "CLEAR",
  "IMPORT",
  "EXPORT",
  "TEMPLATES",
  "DEPLOY",
] as const;

export function NodesTab({ onStatus }: { onStatus?: (s: string) => void }) {
  const [nodes, setNodes] = useState<NodeDef[]>(TEMPLATE);
  const [selected, setSelected] = useState("spy");
  const [running, setRunning] = useState(false);
  const [corr, setCorr] = useState<{ labels: string[]; matrix: number[][] } | null>(
    null,
  );
  const [log, setLog] = useState(
    "Sector correlation (Yahoo OHLCV)",
  );
  const [wfName, setWfName] = useState("Sector Correlation Analysis");

  const selectedNode = nodes.find((n) => n.id === selected);

  function applyTemplate() {
    setNodes(TEMPLATE.map((n) => ({ ...n })));
    setSelected("spy");
    setCorr(null);
    setWfName("Sector Correlation Analysis");
    setLog("Loaded template: Sector Correlation Analysis");
  }

  function clearCanvas() {
    setNodes([]);
    setCorr(null);
    setSelected("");
    setLog("Canvas cleared");
  }

  function updateSelected(patch: Partial<NodeDef>) {
    if (!selected) return;
    setNodes((prev) =>
      prev.map((n) => (n.id === selected ? { ...n, ...patch } : n)),
    );
  }

  async function execute() {
    setRunning(true);
    setLog("Executing workflow");
    try {
      const sources = nodes.filter((n) => n.kind === "source" && n.symbol);
      if (!sources.length) throw new Error("No market source nodes");
      const start = new Date();
      const years = sources[0]?.period === "1y" ? 1 : 1;
      start.setFullYear(start.getFullYear() - years);
      const startStr = start.toISOString().slice(0, 10);
      const series: { sym: string; rets: number[] }[] = [];
      for (const s of sources) {
        const res = await apiGet<{ data: { bars: OhlcvBar[] } }>(
          `/api/v1/equity/price/historical?symbol=${s.symbol}&start=${startStr}`,
        );
        const closes = (res.data.bars || []).map((b) => b.close);
        const rets: number[] = [];
        for (let i = 1; i < closes.length; i++) {
          rets.push(closes[i - 1] ? (closes[i] - closes[i - 1]) / closes[i - 1] : 0);
        }
        series.push({ sym: s.symbol!, rets });
      }
      const labels = series.map((s) => s.sym);
      const matrix = series.map((a, i) =>
        series.map((b, j) =>
          i === j ? 1 : Number(pearson(a.rets, b.rets).toFixed(3)),
        ),
      );
      setCorr({ labels, matrix });
      setLog(`OK | ${labels.join(", ")} | ${sources[0]?.period || "1y"} daily corr`);
      onStatus?.(`Nodes | correlation ${labels.join("×")}`);
    } catch (e) {
      setLog(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setRunning(false);
    }
  }

  function center(id: string) {
    const n = nodes.find((x) => x.id === id);
    if (!n) return { x: 0, y: 0 };
    return { x: n.x + 60, y: n.y + 22 };
  }

  const edgePaths = useMemo(() => {
    return EDGES.filter(
      ([a, b]) => nodes.some((n) => n.id === a) && nodes.some((n) => n.id === b),
    );
  }, [nodes]);

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-black text-[10px]">
      {/* Workflow toolbar */}
      <div className="flex shrink-0 flex-wrap items-center gap-1 border-b border-[#222] bg-[#0a0a0a] px-2 py-1.5">
        <span className="mr-2 font-mono text-[11px] font-bold text-[#ff9500]">
          NODES
        </span>
        {TOOLBAR.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => {
              if (t === "TEMPLATES" || t === "NEW" || t === "LOAD") applyTemplate();
              else if (t === "CLEAR") clearCanvas();
              else if (t === "SAVE" || t === "EXPORT")
                setLog(`${t}: workflow JSON kept in-session (browser only)`);
              else if (t === "DEPLOY")
                setLog("Deploy not available in this build.");
              else setLog(`${t}: stub`);
            }}
            className="border border-[#333] px-2 py-1 text-[#aaa] hover:border-[#ff6600] hover:text-[#ff8800]"
          >
            {t}
          </button>
        ))}
        <button
          type="button"
          disabled={running}
          onClick={() => void execute()}
          className="ml-auto bg-[#c62828] px-4 py-1 font-bold text-white hover:bg-[#e53935]"
        >
          {running ? "RUNNING" : "EXECUTE"}
        </button>
      </div>

      <div className="flex min-h-0 flex-1">
        {/* Palette */}
        <aside className="w-44 shrink-0 overflow-auto border-r border-[#222] bg-[#050505] p-2">
          <div className="mb-2 text-[9px] font-bold tracking-wider text-[#ff6600]">
            LIBRARY
          </div>
          {PALETTE.map((g) => (
            <div key={g.category} className="mb-3">
              <div className="mb-1 text-[9px] text-[#666]">{g.category}</div>
              <ul className="space-y-0.5">
                {g.items.map((it) => (
                  <li key={it.typeId}>
                    <button
                      type="button"
                      className="w-full border border-transparent px-1 py-0.5 text-left text-[#888] hover:border-[#333] hover:text-[#ff8800]"
                      onClick={() =>
                        setLog(
                          `Palette ${it.typeId} - use TEMPLATES to add nodes`,
                        )
                      }
                    >
                      {it.label}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </aside>

        {/* Canvas */}
        <div className="relative min-h-0 flex-1 overflow-auto bg-[#0a0a0a]">
          <div className="absolute left-2 top-2 z-10 font-mono text-[10px] text-[#ff8800]">
            {wfName}
          </div>
          {!nodes.length ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-[#666]">
              <p>Empty canvas</p>
              <button
                type="button"
                onClick={applyTemplate}
                className="bg-[#ff6600] px-3 py-1.5 font-bold text-black"
              >
                START FROM TEMPLATE
              </button>
            </div>
          ) : (
            <>
              <svg className="absolute inset-0 h-full min-h-[440px] w-full min-w-[820px]">
                <defs>
                  <pattern
                    id="grid"
                    width="24"
                    height="24"
                    patternUnits="userSpaceOnUse"
                  >
                    <path
                      d="M 24 0 L 0 0 0 24"
                      fill="none"
                      stroke="#141414"
                      strokeWidth="1"
                    />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
                {edgePaths.map(([a, b]) => {
                  const A = center(a);
                  const B = center(b);
                  return (
                    <path
                      key={a + b}
                      d={`M ${A.x} ${A.y} C ${(A.x + B.x) / 2} ${A.y}, ${(A.x + B.x) / 2} ${B.y}, ${B.x} ${B.y}`}
                      fill="none"
                      stroke="#444"
                      strokeWidth={2}
                    />
                  );
                })}
              </svg>
              <div className="relative min-h-[440px] min-w-[820px] p-4">
                {nodes.map((n) => (
                  <button
                    key={n.id}
                    type="button"
                    onClick={() => setSelected(n.id)}
                    style={{ left: n.x, top: n.y }}
                    className={`absolute w-[128px] border px-2 py-2 text-left font-mono text-[11px] ${
                      selected === n.id
                        ? "border-[#ff6600] bg-[#1a0a00] text-[#ff9500]"
                        : "border-[#333] bg-[#111] text-[#ccc]"
                    }`}
                  >
                    <div className="truncate text-[8px] uppercase text-[#666]">
                      {n.typeId}
                    </div>
                    <div className="truncate">{n.label}</div>
                    {n.symbol && (
                      <div className="mt-1 text-[9px] text-[#38bdf8]">
                        {n.symbol} | {n.period}/{n.interval}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </>
          )}

          {/* MiniMap stub */}
          <div className="absolute bottom-2 right-2 h-16 w-24 border border-[#333] bg-black/80 p-1">
            <div className="text-[7px] text-[#555]">MINIMAP</div>
            <div className="relative mt-1 h-10 w-full bg-[#111]">
              {nodes.map((n) => (
                <span
                  key={n.id}
                  className="absolute h-1 w-1 bg-[#ff6600]"
                  style={{
                    left: `${(n.x / 800) * 100}%`,
                    top: `${(n.y / 400) * 100}%`,
                  }}
                />
              ))}
            </div>
          </div>

          {corr && (
            <div className="absolute bottom-2 left-2 max-w-sm border border-[#333] bg-black/95 p-2">
              <div className="mb-1 text-[9px] text-[#ff6600]">EXECUTION RESULTS</div>
              <HeatmapMatrix labels={corr.labels} matrix={corr.matrix} />
            </div>
          )}
        </div>

        {/* Properties */}
        <aside className="w-56 shrink-0 overflow-auto border-l border-[#222] bg-[#050505] p-3 font-mono">
          <div className="mb-2 text-[9px] font-bold tracking-wider text-[#ff6600]">
            PROPERTIES
          </div>
          {selectedNode ? (
            <div className="space-y-2 text-[#aaa]">
              <div>
                <div className="text-[#555]">Name</div>
                <input
                  value={selectedNode.label}
                  onChange={(e) => updateSelected({ label: e.target.value })}
                  className="mt-0.5 w-full border border-[#333] bg-black px-1.5 py-1 text-[#ff8800]"
                />
              </div>
              <div>
                <div className="text-[#555]">Type</div>
                <div className="text-[#ccc]">{selectedNode.typeId}</div>
              </div>
              {selectedNode.kind === "source" && (
                <>
                  <div>
                    <div className="text-[#555]">Symbol</div>
                    <input
                      value={selectedNode.symbol || ""}
                      onChange={(e) =>
                        updateSelected({
                          symbol: e.target.value.toUpperCase(),
                          label: e.target.value.toUpperCase() || selectedNode.label,
                        })
                      }
                      className="mt-0.5 w-full border border-[#333] bg-black px-1.5 py-1 text-[#ff8800]"
                    />
                  </div>
                  <div>
                    <div className="text-[#555]">Period</div>
                    <select
                      value={selectedNode.period || "1y"}
                      onChange={(e) => updateSelected({ period: e.target.value })}
                      className="mt-0.5 w-full border border-[#333] bg-black px-1.5 py-1 text-[#ff8800]"
                    >
                      <option value="1y">1y</option>
                      <option value="6mo">6mo</option>
                      <option value="3mo">3mo</option>
                    </select>
                  </div>
                  <div>
                    <div className="text-[#555]">Interval</div>
                    <div>{selectedNode.interval || "1d"}</div>
                  </div>
                </>
              )}
              <label className="flex items-center gap-2 text-[#666]">
                <input type="checkbox" disabled /> Disabled
              </label>
              <label className="flex items-center gap-2 text-[#666]">
                <input type="checkbox" disabled /> Continue on Fail
              </label>
            </div>
          ) : (
            <p className="text-[#555]">Select a node</p>
          )}
          <p className="mt-4 border-t border-[#1a1a1a] pt-2 text-[9px] text-[#555]">
            {log}
          </p>
        </aside>
      </div>
    </div>
  );
}
