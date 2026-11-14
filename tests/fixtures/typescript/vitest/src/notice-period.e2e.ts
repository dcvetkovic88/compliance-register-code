import { expect, test } from "vitest";

test("a browser spec never runs under Vitest", () => {
  expect(true).toBe(false);
});
