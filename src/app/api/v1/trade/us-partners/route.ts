import { cached } from "@/lib/platform/cache";
import { fail, ok } from "@/lib/platform/json";
import { runProvider } from "@/lib/platform/run";
import { fetchUsTradePartners } from "@/lib/data/comtrade";

export const maxDuration = 60;

/** Real US bilateral trade partners (UN Comtrade public API). */
export async function GET() {
  try {
    const data = await cached("comtrade:us:partners:2024", 86_400_000, () =>
      fetchUsTradePartners("2024"),
    );
    return ok(
      await runProvider("internal", async () => data, [
        "Exports = flow X / Imports = flow M / USD primaryValue",
      ]),
    );
  } catch (e) {
    return fail(e);
  }
}
