// FILE: 13_missions_batch3/tests/contract.test.ts
import { afterEach, describe, expect, it, vi } from "vitest";
import { validateContract, validateNewsCenter, validateScienceRadar, validateSkillMarket } from "@/contract/validate";
import { getSnapshot as getRadar } from "@/adapters/science-radar";
import { unavailableNewsCenter, unavailableScienceRadar } from "@/contract/unavailable";
import { cloneExample, loadExample, mockFetch, mockFetchFails } from "./helpers";

afterEach(() => {
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
});

describe("contract validator", () => {
  it("accepts the shipped example contract", () => {
    const doc = validateContract(loadExample());
    expect(doc).not.toBeNull();
    expect(doc!.contractVersion).toBe("ahos-arena-1");
    expect(doc!.scienceRadar.items.length).toBeGreaterThan(0);
    expect(doc!.newsCenter.items.length).toBeGreaterThan(0);
  });

  it("rejects malformed input as null (⇒ UNAVAILABLE), never throws", () => {
    expect(validateContract(null)).toBeNull();
    expect(validateContract("x")).toBeNull();
    expect(validateContract({})).toBeNull();
    const badEnum = cloneExample();
    ((badEnum.scienceRadar as Record<string, unknown>).items as Array<Record<string, unknown>>)[0].sourceType =
      "youtube";
    expect(validateContract(badEnum)).toBeNull();
    const badSection = cloneExample();
    delete badSection.weeklyExam;
    expect(validateContract(badSection)).toBeNull();
    const badRealTrading = cloneExample();
    badRealTrading.realTrading = "yes";
    expect(validateContract(badRealTrading)).toBeNull();
  });

  it("rejects records with missing required fields", () => {
    const root = loadExample();
    const missingId = cloneExample();
    const items = (missingId.scienceRadar as Record<string, unknown>).items as Array<Record<string, unknown>>;
    delete items[0].id;
    expect(validateScienceRadar(missingId.scienceRadar, root)).toBeNull();

    const badNews = cloneExample();
    const news = (badNews.newsCenter as Record<string, unknown>).items as Array<Record<string, unknown>>;
    news[0].summary = "x".repeat(121);
    expect(validateNewsCenter(badNews.newsCenter, root)).toBeNull();

    const badSkill = cloneExample();
    const entries = (badSkill.skillMarket as Record<string, unknown>).entries as Array<Record<string, unknown>>;
    entries[0].permissions = "not-an-array";
    expect(validateSkillMarket(badSkill.skillMarket, root)).toBeNull();
  });

  it("error → UNAVAILABLE snapshots have no fabricated rows", () => {
    const u = unavailableScienceRadar();
    expect(u.items).toEqual([]);
    expect(u.source).toBeNull();
    expect(u.generatedAt).toBeNull();
    expect(unavailableNewsCenter().items).toEqual([]);
  });
});

describe("adapters (error → UNAVAILABLE)", () => {
  it("returns a valid snapshot from the contract", async () => {
    mockFetch(loadExample());
    const snap = await getRadar();
    expect(snap.kind).toBe("scienceRadar");
    expect(snap.items.length).toBeGreaterThan(0);
  });

  it("returns UNAVAILABLE on network failure (without ?demo=1)", async () => {
    window.history.replaceState({}, "", "/arena/science-radar");
    mockFetchFails();
    const snap = await getRadar();
    expect(snap.items).toEqual([]);
    expect(snap.source).toBeNull();
    expect(snap.generatedAt).toBeNull();
  });

  it("returns UNAVAILABLE on malformed payload (without ?demo=1)", async () => {
    window.history.replaceState({}, "", "/arena/science-radar");
    mockFetch({ nonsense: true });
    const snap = await getRadar();
    expect(snap.items).toEqual([]);
    expect(snap.executionMode).toBe("UNKNOWN");
  });
});
