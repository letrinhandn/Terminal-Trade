import { NextRequest, NextResponse } from "next/server";

/**
 * CoinDesk Data API historical options - optional / deferred.
 * Free / Personal access ended 2026-05-21; accounts without a paid
 * subscription cannot use the Data API. Contact CoinDesk Data Sales
 * for pricing + redistribution rights before enabling for customers.
 */
export async function GET(req: NextRequest) {
  const key = process.env.COINDESK_API_KEY;
  const currency = req.nextUrl.searchParams.get("currency") || "BTC";

  if (!key) {
    return NextResponse.json(
      {
        configured: false,
        currency,
        error:
          "CoinDesk Data API not configured (paid subscription required since 2026-05-21)",
        guidance:
          "Terminal Trade uses CoinGecko (quotes) + Coinbase Exchange (candles) for free prototype crypto. Enable CoinDesk later only with a quoted plan that covers display and/or API redistribution.",
        sales: "https://data.coindesk.com/",
      },
      { status: 503 },
    );
  }

  return NextResponse.json({
    configured: true,
    currency,
    message:
      "CoinDesk key present - historical options surface adapter not implemented yet; confirm commercial/redistribution rights with CoinDesk Data Sales before shipping.",
    contracts: [],
  });
}
