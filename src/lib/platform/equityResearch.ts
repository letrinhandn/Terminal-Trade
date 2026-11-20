import { fetchYahooResearchBundle } from "@/lib/data/yahoo";
import { getCompanyBundle, isFinnhubConfigured } from "@/lib/data/finnhub";
import { cached } from "@/lib/platform/cache";
import { runProvider } from "@/lib/platform/run";
import type { PlatformResult } from "@/lib/platform/types";

async function bundle(symbol: string) {
  return cached(`eq:research:${symbol.toUpperCase()}`, 600_000, () =>
    fetchYahooResearchBundle(symbol),
  );
}

function asRows(node: unknown, nestedKey: string): Record<string, unknown>[] {
  if (!node || typeof node !== "object") return [];
  const inner = (node as Record<string, unknown>)[nestedKey];
  return Array.isArray(inner) ? (inner as Record<string, unknown>[]) : [];
}

async function finnhubSafe(symbol: string) {
  if (!isFinnhubConfigured()) return { data: null as unknown, warning: "FINNHUB_API_KEY not set" };
  try {
    const data = await cached(`eq:fh:${symbol.toUpperCase()}`, 600_000, () =>
      getCompanyBundle(symbol),
    );
    return { data, warning: null as string | null };
  } catch (e) {
    return {
      data: null as unknown,
      warning: e instanceof Error ? e.message : String(e),
    };
  }
}

export async function equityFundamentals(
  symbol: string,
  period: "annual" | "quarterly" = "annual",
): Promise<PlatformResult<Record<string, unknown>>> {
  return runProvider("yahoo", async () => {
    const { raw } = await bundle(symbol);
    const incomeKey =
      period === "annual"
        ? "incomeStatementHistory"
        : "incomeStatementHistoryQuarterly";
    const balanceKey =
      period === "annual"
        ? "balanceSheetHistory"
        : "balanceSheetHistoryQuarterly";
    const cashKey =
      period === "annual"
        ? "cashflowStatementHistory"
        : "cashflowStatementHistoryQuarterly";
    return {
      symbol: symbol.toUpperCase(),
      period,
      income: asRows(raw[incomeKey], "incomeStatementHistory"),
      balance: asRows(raw[balanceKey], "balanceSheetStatements"),
      cashflow: asRows(raw[cashKey], "cashflowStatements"),
      financialData: raw.financialData ?? null,
    };
  });
}

export async function equityEarnings(
  symbol: string,
): Promise<PlatformResult<Record<string, unknown>>> {
  const warnings: string[] = [];
  const { raw } = await bundle(symbol);
  const fh = await finnhubSafe(symbol);
  if (fh.warning) warnings.push(fh.warning);
  const fhData = fh.data as {
    earnings?: unknown;
    recommendations?: unknown;
    price_targets?: unknown;
    upgrades?: unknown;
  } | null;
  return runProvider(
    fhData ? "finnhub" : "yahoo",
    async () => ({
      symbol: symbol.toUpperCase(),
      earnings: raw.earnings ?? null,
      earningsHistory: raw.earningsHistory ?? null,
      earningsTrend: raw.earningsTrend ?? null,
      recommendationTrend: raw.recommendationTrend ?? null,
      upgradeDowngradeHistory: raw.upgradeDowngradeHistory ?? null,
      finnhub: fhData
        ? {
            earnings: fhData.earnings,
            recommendations: fhData.recommendations,
            price_targets: fhData.price_targets,
            upgrades: fhData.upgrades,
          }
        : null,
    }),
    warnings,
  );
}

export async function equityCalendar(
  symbol: string,
): Promise<PlatformResult<Record<string, unknown>>> {
  return runProvider("yahoo", async () => {
    const { raw } = await bundle(symbol);
    return {
      symbol: symbol.toUpperCase(),
      calendarEvents: raw.calendarEvents ?? null,
      earnings: raw.earnings ?? null,
    };
  });
}

export async function equityOwnership(
  symbol: string,
): Promise<PlatformResult<Record<string, unknown>>> {
  const warnings: string[] = [];
  const { raw } = await bundle(symbol);
  const fh = await finnhubSafe(symbol);
  if (fh.warning) warnings.push(fh.warning);
  const fhData = fh.data as { insider?: unknown; peers?: unknown } | null;
  return runProvider(
    fhData ? "finnhub" : "yahoo",
    async () => ({
      symbol: symbol.toUpperCase(),
      majorHoldersBreakdown: raw.majorHoldersBreakdown ?? null,
      institutionOwnership: raw.institutionOwnership ?? null,
      fundOwnership: raw.fundOwnership ?? null,
      insiderHolders: raw.insiderHolders ?? null,
      insiderTransactions: raw.insiderTransactions ?? null,
      defaultKeyStatistics: raw.defaultKeyStatistics ?? null,
      finnhub: fhData
        ? { insider: fhData.insider, peers: fhData.peers }
        : null,
    }),
    warnings,
  );
}

export async function equityEsg(
  symbol: string,
): Promise<PlatformResult<Record<string, unknown>>> {
  return runProvider("yahoo", async () => {
    const { raw } = await bundle(symbol);
    // yahoo-finance2 v4 dropped esgScores module - surface governance/company
    // profile fields + SEC filings as the ESG/governance desk.
    return {
      symbol: symbol.toUpperCase(),
      note: "Yahoo quoteSummary no longer ships esgScores; showing asset/governance proxies + SEC filings.",
      assetProfile: raw.assetProfile ?? null,
      summaryProfile: raw.summaryProfile ?? null,
      netSharePurchaseActivity: raw.netSharePurchaseActivity ?? null,
      secFilings: raw.secFilings ?? null,
      keyStats: raw.defaultKeyStatistics ?? null,
    };
  });
}

export async function equityOverviewWidgets(symbol: string) {
  return runProvider("yahoo", async () => {
    const { raw } = await bundle(symbol);
    return {
      symbol: symbol.toUpperCase(),
      profile: raw.summaryProfile ?? null,
      summaryDetail: raw.summaryDetail ?? null,
      keyStats: raw.defaultKeyStatistics ?? null,
      financialData: raw.financialData ?? null,
      recommendationTrend: raw.recommendationTrend ?? null,
      calendarEvents: raw.calendarEvents ?? null,
      assetProfile: raw.assetProfile ?? null,
      secFilings: raw.secFilings ?? null,
      netSharePurchaseActivity: raw.netSharePurchaseActivity ?? null,
    };
  });
}
