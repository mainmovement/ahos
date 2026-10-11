/**
 * M-D5.5 idea-shelf selftest — the upgrade rule, as an assertion.
 *
 * Run: npm run test:idea-shelf
 *
 * `awaitingUpgrade` and `parseShelf` are pure functions of plain inputs, so the
 * whole rule can be asserted on a machine with no shelf file and no GPU — which
 * is the point, because the shelf does not exist yet (M59.S has not shipped) and
 * the rule still has to be right before the first registry arrives.
 *
 * What this proves is the negative that matters: that a missing or unreadable
 * registry can never become an empty list of ideas, and that an idea with an
 * unknown tier tag can never be classified as runnable or as blocked.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  awaitingUpgrade,
  hardwareOrdinal,
  parseShelf,
  ramGuardState,
  type ShelfIdea,
} from "../components/shelf/ideaShelf.ts";

const IDEA = (over: Partial<ShelfIdea>): ShelfIdea => ({
  id: "x",
  title: "x",
  tier: null,
  ...over,
});

describe("M-D5.5: a missing registry is UNKNOWN, not an empty shelf", () => {
  it("reports a missing file as UNAVAILABLE, never as zero ideas", () => {
    assert.equal(parseShelf(null).status, "UNAVAILABLE");
    assert.equal(parseShelf(undefined).status, "UNAVAILABLE");
    assert.equal(parseShelf("").status, "UNAVAILABLE");
  });

  it("reports an unparseable or misshapen file as UNAVAILABLE", () => {
    assert.equal(parseShelf("{not json").status, "UNAVAILABLE");
    assert.equal(parseShelf("null").status, "UNAVAILABLE");
    assert.equal(parseShelf("[]").status, "UNAVAILABLE");
    assert.equal(parseShelf('{"ideas": 5}').status, "UNAVAILABLE");
  });

  it("carries a reason, so the panel can say what kind of missing it was", () => {
    const missing = parseShelf(null);
    assert.equal(missing.status, "UNAVAILABLE");
    if (missing.status !== "UNAVAILABLE") return;
    assert.equal(missing.reason, "missing");
    const shaped = parseShelf('{"ideas": 5}');
    assert.equal(shaped.status, "UNAVAILABLE");
    if (shaped.status !== "UNAVAILABLE") return;
    assert.equal(shaped.reason, "no ideas array");
  });

  it("parses a well-formed registry", () => {
    const parsed = parseShelf(JSON.stringify({
      ideas: [
        { id: "laya", title: "Laya", tier: "T16", est_ram_mb: 900, core: true, priority: 3 },
        { id: "ocr", title: "light-ocr", tier: "T8" },
      ],
    }));
    assert.equal(parsed.status, "OK");
    if (parsed.status !== "OK") return;
    assert.equal(parsed.ideas.length, 2);
    assert.equal(parsed.ideas[0].tier, "T16");
    assert.equal(parsed.ideas[1].core, undefined);
  });

  it("drops an entry with no id or no title rather than guessing a name", () => {
    const parsed = parseShelf(JSON.stringify({
      ideas: [{ id: "a", tier: "T8" }, { title: "no id", tier: "T8" }, { id: "ok", title: "Ok", tier: "T8" }],
    }));
    if (parsed.status !== "OK") throw new Error("expected OK");
    assert.equal(parsed.ideas.length, 1);
    assert.equal(parsed.ideas[0].id, "ok");
  });

  it("deduplicates by id, keeping the first", () => {
    const parsed = parseShelf(JSON.stringify({
      ideas: [
        { id: "dup", title: "first", tier: "T8" },
        { id: "dup", title: "second", tier: "GPU" },
      ],
    }));
    if (parsed.status !== "OK") throw new Error("expected OK");
    assert.equal(parsed.ideas.length, 1);
    assert.equal(parsed.ideas[0].title, "first");
  });

  it("keeps an unrecognised tier tag as null, never as a low requirement", () => {
    const parsed = parseShelf(JSON.stringify({
      ideas: [{ id: "future", title: "Future", tier: "T64" }],
    }));
    if (parsed.status !== "OK") throw new Error("expected OK");
    assert.equal(parsed.ideas[0].tier, null);
  });
});

describe("M-D5.5: the ladder order", () => {
  it("ranks T8 below T16 below T32 below GPU", () => {
    assert.equal(hardwareOrdinal("T8"), 0);
    assert.equal(hardwareOrdinal("T16"), 1);
    assert.equal(hardwareOrdinal("T32"), 2);
    assert.equal(hardwareOrdinal("GPU"), 3);
  });

  it("is null for an unknown tier", () => {
    assert.equal(hardwareOrdinal(null), null);
  });
});

describe("M-D5.5: awaitingUpgrade lists only what the machine cannot run", () => {
  const SHELF: ShelfIdea[] = [
    IDEA({ id: "cheap", title: "Cheap", tier: "T8" }),
    IDEA({ id: "mid", title: "Mid", tier: "T16" }),
    IDEA({ id: "big", title: "Big", tier: "T32" }),
    IDEA({ id: "huge", title: "Huge", tier: "GPU" }),
  ];

  it("lists nothing above a GPU machine", () => {
    assert.equal(awaitingUpgrade(SHELF, "GPU").length, 0);
  });

  it("lists exactly the ideas above a T8 machine, highest requirement first", () => {
    assert.deepEqual(
      awaitingUpgrade(SHELF, "T8").map((i) => i.id),
      ["huge", "big", "mid"],
    );
  });

  it("lists only GPU above a T32 machine", () => {
    assert.deepEqual(
      awaitingUpgrade(SHELF, "T32").map((i) => i.id),
      ["huge"],
    );
  });

  it("lists nothing for an idea at or below the machine's tier", () => {
    assert.deepEqual(awaitingUpgrade(SHELF, "T16").map((i) => i.id), ["huge", "big"]);
  });

  it("lists nothing when the machine's own tier is unknown", () => {
    // The machine being unknown is not 'everything is waiting' and it is not
    // 'nothing is waiting' — the panel says the tier is unknown instead.
    assert.equal(awaitingUpgrade(SHELF, null).length, 0);
  });

  it("excludes an idea whose tier tag the registry did not specify", () => {
    // Such an idea is neither runnable nor blocked; listing it as awaiting would
    // claim a requirement the registry never recorded.
    const shelf = [IDEA({ id: "mystery", title: "Mystery", tier: null })];
    assert.equal(awaitingUpgrade(shelf, "T8").length, 0);
    assert.equal(awaitingUpgrade(shelf, "GPU").length, 0);
  });

  it("orders equal requirements by M59.S priority, higher first", () => {
    const shelf = [
      IDEA({ id: "low", title: "Low", tier: "T16", priority: 1 }),
      IDEA({ id: "high", title: "High", tier: "T16", priority: 9 }),
    ];
    assert.deepEqual(
      awaitingUpgrade(shelf, "T8").map((i) => i.id),
      ["high", "low"],
    );
  });

  it("works on an empty shelf without inventing ideas", () => {
    assert.equal(awaitingUpgrade([], "T8").length, 0);
  });
});

describe("M-D5.5: the RAM-guard line", () => {
  it("flags a value under the floor", () => {
    assert.equal(ramGuardState(4).state, "UNDER_FLOOR");
  });

  it("names the floor exactly, without demoting", () => {
    // This machine reports 8 GB: at the floor, which is the spec's baseline, not
    // a violation of it.
    assert.equal(ramGuardState(8).state, "AT_FLOOR");
  });

  it("names a value above the floor", () => {
    assert.equal(ramGuardState(16).state, "ABOVE_FLOOR");
  });

  it("is UNKNOWN when the browser will not say", () => {
    // navigator.deviceMemory is coarse and often withheld; an unreadable value
    // is not 'under the floor' — that would turn a gap into a measurement.
    assert.equal(ramGuardState(null).state, "UNKNOWN");
  });

  it("says it in Persian", () => {
    for (const v of [null, 4, 8, 16] as const) {
      assert.ok(ramGuardState(v).fa, "the RAM line must have Persian text");
    }
  });
});
