/** Shared crypto symbol helpers (Yahoo / CoinGecko / Coinbase). */

export const CRYPTO_MAJORS = new Set([
  "BTC",
  "ETH",
  "SOL",
  "DOGE",
  "AVAX",
  "ADA",
  "DOT",
  "LINK",
  "XRP",
  "LTC",
  "BNB",
  "MATIC",
  "NEAR",
  "ATOM",
]);

/** CoinGecko coin ids for majors */
export const COINGECKO_IDS: Record<string, string> = {
  BTC: "bitcoin",
  ETH: "ethereum",
  SOL: "solana",
  DOGE: "dogecoin",
  AVAX: "avalanche-2",
  ADA: "cardano",
  DOT: "polkadot",
  LINK: "chainlink",
  XRP: "ripple",
  LTC: "litecoin",
  BNB: "binancecoin",
  MATIC: "matic-network",
  NEAR: "near",
  ATOM: "cosmos",
};

/** Coinbase Exchange product ids (spot USD). Source prices are exchange-specific. */
export const COINBASE_PRODUCTS: Record<string, string> = {
  BTC: "BTC-USD",
  ETH: "ETH-USD",
  SOL: "SOL-USD",
  DOGE: "DOGE-USD",
  AVAX: "AVAX-USD",
  ADA: "ADA-USD",
  DOT: "DOT-USD",
  LINK: "LINK-USD",
  XRP: "XRP-USD",
  LTC: "LTC-USD",
  ATOM: "ATOM-USD",
  NEAR: "NEAR-USD",
};

export function baseCryptoSymbol(symbol: string): string {
  return symbol.trim().toUpperCase().replace(/-USD$/, "");
}

export function isCryptoSymbol(symbol: string): boolean {
  const s = baseCryptoSymbol(symbol);
  return CRYPTO_MAJORS.has(s) || Boolean(COINGECKO_IDS[s]);
}
