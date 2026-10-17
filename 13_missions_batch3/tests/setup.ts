// FILE: 13_missions_batch3/tests/setup.ts
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

(globalThis as Record<string, unknown>).IS_REACT_ACT_ENVIRONMENT = true;

afterEach(() => {
  cleanup();
});
