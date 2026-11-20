/**
 * US bilateral merchandise trade via UN Comtrade public preview API (no key).
 * Docs: https://comtradeplus.un.org/en/api-docs
 * Values are USD primaryValue (annual HS TOTAL).
 */

export type TradePartner = {
  code: number;
  iso: string;
  short: string;
  name: string;
  exports: number;
  imports: number;
};

const US_REPORTER = 842;

/** Curated bilateral trade partners. */
const PARTNERS: { code: number; iso: string; short: string; name: string }[] = [
  { code: 484, iso: "MEX", short: "Mex.", name: "Mexico" },
  { code: 124, iso: "CAN", short: "Can.", name: "Canada" },
  { code: 156, iso: "CHN", short: "China", name: "China" },
  { code: 410, iso: "KOR", short: "S.K.", name: "South Korea" },
  { code: 392, iso: "JPN", short: "Japan", name: "Japan" },
  { code: 704, iso: "VNM", short: "Viet.", name: "Vietnam" },
  { code: 699, iso: "IND", short: "India", name: "India" },
  { code: 372, iso: "IRL", short: "Ire.", name: "Ireland" },
  { code: 528, iso: "NLD", short: "Neth.", name: "Netherlands" },
  { code: 702, iso: "SGP", short: "Sing.", name: "Singapore" },
  { code: 757, iso: "CHE", short: "Switz.", name: "Switzerland" },
  { code: 276, iso: "DEU", short: "Ger.", name: "Germany" },
  { code: 826, iso: "GBR", short: "UK", name: "United Kingdom" },
];

async function fetchFlow(
  period: string,
  flowCode: "X" | "M",
): Promise<Map<number, number>> {
  const partnerCode = PARTNERS.map((p) => p.code).join(",");
  const url = new URL(
    `https://comtradeapi.un.org/public/v1/preview/C/A/HS`,
  );
  url.searchParams.set("reporterCode", String(US_REPORTER));
  url.searchParams.set("period", period);
  url.searchParams.set("partnerCode", partnerCode);
  url.searchParams.set("cmdCode", "TOTAL");
  url.searchParams.set("flowCode", flowCode);

  const res = await fetch(url.toString(), {
    headers: { Accept: "application/json" },
    next: { revalidate: 86_400 },
  });
  if (!res.ok) {
    throw new Error(`Comtrade ${res.status}: ${await res.text()}`);
  }
  const body = (await res.json()) as {
    error?: string;
    data?: { partnerCode?: number; primaryValue?: number }[];
  };
  if (body.error) throw new Error(`Comtrade: ${body.error}`);
  const map = new Map<number, number>();
  for (const row of body.data || []) {
    const code = Number(row.partnerCode);
    const val = Number(row.primaryValue);
    if (Number.isFinite(code) && Number.isFinite(val)) map.set(code, val);
  }
  return map;
}

export async function fetchUsTradePartners(
  period = "2024",
): Promise<{ period: string; partners: TradePartner[]; source: string }> {
  let year = period;
  let exportsMap: Map<number, number>;
  let importsMap: Map<number, number>;
  try {
    [exportsMap, importsMap] = await Promise.all([
      fetchFlow(year, "X"),
      fetchFlow(year, "M"),
    ]);
    if (!exportsMap.size && !importsMap.size) throw new Error("empty");
  } catch {
    year = "2023";
    [exportsMap, importsMap] = await Promise.all([
      fetchFlow(year, "X"),
      fetchFlow(year, "M"),
    ]);
  }

  const partners: TradePartner[] = PARTNERS.map((p) => ({
    ...p,
    exports: exportsMap.get(p.code) ?? 0,
    imports: importsMap.get(p.code) ?? 0,
  }))
    .filter((p) => p.exports > 0 || p.imports > 0)
    .sort((a, b) => b.exports + b.imports - (a.exports + a.imports));

  if (!partners.length) {
    throw new Error("No Comtrade partner rows for US");
  }

  return {
    period: year,
    partners,
    source: "UN Comtrade public preview (HS TOTAL, annual, reporter=USA)",
  };
}
