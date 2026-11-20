/** Black-Scholes pricing + Greeks (port of metrics/options_metrics.py). */

function cdf(x: number): number {
  return 0.5 * (1 + erf(x / Math.SQRT2));
}

function pdf(x: number): number {
  return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
}

function erf(x: number): number {
  // Abramowitz and Stegun approximation
  const sign = x < 0 ? -1 : 1;
  const ax = Math.abs(x);
  const a1 = 0.254829592;
  const a2 = -0.284496736;
  const a3 = 1.421413741;
  const a4 = -1.453152027;
  const a5 = 1.061405429;
  const p = 0.3275911;
  const t = 1 / (1 + p * ax);
  const y = 1 - (((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t) * Math.exp(-ax * ax);
  return sign * y;
}

export function blackScholes(
  S: number,
  K: number,
  T: number,
  r: number,
  sigma: number,
  optionType: "call" | "put" = "call",
) {
  if (T <= 0) {
    const intrinsic = optionType === "call" ? Math.max(0, S - K) : Math.max(0, K - S);
    return {
      price: intrinsic,
      delta: optionType === "call" ? (S > K ? 1 : 0) : S < K ? -1 : 0,
      gamma: 0,
      theta: 0,
      vega: 0,
      rho: 0,
    };
  }

  const d1 = (Math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * Math.sqrt(T));
  const d2 = d1 - sigma * Math.sqrt(T);

  const price =
    optionType === "call"
      ? S * cdf(d1) - K * Math.exp(-r * T) * cdf(d2)
      : K * Math.exp(-r * T) * cdf(-d2) - S * cdf(-d1);

  const delta = optionType === "call" ? cdf(d1) : cdf(d1) - 1;
  const gamma = pdf(d1) / (S * sigma * Math.sqrt(T));
  const vega = (S * pdf(d1) * Math.sqrt(T)) / 100;
  const term1 = -(S * pdf(d1) * sigma) / (2 * Math.sqrt(T));
  const theta =
    (optionType === "call"
      ? term1 - r * K * Math.exp(-r * T) * cdf(d2)
      : term1 + r * K * Math.exp(-r * T) * cdf(-d2)) / 365;
  const rho =
    ((optionType === "call"
      ? K * T * Math.exp(-r * T) * cdf(d2)
      : -K * T * Math.exp(-r * T) * cdf(-d2)) /
      100);

  return { price, delta, gamma, theta, vega, rho };
}

export function formatPricerResults(
  spot: number,
  strike: number,
  dteDays: number,
  iv: number,
  optionType: "call" | "put",
  r = 0.02,
): string {
  const g = blackScholes(spot, strike, dteDays / 365, r, iv, optionType);
  return [
    `THEORETICAL PRICE: $${g.price.toFixed(2)}`,
    "",
    "GREEKS:",
    `Delta: ${g.delta.toFixed(4)}`,
    `Gamma: ${g.gamma.toFixed(6)}`,
    `Vega: ${g.vega.toFixed(2)}`,
    `Theta: ${g.theta.toFixed(2)} (per day)`,
    "",
    "INPUTS:",
    `Underlying: $${spot.toLocaleString()}`,
    `Strike: $${strike.toLocaleString()}`,
    `DTE: ${Math.round(dteDays)} days`,
    `IV: ${(iv * 100).toFixed(1)}%`,
    `Type: ${optionType.toUpperCase()}`,
  ].join("\n");
}
