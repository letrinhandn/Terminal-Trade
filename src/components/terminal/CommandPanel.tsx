"use client";

import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import type { CommandAction } from "@/lib/types";
import {
  resolveCommand,
  resolveSuggestion,
  searchCommands,
  type SuggestionRow,
} from "@/lib/commands/engine";

const GROUP_LABEL: Record<string, string> = {
  instrument: "INSTRUMENTS",
  screen: "SCREENS",
  action: "ACTIONS",
  help: "HELP",
  data: "DATA",
};

export function CommandPanel({
  onExecute,
  placeholder = "Command (Ctrl+K): AAPL CHART, OPEN PF, HELP",
}: {
  onExecute: (action: CommandAction) => void;
  placeholder?: string;
}) {
  const [cmd, setCmd] = useState("");
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState<SuggestionRow[]>([]);
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = useId();

  const refresh = useCallback((value: string, show: boolean) => {
    const next = searchCommands(value, 12);
    setRows(next);
    setActive(0);
    setOpen(show && (value.trim().length > 0 || next.length > 0));
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent | globalThis.KeyboardEvent) => {
      const isInput =
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement;
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        inputRef.current?.focus();
        refresh(cmd, true);
        return;
      }
      if (e.key === "/" && !isInput) {
        e.preventDefault();
        inputRef.current?.focus();
        refresh(cmd, true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [cmd, refresh]);

  function onChange(value: string) {
    setCmd(value);
    refresh(value, true);
  }

  function run(action: CommandAction) {
    setOpen(false);
    setCmd("");
    setRows([]);
    onExecute(action);
  }

  function submit() {
    if (open && rows[active]) {
      run(resolveSuggestion(rows[active]));
      return;
    }
    run(resolveCommand(cmd));
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      setRows([]);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!open) refresh(cmd, true);
      setActive((i) => Math.min(i + 1, Math.max(0, rows.length - 1)));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
      return;
    }
    if (e.key === "Tab" && open && rows[active]) {
      e.preventDefault();
      setCmd(rows[active].fill);
      refresh(rows[active].fill, true);
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      submit();
    }
  }

  let lastGroup = "";

  return (
    <div className="relative border-b-2 border-[#ff6600] bg-[#0a0a0a] px-3 py-2">
      <div className="flex items-center gap-3">
        <span className="font-mono text-lg font-bold text-[#ff6600]">&gt;&gt;</span>
        <input
          ref={inputRef}
          value={cmd}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          onFocus={() => refresh(cmd, true)}
          onBlur={() => {
            // delay so click on suggestion registers
            window.setTimeout(() => setOpen(false), 150);
          }}
          placeholder={placeholder}
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          className="font-mono flex-1 border-2 border-[#ff6600] bg-black px-3 py-2 text-[#ff8800] outline-none focus:border-[#ff8800]"
        />
        <button
          type="button"
          onClick={submit}
          className="bg-[#ff6600] px-4 py-2 text-sm font-bold text-black hover:bg-[#ff8800]"
        >
          Execute
        </button>
      </div>

      {open && rows.length > 0 && (
        <ul
          id={listId}
          role="listbox"
          className="absolute left-12 right-28 z-30 mt-1 max-h-80 overflow-auto border-2 border-[#ff6600] bg-black font-mono text-sm shadow-xl"
        >
          {rows.map((r, i) => {
            const showHead = r.group !== lastGroup;
            lastGroup = r.group;
            return (
              <li key={r.key}>
                {showHead && (
                  <div className="sticky top-0 border-b border-[#1a1a1a] bg-[#0a0a0a] px-3 py-1 text-[9px] tracking-[0.12em] text-[#666]">
                    {GROUP_LABEL[r.group] || r.group.toUpperCase()}
                  </div>
                )}
                <button
                  type="button"
                  role="option"
                  aria-selected={i === active}
                  className={`flex w-full items-start justify-between gap-3 border-b border-[#141414] px-3 py-2 text-left ${
                    i === active
                      ? "bg-[#1a0a00] text-[#ff9500]"
                      : "text-[#ccc] hover:bg-[#111]"
                  }`}
                  onMouseDown={(e) => e.preventDefault()}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => run(resolveSuggestion(r))}
                >
                  <span>
                    <span className="block font-bold text-[#ff8800]">
                      {r.title}
                    </span>
                    <span className="block text-[10px] text-[#666]">
                      {r.subtitle}
                    </span>
                  </span>
                  {r.shortcut && (
                    <span className="shrink-0 text-[10px] text-[#555]">
                      {r.shortcut}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
          <li className="px-3 py-1.5 text-[9px] text-[#444]">
            Up/Down select, Tab fill, Enter run, Esc close, Ctrl+K focus
          </li>
        </ul>
      )}
    </div>
  );
}
