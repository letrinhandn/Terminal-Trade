import type { PlatformMeta, PlatformResult, ProviderId } from "@/lib/platform/types";

export async function runProvider<T>(
  provider: ProviderId,
  fn: () => Promise<T>,
  warnings: string[] = [],
): Promise<PlatformResult<T>> {
  const t0 = Date.now();
  const data = await fn();
  const meta: PlatformMeta = {
    provider,
    latencyMs: Date.now() - t0,
    asOf: new Date().toISOString(),
    warnings: warnings.length ? warnings : undefined,
  };
  return { data, meta };
}
