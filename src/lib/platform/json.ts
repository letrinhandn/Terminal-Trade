import { NextResponse } from "next/server";
import { PlatformError } from "@/lib/platform/types";
import type { PlatformResult } from "@/lib/platform/types";

export function ok<T>(result: PlatformResult<T>, init?: ResponseInit) {
  return NextResponse.json(result, init);
}

export function fail(e: unknown) {
  if (e instanceof PlatformError) {
    return NextResponse.json(
      { error: e.message, provider: e.provider },
      { status: e.status },
    );
  }
  return NextResponse.json(
    { error: e instanceof Error ? e.message : String(e) },
    { status: 500 },
  );
}
