import { NextResponse } from "next/server";
import { db } from "@/db";
import { paperTrades, tokens, learningLogs } from "@/db/schema";
import { desc, eq } from "drizzle-orm";

export async function GET() {
  try {
    const trades = await db.select().from(paperTrades).orderBy(desc(paperTrades.createdAt));
    
    // Calculate Stats
    let totalPnlUsd = 0;
    let totalWins = 0;
    let totalLosses = 0;

    trades.forEach((t) => {
      totalPnlUsd += parseFloat(t.pnlUsd || "0");
      if (t.status === "CLOSED_WIN") totalWins++;
      if (t.status === "CLOSED_LOSS") totalLosses++;
    });

    const winRate = totalWins + totalLosses > 0 ? ((totalWins / (totalWins + totalLosses)) * 100).toFixed(1) : "100.0";

    return NextResponse.json({
      success: true,
      trades,
      stats: {
        totalPnlUsd: totalPnlUsd.toFixed(2),
        winRate: `${winRate}%`,
        activeTradesCount: trades.filter((t) => t.status === "OPEN").length,
        closedTradesCount: trades.filter((t) => t.status !== "OPEN").length,
      },
    });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { tokenId, symbol, entryPrice, stopLoss, targetPrice, virtualCapital = "100" } = body;

    const size = (parseFloat(virtualCapital) / parseFloat(entryPrice)).toFixed(2);

    const [newTrade] = await db
      .insert(paperTrades)
      .values({
        tokenId,
        symbol,
        type: "BUY",
        entryPrice: entryPrice.toString(),
        currentPrice: entryPrice.toString(),
        stopLoss: stopLoss.toString(),
        targetPrice: targetPrice.toString(),
        virtualCapital: virtualCapital.toString(),
        positionSize: size,
        pnlUsd: "0.00",
        pnlPercent: "0.00",
        status: "OPEN",
        postMortem: `Paper trade initialized. Stop Loss: $${stopLoss}, Target: $${targetPrice}. R:R = ${(
          (parseFloat(targetPrice) - parseFloat(entryPrice)) /
          (parseFloat(entryPrice) - parseFloat(stopLoss))
        ).toFixed(2)}`,
      })
      .returning();

    return NextResponse.json({ success: true, trade: newTrade });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const body = await request.json();
    const { id, exitPrice, status, postMortem } = body;

    const tradeList = await db.select().from(paperTrades).where(eq(paperTrades.id, id)).limit(1);
    if (tradeList.length === 0) {
      return NextResponse.json({ success: false, error: "Trade not found" }, { status: 404 });
    }

    const trade = tradeList[0];
    const entry = parseFloat(trade.entryPrice);
    const exit = parseFloat(exitPrice);
    const capital = parseFloat(trade.virtualCapital);
    const pnlUsdVal = (capital * (exit - entry) / entry);
    const pnlPctVal = ((exit - entry) / entry) * 100;

    const isWin = pnlPctVal >= 0;
    const finalStatus = status || (isWin ? "CLOSED_WIN" : "CLOSED_LOSS");

    const [updated] = await db
      .update(paperTrades)
      .set({
        exitPrice: exitPrice.toString(),
        currentPrice: exitPrice.toString(),
        pnlUsd: pnlUsdVal.toFixed(2),
        pnlPercent: pnlPctVal.toFixed(2),
        status: finalStatus,
        postMortem: postMortem || (isWin ? "Target achieved. Success pattern confirmed." : "Stop loss triggered. Failure pattern logged."),
        closedAt: new Date(),
      })
      .where(eq(paperTrades.id, id))
      .returning();

    // Log to Tree of Wisdom Learning Engine
    await db.insert(learningLogs).values({
      eventType: isWin ? "WIN_PATTERN" : "FAILURE_PATTERN",
      title: `${trade.symbol} Paper Trade Post-Mortem: ${isWin ? "WIN +" + pnlPctVal.toFixed(1) + "%" : "LOSS " + pnlPctVal.toFixed(1) + "%"}`,
      description: postMortem || `Trade closed at $${exitPrice}. PnL: ${pnlPctVal.toFixed(2)}%.`,
      impact: isWin ? "Positive pattern weight boosted in scoring matrix." : "Risk threshold tightened in Red Team gate.",
      treeLayer: isWin ? "BRANCHES" : "ROOTS",
    });

    return NextResponse.json({ success: true, trade: updated });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
