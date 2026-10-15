import { getKpis } from "@/lib/api/dashboard";
import { getEarth } from "@/lib/api/org";
import { getMarketBoard } from "@/lib/api/markets";
import { getPaperAccount, getPaperIntraday } from "@/lib/api/paper";
import { getNewsroom } from "@/lib/api/news";
import { getUniversity } from "@/lib/api/university";
import { getSystem } from "@/lib/api/system";
import { CommandCenterView } from "@/components/views/command-center";

export default async function CommandCenterPage() {
  const [kpis, earth, market, paper, intraday, news, university, system] = await Promise.all([
    getKpis(),
    getEarth(),
    getMarketBoard(),
    getPaperAccount(),
    getPaperIntraday(),
    getNewsroom(),
    getUniversity(),
    getSystem(),
  ]);
  // Ship only the candles the overview chart needs (keeps the RSC payload lean).
  const chartIds = ["btc", "xau", "brent", "spx", "eth"];
  const slim = { ...market, data: { ...market.data, candles: Object.fromEntries(chartIds.map((id) => [id, market.data.candles[id] ?? []])) } };
  return <CommandCenterView kpis={kpis} earth={earth} market={slim} paper={paper} intraday={intraday} news={news} university={university} system={system} />;
}
