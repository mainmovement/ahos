"use client";

import { useMemo, useState, type ReactNode } from "react";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Columns3,
  Download,
  SearchX,
  Table2,
} from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { Panel } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { StatusBadge } from "@/components/status/status-badge";
import { SignalBadge } from "@/components/status/signal-badge";
import { ProvenancePanel } from "@/components/status/provenance-panel";
import { EmptyState } from "@/components/status/empty-state";
import { POSITIONS, tradesForPosition } from "@/lib/data/positions";
import { DATASET } from "@/lib/data/config";
import { csvWithBom, toCsv } from "@/lib/formatters/csv";
import {
  formatLeverage,
  formatNumber,
  formatSignedUsd,
  localizeDigits,
} from "@/lib/formatters/numbers";
import { formatDateTime } from "@/lib/formatters/dates";
import type { DataStatus, DeskId, Position, PositionState, Side } from "@/lib/types";
import { cn } from "@/lib/utils";

type SortKey = "symbol" | "deskId" | "side" | "entry" | "mark" | "gross" | "fees" | "funding" | "net" | "state";

const PAGE_SIZE = 10;

export function PositionsTable() {
  const { dict, locale } = useLocale();
  const [search, setSearch] = useState("");
  const [desk, setDesk] = useState<"all" | DeskId>("all");
  const [side, setSide] = useState<"all" | Side>("all");
  const [state, setState] = useState<"all" | PositionState>("all");
  const [prov, setProv] = useState<"all" | DataStatus>("all");
  const [sortKey, setSortKey] = useState<SortKey>("symbol");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);
  const [hiddenCols, setHiddenCols] = useState<Set<string>>(new Set());
  const [drawerId, setDrawerId] = useState<string | null>(null);
  const isRtl = locale === "fa";

  const desks: DeskId[] = ["gold", "oil", "crypto", "onchain", "exchanges", "tokens", "stocks"];
  const provOptions: DataStatus[] = ["SAMPLE", "STALE", "UNVERIFIED", "QUARANTINED"];

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return POSITIONS.filter((p) => {
      if (desk !== "all" && p.deskId !== desk) return false;
      if (side !== "all" && p.side !== side) return false;
      if (state !== "all" && p.state !== state) return false;
      if (prov !== "all" && p.provenance.status !== prov) return false;
      if (q) {
        const hay = `${p.symbol} ${p.id} ${p.deskId}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [search, desk, side, state, prov]);

  const sorted = useMemo(() => {
    const dir = sortDir === "asc" ? 1 : -1;
    const value = (p: Position): number | string => {
      switch (sortKey) {
        case "symbol": return p.symbol;
        case "deskId": return p.deskId;
        case "side": return p.side;
        case "entry": return p.entry;
        case "mark": return p.mark;
        case "gross": return p.pnl.gross;
        case "fees": return p.pnl.fees ?? Number.NEGATIVE_INFINITY;
        case "funding": return p.pnl.funding ?? Number.NEGATIVE_INFINITY;
        case "net": return p.pnl.net ?? Number.NEGATIVE_INFINITY;
        case "state": return p.state;
        default: return p.id;
      }
    };
    return [...filtered].sort((a, b) => {
      const va = value(a);
      const vb = value(b);
      if (typeof va === "string" && typeof vb === "string") return va.localeCompare(vb) * dir;
      return ((va as number) - (vb as number)) * dir;
    });
  }, [filtered, sortKey, sortDir]);

  const pageCount = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const rows = sorted.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const visible = (id: string) => !hiddenCols.has(id);
  const toggleCol = (id: string) => {
    setHiddenCols((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const exportCsv = () => {
    const header = ["id", "symbol", "desk", "side", "leverage", "entry", "mark", "qty", "gross", "fees", "funding", "net", "state", "provenance", "observed_at_utc"];
    const body = sorted.map((p) => [
      p.id,
      p.symbol,
      p.deskId,
      p.side,
      p.leverage,
      p.entry,
      p.mark,
      p.qty,
      p.pnl.gross,
      p.pnl.fees,
      p.pnl.funding,
      p.pnl.net,
      p.state,
      p.provenance.status,
      p.provenance.observedAt,
    ]);
    const meta = [
      ["# AHOS Intelligence Command Deck — PAPER-ONLY SAMPLE EXPORT. Not real trading data."],
      ["# dataset", DATASET.id, "as_of", DATASET.asOf],
    ];
    const csv = toCsv([...meta, header, ...body] as Array<ReadonlyArray<string | number | null>>);
    const blob = new Blob([csvWithBom(csv)], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ahos-paper-positions-${DATASET.id}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearFilters = () => {
    setSearch("");
    setDesk("all");
    setSide("all");
    setState("all");
    setProv("all");
    setPage(1);
  };

  const ariaSortFor = (key: SortKey): "ascending" | "descending" | "none" =>
    sortKey === key ? (sortDir === "asc" ? "ascending" : "descending") : "none";

  const drawerPosition = drawerId ? POSITIONS.find((p) => p.id === drawerId) ?? null : null;

  return (
    <div className="flex flex-col gap-4">
      {/* toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-52 flex-1 sm:max-w-72">
          <Input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder={dict.positions.searchPlaceholder}
            aria-label={dict.positions.searchPlaceholder}
            className="h-9 pe-3"
          />
        </div>

        <Select value={desk} onValueChange={(v) => { setDesk(v as typeof desk); setPage(1); }}>
          <SelectTrigger className="h-9 w-32" aria-label={dict.positions.deskFilter}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{dict.common.all}</SelectItem>
            {desks.map((d) => (
              <SelectItem key={d} value={d}>
                {d}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={side} onValueChange={(v) => { setSide(v as typeof side); setPage(1); }}>
          <SelectTrigger className="h-9 w-28" aria-label={dict.positions.sideFilter}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{dict.common.all}</SelectItem>
            <SelectItem value="LONG">{dict.positions.long}</SelectItem>
            <SelectItem value="SHORT">{dict.positions.short}</SelectItem>
          </SelectContent>
        </Select>

        <Select value={state} onValueChange={(v) => { setState(v as typeof state); setPage(1); }}>
          <SelectTrigger className="h-9 w-28" aria-label={dict.positions.stateFilter}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{dict.common.all}</SelectItem>
            <SelectItem value="OPEN">{dict.positions.open}</SelectItem>
            <SelectItem value="CLOSED">{dict.positions.closed}</SelectItem>
          </SelectContent>
        </Select>

        <Select value={prov} onValueChange={(v) => { setProv(v as typeof prov); setPage(1); }}>
          <SelectTrigger className="h-9 w-36" aria-label={dict.positions.provenanceFilter}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{dict.common.all}</SelectItem>
            {provOptions.map((s) => (
              <SelectItem key={s} value={s}>
                {dict.status[s]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="h-9">
              <Columns3 aria-hidden />
              {dict.positions.columns}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>{dict.positions.columns}</DropdownMenuLabel>
            {[
              ["desk", dict.positions.colDesk],
              ["side", dict.positions.colSide],
              ["leverage", dict.positions.colLeverage],
              ["entry", dict.positions.colEntry],
              ["mark", dict.positions.colMark],
              ["gross", dict.positions.colGross],
              ["fees", dict.positions.colFees],
              ["funding", dict.positions.colFunding],
              ["net", dict.positions.colNet],
              ["state", dict.positions.colStatus],
              ["prov", dict.positions.colProvenance],
            ].map(([id, label]) => (
              <DropdownMenuCheckboxItem
                key={id}
                checked={visible(id)}
                onCheckedChange={() => toggleCol(id)}
                onSelect={(e) => e.preventDefault()}
              >
                {label}
              </DropdownMenuCheckboxItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <Button variant="accent" size="sm" className="h-9" onClick={exportCsv}>
          <Download aria-hidden />
          {dict.common.exportCsv}
        </Button>

        <p aria-live="polite" className="tnum ms-auto text-[11px] text-muted-foreground">
          {localizeDigits(String(sorted.length), locale)} {dict.common.results}
        </p>
      </div>

      <p className="text-[10px] text-muted-foreground">{dict.positions.exportNote}</p>

      {/* table */}
      {rows.length === 0 ? (
        <Panel>
          <EmptyState
            icon={SearchX}
            title={dict.positions.emptyTitle}
            body={dict.positions.emptyBody}
            action={
              <Button variant="outline" size="sm" onClick={clearFilters}>
                {dict.positions.clearFilters}
              </Button>
            }
          />
        </Panel>
      ) : (
        <Panel className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] border-collapse text-xs">
              <caption className="sr-only">{dict.positions.title}</caption>
              <thead className="border-b border-border bg-muted/40">
                <tr>
                  {(
                    [
                      ["symbol", dict.positions.colSymbol, "symbol", ""],
                      visible("desk") ? ["desk", dict.positions.colDesk, "deskId", "hidden md:table-cell"] : null,
                      visible("side") ? ["side", dict.positions.colSide, "side", ""] : null,
                      visible("leverage") ? ["lev", dict.positions.colLeverage, undefined, "hidden lg:table-cell"] : null,
                      visible("entry") ? ["entry", dict.positions.colEntry, "entry", "hidden sm:table-cell"] : null,
                      visible("mark") ? ["mark", dict.positions.colMark, "mark", "hidden sm:table-cell"] : null,
                      visible("gross") ? ["gross", dict.positions.colGross, "gross", ""] : null,
                      visible("fees") ? ["fees", dict.positions.colFees, "fees", "hidden lg:table-cell"] : null,
                      visible("funding") ? ["funding", dict.positions.colFunding, "funding", "hidden lg:table-cell"] : null,
                      visible("net") ? ["net", dict.positions.colNet, "net", ""] : null,
                      visible("state") ? ["state", dict.positions.colStatus, "state", "hidden md:table-cell"] : null,
                      visible("prov") ? ["prov", dict.positions.colProvenance, undefined, ""] : null,
                      ["actions", "", undefined, ""],
                    ].filter(Boolean) as Array<[string, string, SortKey | undefined, string]>
                  ).map(([id, label, sortValue, cls]) => (
                    <th
                      key={id}
                      scope="col"
                      aria-sort={sortValue ? ariaSortFor(sortValue) : undefined}
                      className={cn("whitespace-nowrap px-3 py-2.5 text-start text-[11px] font-bold text-muted-foreground", cls)}
                    >
                      {sortValue ? (
                        <button
                          type="button"
                          onClick={() => toggleSort(sortValue)}
                          className={cn(
                            "inline-flex items-center gap-1 rounded px-1 py-0.5 transition-colors hover:text-foreground",
                            sortKey === sortValue && "text-primary",
                          )}
                        >
                          {label}
                          {sortKey === sortValue ? (
                            sortDir === "asc" ? <ArrowUp className="size-3" aria-hidden /> : <ArrowDown className="size-3" aria-hidden />
                          ) : (
                            <ArrowUpDown className="size-3 opacity-40" aria-hidden />
                          )}
                        </button>
                      ) : (
                        label
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((p) => (
                  <tr
                    key={p.id}
                    className="border-b border-border/50 transition-colors last:border-0 hover:bg-muted/30"
                  >
                    <td className="px-3 py-2.5">
                      <button
                        type="button"
                        onClick={() => setDrawerId(p.id)}
                        className="group flex flex-col items-start gap-0.5 text-start"
                      >
                        <span className="font-mono font-bold text-foreground group-hover:text-primary" dir="ltr">
                          {p.symbol}
                        </span>
                        <span className="tnum font-mono text-[9px] text-subtle" dir="ltr">{p.id}</span>
                      </button>
                    </td>
                    {visible("desk") ? (
                      <td className="hidden px-3 py-2.5 md:table-cell">
                        <Badge variant="muted">{p.deskId}</Badge>
                      </td>
                    ) : null}
                    {visible("side") ? (
                      <td className="px-3 py-2.5">
                        <SignalBadge state={p.side === "LONG" ? "LONG" : "SHORT"} size="sm" />
                      </td>
                    ) : null}
                    {visible("leverage") ? (
                      <td className="tnum hidden px-3 py-2.5 lg:table-cell" dir="ltr">
                        {formatLeverage(p.leverage, "en")}
                      </td>
                    ) : null}
                    {visible("entry") ? (
                      <td className="tnum hidden px-3 py-2.5 text-muted-foreground sm:table-cell" dir="ltr">
                        {formatNumber(p.entry, "en", p.entry < 10 ? 3 : 1)}
                      </td>
                    ) : null}
                    {visible("mark") ? (
                      <td className="tnum hidden px-3 py-2.5 text-muted-foreground sm:table-cell" dir="ltr">
                        {formatNumber(p.mark, "en", p.mark < 10 ? 3 : 1)}
                      </td>
                    ) : null}
                    {visible("gross") ? (
                      <td className={cn("tnum px-3 py-2.5 font-bold", p.pnl.gross >= 0 ? "text-success" : "text-danger")} dir="ltr">
                        {formatSignedUsd(p.pnl.gross, "en")}
                      </td>
                    ) : null}
                    {visible("fees") ? (
                      <td className="tnum hidden px-3 py-2.5 lg:table-cell" dir="ltr">
                        {p.pnl.fees === null ? <StatusBadge status="NOT_MEASURED" size="sm" /> : `-$${formatNumber(p.pnl.fees, "en", 2)}`}
                      </td>
                    ) : null}
                    {visible("funding") ? (
                      <td className="tnum hidden px-3 py-2.5 lg:table-cell" dir="ltr">
                        {p.pnl.funding === null ? <StatusBadge status="NOT_MEASURED" size="sm" /> : formatSignedUsd(p.pnl.funding, "en")}
                      </td>
                    ) : null}
                    {visible("net") ? (
                      <td className={cn("tnum px-3 py-2.5 font-extrabold", p.pnl.net === null ? "text-muted-foreground" : p.pnl.net >= 0 ? "text-success" : "text-danger")} dir="ltr">
                        {p.pnl.net === null ? dict.common.valueMissing : formatSignedUsd(p.pnl.net, "en")}
                      </td>
                    ) : null}
                    {visible("state") ? (
                      <td className="hidden px-3 py-2.5 md:table-cell">
                        <Badge variant={p.state === "OPEN" ? "accent" : "muted"}>{p.state === "OPEN" ? dict.positions.open : dict.positions.closed}</Badge>
                      </td>
                    ) : null}
                    {visible("prov") ? (
                      <td className="px-3 py-2.5">
                        <StatusBadge status={p.provenance.status} size="sm" />
                      </td>
                    ) : null}
                    <td className="px-3 py-2.5 text-end">
                      <Button variant="ghost" size="icon-sm" onClick={() => setDrawerId(p.id)} aria-label={`${dict.positions.detailTitle} ${p.symbol}`}>
                        <ChevronRight className={isRtl ? "rotate-180" : undefined} aria-hidden />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* pagination */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border/70 bg-muted/20 px-4 py-2.5 text-[11px]">
            <p className="tnum text-muted-foreground">
              {dict.common.showing} {localizeDigits(String((safePage - 1) * PAGE_SIZE + 1), locale)}–
              {localizeDigits(String(Math.min(safePage * PAGE_SIZE, sorted.length)), locale)} {dict.common.of}{" "}
              {localizeDigits(String(sorted.length), locale)}
            </p>
            <div className="flex items-center gap-1.5">
              <Button variant="outline" size="icon-sm" disabled={safePage <= 1} onClick={() => setPage((v) => Math.max(1, v - 1))} aria-label={dict.common.prev}>
                <ChevronRight className={isRtl ? "rotate-180" : undefined} aria-hidden />
              </Button>
              <span className="tnum px-1">
                {dict.common.page} {localizeDigits(String(safePage), locale)} {dict.common.of} {localizeDigits(String(pageCount), locale)}
              </span>
              <Button variant="outline" size="icon-sm" disabled={safePage >= pageCount} onClick={() => setPage((v) => Math.min(pageCount, v + 1))} aria-label={dict.common.next}>
                <ChevronLeft className={isRtl ? "rotate-180" : undefined} aria-hidden />
              </Button>
            </div>
          </div>
        </Panel>
      )}

      {/* detail drawer */}
      <Sheet open={drawerId !== null} onOpenChange={(open) => !open && setDrawerId(null)}>
        <SheetContent side="end" className="panel p-0">
          {drawerPosition ? (
            <PositionDrawerContent position={drawerPosition} onClose={() => setDrawerId(null)} />
          ) : null}
        </SheetContent>
      </Sheet>
    </div>
  );
}

function PositionDrawerContent({ position, onClose }: { position: Position; onClose: () => void }) {
  const { dict, locale } = useLocale();
  const trades = tradesForPosition(position.id);
  const { pnl } = position;

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border/70 panel-pad">
        <p className="text-[10px] font-bold uppercase tracking-wider text-subtle" dir="ltr">{position.id}</p>
        <SheetTitle className="mt-0.5 font-mono text-xl font-extrabold" dir="ltr">
          {position.symbol}
        </SheetTitle>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <SignalBadge state={position.side === "LONG" ? "LONG" : "SHORT"} size="sm" />
          <Badge variant={position.state === "OPEN" ? "accent" : "muted"}>
            {position.state === "OPEN" ? dict.positions.open : dict.positions.closed}
          </Badge>
          <StatusBadge status={position.provenance.status} size="sm" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto panel-pad flex flex-col gap-4">
        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-xs">
          <Field label={dict.positions.colDesk} value={<Badge variant="muted">{position.deskId}</Badge>} />
          <Field label={dict.positions.colLeverage} value={<span className="tnum" dir="ltr">{formatLeverage(position.leverage, "en")}</span>} />
          <Field label={dict.positions.colEntry} value={<span className="tnum" dir="ltr">{formatNumber(position.entry, "en", position.entry < 10 ? 4 : 2)}</span>} />
          <Field label={dict.positions.colMark} value={<span className="tnum" dir="ltr">{formatNumber(position.mark, "en", position.mark < 10 ? 4 : 2)}</span>} />
          <Field
            label={dict.common.observedAt}
            value={
              position.provenance.observedAt ? (
                <span className="tnum">{formatDateTime(position.provenance.observedAt, locale)}</span>
              ) : (
                <StatusBadge status="NOT_MEASURED" size="sm" />
              )
            }
          />
          <Field label={dict.positions.colStatus} value={position.state === "OPEN" ? dict.positions.open : dict.positions.closed} />
        </dl>

        {/* accounting */}
        <div className="rounded-xl border border-border/70 bg-muted/20 p-3">
          <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-subtle" dir="ltr">
            {dict.positions.formula}
          </p>
          <dl className="flex flex-col gap-2 text-xs">
            <div className="flex items-center justify-between gap-2">
              <dt className="text-muted-foreground">{dict.positions.colGross}</dt>
              <dd className={cn("tnum font-bold", pnl.gross >= 0 ? "text-success" : "text-danger")} dir="ltr">
                {formatSignedUsd(pnl.gross, "en")}
              </dd>
            </div>
            <div className="flex items-center justify-between gap-2">
              <dt className="text-muted-foreground">{dict.positions.colFees}</dt>
              <dd>
                {pnl.fees === null ? <StatusBadge status="NOT_MEASURED" size="sm" /> : <span className="tnum font-bold text-danger" dir="ltr">-{formatNumber(pnl.fees, "en", 2)}</span>}
              </dd>
            </div>
            <div className="flex items-center justify-between gap-2">
              <dt className="text-muted-foreground">{dict.positions.colFunding}</dt>
              <dd>
                {pnl.funding === null ? <StatusBadge status="NOT_MEASURED" size="sm" /> : <span className="tnum font-bold" dir="ltr">{formatSignedUsd(pnl.funding, "en")}</span>}
              </dd>
            </div>
            <div className="flex items-center justify-between gap-2 border-t border-border/60 pt-2">
              <dt className="font-bold">{dict.positions.colNet}</dt>
              <dd>
                {pnl.net === null ? (
                  <span className="text-[10px] text-warning">{dict.positions.netNotComputable}</span>
                ) : (
                  <span className={cn("tnum text-base font-extrabold", pnl.net >= 0 ? "text-success" : "text-danger")} dir="ltr">
                    {formatSignedUsd(pnl.net, "en")}
                  </span>
                )}
              </dd>
            </div>
          </dl>
          {pnl.fees === null || pnl.funding === null ? (
            <p className="mt-2 flex flex-col gap-0.5 text-[10px] leading-relaxed text-warning">
              {pnl.fees === null ? <span>{dict.positions.missingFees}</span> : null}
              {pnl.funding === null ? <span>{dict.positions.missingFunding}</span> : null}
            </p>
          ) : null}
        </div>

        <ProvenancePanel provenance={position.provenance} title={dict.positions.colProvenance} />

        {/* executions */}
        <div>
          <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-subtle">{dict.positions.executions}</p>
          {trades.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border-strong">
              <EmptyState icon={Table2} title={dict.positions.noExecutions} />
            </div>
          ) : (
            <ul className="flex flex-col gap-2">
              {trades.map((t) => (
                <li key={t.id} className="flex items-center justify-between gap-2 rounded-xl border border-border/60 bg-muted/20 px-3 py-2 text-[11px]">
                  <span className="flex items-center gap-2">
                    <Badge variant={t.kind === "ENTRY" ? "accent" : "muted"}>{t.kind}</Badge>
                    <span className="tnum" dir="ltr">
                      {formatNumber(t.price, "en", t.price < 10 ? 4 : 2)} × {formatNumber(t.qty, "en", 3)}
                    </span>
                  </span>
                  <span className="flex items-center gap-2 text-muted-foreground">
                    <span className="tnum" dir="ltr">
                      {t.fee === null ? <StatusBadge status="NOT_MEASURED" size="sm" /> : `fee ${formatNumber(t.fee, "en", 2)}`}
                    </span>
                    <time className="tnum">{t.at ? formatDateTime(t.at, locale) : "—"}</time>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="border-t border-border/70 panel-pad">
        <Button variant="outline" size="sm" className="w-full" onClick={onClose}>
          {dict.common.close}
        </Button>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-[10px] text-muted-foreground">{label}</dt>
      <dd className="mt-0.5">{value}</dd>
    </div>
  );
}
