/** Shared API envelope types for platform routes. */

export type ProviderId =
  | "yahoo"
  | "finnhub"
  | "fred"
  | "rss"
  | "deribit"
  | "coingecko"
  | "coinbase"
  | "internal";

export interface PlatformMeta {
  provider: ProviderId;
  latencyMs: number;
  asOf: string;
  warnings?: string[];
}

export interface PlatformResult<T> {
  data: T;
  meta: PlatformMeta;
}

export class PlatformError extends Error {
  constructor(
    message: string,
    public status = 500,
    public provider?: ProviderId,
  ) {
    super(message);
    this.name = "PlatformError";
  }
}
