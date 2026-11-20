/// <reference lib="webworker" />

/**
 * Evaluates custom strategy code in a Web Worker (never on the server).
 * Expected: function run(bars) => barsWithSignal
 */

export type WorkerBar = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  signal?: number;
};

export type WorkerRequest = {
  code: string;
  bars: WorkerBar[];
};

export type WorkerResponse =
  | { ok: true; bars: WorkerBar[] }
  | { ok: false; error: string };

self.onmessage = (event: MessageEvent<WorkerRequest>) => {
  const { code, bars } = event.data;
  try {
    // Allow `export function run` / `export default` style from the editor.
    const cleaned = code
      .replace(/^\s*export\s+default\s+/m, "")
      .replace(/^\s*export\s+/gm, "");

    const runner = new Function(
      "bars",
      `${cleaned}\n; if (typeof run !== "function") throw new Error("Define function run(bars)");\nreturn run(bars);`,
    );

    const out = runner(bars);
    if (!Array.isArray(out)) {
      throw new Error("run(bars) must return an array");
    }

    (self as unknown as DedicatedWorkerGlobalScope).postMessage({
      ok: true,
      bars: out,
    } satisfies WorkerResponse);
  } catch (e) {
    (self as unknown as DedicatedWorkerGlobalScope).postMessage({
      ok: false,
      error: e instanceof Error ? e.message : String(e),
    } satisfies WorkerResponse);
  }
};
