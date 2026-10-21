import type { NewsroomAdapter, NewsroomRequest } from "@/src/mock/newsroom/adapters";
import type { NewsroomSnapshot } from "./types";

export const soakNewsroomAdapter: NewsroomAdapter = {
  id: "soak:M13_SOAK/witness",
  kind: "http",

  async load(request: NewsroomRequest = {}): Promise<NewsroomSnapshot> {
    const res = await fetch("/api/newsroom/snapshot", { signal: request.signal, cache: "no-store" });
    if (!res.ok) throw new Error("M13 witness newsroom unavailable");
    const body = (await res.json()) as { ok?: boolean; snapshot?: NewsroomSnapshot };
    if (!body.ok || !body.snapshot) throw new Error("empty soak newsroom");
    return body.snapshot;
  },
};
