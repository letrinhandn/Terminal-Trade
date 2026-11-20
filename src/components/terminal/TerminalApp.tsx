"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { CommandAction, TabId } from "@/lib/types";
import { FKEY_TABS, HELP_TEXT } from "@/lib/commands/parser";
import { CommandPanel } from "@/components/terminal/CommandPanel";
import { DashboardTab } from "@/components/dashboard/DashboardTab";
import { MarketsTab } from "@/components/markets/MarketsTab";
import { EquityTab } from "@/components/equity/EquityTab";
import { SignalsTab } from "@/components/signals/SignalsTab";
import { PortfolioTab } from "@/components/portfolio/PortfolioTab";
import { EconomyTab } from "@/components/economy/EconomyTab";
import { NewsTab } from "@/components/news/NewsTab";
import { IdeasTab } from "@/components/ideas/IdeasTab";
import { OptionsDeskTab } from "@/components/options/OptionsDeskTab";
import { NodesTab } from "@/components/nodes/NodesTab";
import { GeopoliticsTab } from "@/components/geopolitics/GeopoliticsTab";

export function TerminalApp() {
  const [tab, setTab] = useState<TabId>("dashboard");
  const [symbol, setSymbol] = useState("AAPL");
  const [helpOpen, setHelpOpen] = useState(false);
  const [status, setStatus] = useState("Ready");
  const [clock, setClock] = useState("");

  useEffect(() => {
    const tick = () =>
      setClock(
        new Date()
          .toLocaleString(undefined, {
            day: "2-digit",
            month: "short",
            year: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false,
          })
          .toUpperCase(),
      );
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        if (e.key !== "F1" && !e.key.startsWith("F")) return;
      }
      const map: Record<string, TabId> = {
        F1: "dashboard",
        F2: "markets",
        F3: "equity",
        F4: "signals",
        F5: "portfolio",
        F6: "economy",
        F7: "news",
        F8: "geopolitics",
      };
      if (map[e.key]) {
        e.preventDefault();
        setTab(map[e.key]);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const onExecute = useCallback((action: CommandAction) => {
    if (action.type === "help") {
      setHelpOpen(true);
      setStatus("Help");
      return;
    }
    if (action.type === "noop") {
      if (action.message) setStatus(action.message);
      return;
    }
    if (action.symbol) setSymbol(action.symbol.toUpperCase());
    if (action.tab) setTab(action.tab);
    else if (action.type === "symbol" && action.symbol) setTab("equity");

    const bits = [
      action.tab?.toUpperCase(),
      action.symbol,
      action.view,
      action.section,
    ].filter(Boolean);
    setStatus(bits.length ? bits.join(" / ") : "OK");
  }, []);

  const titleSymbol = useMemo(() => symbol.toUpperCase(), [symbol]);
  const onStatus = useCallback((s: string) => setStatus(s), []);

  return (
    <div className="flex min-h-screen flex-col bg-black text-[#f2f2f2]">
      <header className="border-b border-[#ff6600] bg-black px-3 py-1.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-3">
            <img
              src="/brand/logo-mark.svg"
              alt=""
              width={28}
              height={28}
              className="h-7 w-7 shrink-0"
            />
            <h1 className="font-display text-lg font-bold tracking-wide text-[#ff9500]">
              TERMINAL TRADE
            </h1>
            <span className="font-mono text-[10px] text-[#666]">
              Default / {tab}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-3 font-mono text-[10px]">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" />
              LIVE
            </span>
            <span className="text-[#888]">{clock}</span>
            <span className="text-[#ff8800]">{titleSymbol}</span>
            <span className="text-[#555]">Ctrl+K</span>
          </div>
        </div>
      </header>

      <CommandPanel onExecute={onExecute} />

      <nav className="flex flex-wrap gap-1 border-b border-[#333] bg-black px-2 pt-2">
        {FKEY_TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-3 py-2 text-xs font-bold sm:px-4 sm:text-sm ${
              tab === t.id
                ? "bg-[#ff6600] text-black"
                : "border border-[#333] bg-[#1a1a1a] text-[#888] hover:bg-[#333] hover:text-[#ff8800]"
            }`}
          >
            <span className="mr-1 text-[10px] opacity-60">{t.key}</span>
            {t.label}
          </button>
        ))}
      </nav>

      <main className="flex min-h-0 flex-1 flex-col overflow-hidden">
        {tab === "dashboard" && (
          <DashboardTab
            symbol={symbol}
            onSymbolChange={setSymbol}
            onGoEquity={() => setTab("equity")}
            onStatus={onStatus}
          />
        )}
        {tab === "markets" && (
          <MarketsTab
            symbol={symbol}
            onSymbolChange={setSymbol}
            onGoEquity={() => setTab("equity")}
            onStatus={onStatus}
          />
        )}
        {tab === "equity" && (
          <EquityTab
            symbol={symbol}
            onSymbolChange={setSymbol}
            onStatus={onStatus}
            onGoSignals={() => setTab("signals")}
            onGoNews={() => setTab("news")}
          />
        )}
        {tab === "signals" && (
          <SignalsTab symbol={symbol} onSymbolChange={setSymbol} />
        )}
        {tab === "portfolio" && (
          <PortfolioTab
            symbol={symbol}
            onSymbolChange={setSymbol}
            onGoIdeas={() => setTab("ideas")}
          />
        )}
        {tab === "economy" && <EconomyTab onStatus={onStatus} />}
        {tab === "news" && (
          <NewsTab
            symbol={symbol}
            onSymbolChange={setSymbol}
            onStatus={onStatus}
          />
        )}
        {tab === "nodes" && <NodesTab onStatus={onStatus} />}
        {tab === "geopolitics" && <GeopoliticsTab onStatus={onStatus} />}
        {tab === "ideas" && (
          <IdeasTab
            symbol={symbol}
            onSymbolChange={setSymbol}
            onGoPortfolio={() => setTab("portfolio")}
          />
        )}
        {tab === "options" && (
          <OptionsDeskTab symbol={symbol} onStatus={onStatus} />
        )}
      </main>

      <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-[#222] bg-black px-3 py-1 font-mono text-[10px] text-[#666]">
        <span className="truncate text-[#aaa]">{status}</span>
        <span className="flex flex-wrap gap-3">
          <span>v4.0.0</span>
          <span className="text-emerald-500">CONNECTED</span>
          <span>{tab.toUpperCase()}</span>
          <span className="text-[#ff8800]">READY</span>
        </span>
      </footer>

      {helpOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
          <div className="max-h-[80vh] w-full max-w-xl overflow-auto border-2 border-[#ff6600] bg-[#0a0a0a] p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-bold text-[#ff6600]">
                Command Reference
              </h2>
              <button
                type="button"
                className="text-[#ff8800]"
                onClick={() => setHelpOpen(false)}
              >
                Close
              </button>
            </div>
            <pre className="font-mono whitespace-pre-wrap text-sm text-[#ccc]">
              {HELP_TEXT}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
